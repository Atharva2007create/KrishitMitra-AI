import base64
import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAGIC_PREFIXES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}
MAX_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
MODEL_NAME = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL_NAME = os.environ.get("GEMINI_IMAGE_FALLBACK_MODEL", "gemini-3.7-flash")
MODEL_NAMES = tuple(dict.fromkeys((MODEL_NAME, FALLBACK_MODEL_NAME)))
ALLOWED_BUCKET = os.environ.get("IMAGES_BUCKET", "")
GEMINI_SECRET_ARN = os.environ.get("GEMINI_SECRET_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


class ImagePipelineError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _secret(arn: str) -> dict[str, Any]:
    if not arn:
        raise ImagePipelineError("SECRET_NOT_CONFIGURED", "Required secret is not configured")
    value = boto3.client("secretsmanager", region_name=AWS_REGION).get_secret_value(SecretId=arn)
    raw = value.get("SecretString")
    if not raw:
        raise ImagePipelineError("SECRET_INVALID", "Secret has no string value")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ImagePipelineError("SECRET_INVALID", "Secret value must be a JSON object")
    return parsed


def _event_object(event: dict[str, Any]) -> tuple[str, str]:
    records = event.get("Records")
    if not isinstance(records, list) or len(records) != 1:
        raise ImagePipelineError("INVALID_EVENT", "Exactly one S3 record is required")
    record = records[0]
    if not isinstance(record, dict) or not isinstance(record.get("s3"), dict):
        raise ImagePipelineError("INVALID_EVENT", "S3 event data is missing")
    s3 = record["s3"]
    bucket = str(s3.get("bucket", {}).get("name", ""))
    key = urllib.parse.unquote_plus(str(s3.get("object", {}).get("key", "")))
    if not bucket or not key:
        raise ImagePipelineError("INVALID_EVENT", "S3 bucket or key is missing")
    if ALLOWED_BUCKET and bucket != ALLOWED_BUCKET:
        raise ImagePipelineError("UNAPPROVED_BUCKET", "S3 bucket is not approved")
    parts = key.split("/")
    if len(parts) != 5 or parts[0] != "farmer-uploads" or ".." in parts:
        raise ImagePipelineError("INVALID_OBJECT_KEY", "S3 object key is outside the upload area")
    return bucket, key


def _result_key(key: str) -> str:
    return f"analysis-results/{key.split('/')[3]}.json"


def _hash_key(content_hash: str, model: str = MODEL_NAME) -> str:
    safe_model = model.replace("/", "_")
    return f"analysis-hashes/{safe_model}/{content_hash}.json"


def _write_result(bucket: str, key: str, value: dict[str, Any]) -> None:
    boto3.client("s3", region_name=AWS_REGION).put_object(
        Bucket=bucket,
        Key=_result_key(key),
        Body=json.dumps(value, ensure_ascii=False).encode(),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def _validate_and_load(bucket: str, key: str) -> tuple[bytes, str, dict[str, str]]:
    s3 = boto3.client("s3", region_name=AWS_REGION)
    head = s3.head_object(Bucket=bucket, Key=key)
    size = int(head.get("ContentLength", 0))
    content_type = str(head.get("ContentType", "")).lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ImagePipelineError("UNSUPPORTED_IMAGE_TYPE", "Only JPEG, PNG, and WebP are allowed")
    if size < 1 or size > MAX_BYTES:
        raise ImagePipelineError("INVALID_IMAGE_SIZE", "Image size is outside the allowed range")
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read(MAX_BYTES + 1)
    if len(body) != size or len(body) > MAX_BYTES:
        raise ImagePipelineError("INVALID_IMAGE_SIZE", "Downloaded image size is invalid")
    if not any(body.startswith(prefix) for prefix in MAGIC_PREFIXES[content_type]):
        raise ImagePipelineError("IMAGE_SIGNATURE_INVALID", "Image bytes do not match MIME type")
    if content_type == "image/webp" and body[8:12] != b"WEBP":
        raise ImagePipelineError("IMAGE_SIGNATURE_INVALID", "WebP signature is invalid")
    metadata = {str(k).lower(): str(v) for k, v in head.get("Metadata", {}).items()}
    for name in ("attachment-id", "user-id", "session-id", "source-type"):
        if not metadata.get(name):
            raise ImagePipelineError("OBJECT_METADATA_INVALID", f"Missing object metadata: {name}")
    if metadata["attachment-id"] != key.split("/")[3]:
        raise ImagePipelineError("OBJECT_METADATA_INVALID", "Attachment identity does not match key")
    return body, content_type, metadata


def _gemini_key() -> str:
    value = _secret(GEMINI_SECRET_ARN)
    key = value.get("api_key") or value.get("GEMINI_API_KEY")
    if not isinstance(key, str) or not key:
        raise ImagePipelineError("GEMINI_SECRET_INVALID", "Gemini API key is missing")
    return key


def _analyze(image: bytes, content_type: str) -> dict[str, Any]:
    prompt = """Inspect this crop image as visual triage for Tur/Pigeonpea. Return JSON only:
{"image_sufficient":boolean,"quality":{"focus":"GOOD|POOR","lighting":"GOOD|POOR","crop_visible":boolean,"notes":[string]},"observations":[{"feature":string,"location":string,"severity":"LOW|MEDIUM|HIGH|UNKNOWN"}],"candidate_issues":[{"name":string,"confidence":"LOW|MEDIUM|HIGH","reason":string}],"follow_up_questions":[string]}
Never claim a confirmed diagnosis. Do not provide pesticide, dose, treatment, or final guidance. Set image_sufficient=false for blurry, dark, unrelated, or unusable images."""
    payload = {
        "contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": content_type, "data": base64.b64encode(image).decode()}},
        ]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1600,
            "responseMimeType": "application/json",
        },
    }
    raw = b""
    model_used = ""
    last_error: Exception | None = None
    for model in MODEL_NAMES:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{urllib.parse.quote(model, safe='')}:generateContent?key="
            f"{urllib.parse.quote(_gemini_key(), safe='')}"
        )
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
        )
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    raw = response.read(1_000_001)
                model_used = model
                break
            except urllib.error.HTTPError as exc:
                last_error = exc
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt == 1:
                    break
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt == 1:
                    break
            time.sleep(2**attempt)
        if model_used:
            break
    if not model_used:
        raise ImagePipelineError("MODEL_UNAVAILABLE", "Image model is unavailable") from last_error
    if len(raw) > 1_000_000:
        raise ImagePipelineError("MODEL_RESPONSE_TOO_LARGE", "Model response is too large")
    try:
        envelope = json.loads(raw)
        text = envelope["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ImagePipelineError("MODEL_SCHEMA_INVALID", "Model response schema is invalid") from exc
    if not isinstance(result, dict):
        raise ImagePipelineError("MODEL_SCHEMA_INVALID", "Model result must be an object")
    if not isinstance(result.get("observations"), list):
        raise ImagePipelineError("MODEL_SCHEMA_INVALID", "Observations must be a list")
    if not isinstance(result.get("candidate_issues"), list):
        raise ImagePipelineError("MODEL_SCHEMA_INVALID", "Candidate issues must be a list")
    if not isinstance(result.get("quality"), dict):
        raise ImagePipelineError("MODEL_SCHEMA_INVALID", "Quality must be an object")
    serialized = json.dumps(result, ensure_ascii=False).casefold()
    if any(term in serialized for term in ("dose", "dosage", "spray", "apply", "treatment")):
        raise ImagePipelineError("MODEL_SAFETY_REJECTED", "Model returned treatment content")
    result["_model_used"] = model_used
    return result


def _reuse(bucket: str, content_hash: str) -> dict[str, Any] | None:
    s3 = boto3.client("s3", region_name=AWS_REGION)
    for model in MODEL_NAMES:
        try:
            body = s3.get_object(Bucket=bucket, Key=_hash_key(content_hash, model))["Body"].read(
                1_000_001
            )
            value = json.loads(body)
            if isinstance(value, dict) and value.get("status") in {
                "COMPLETED",
                "IMAGE_INSUFFICIENT",
            }:
                return value
        except Exception:
            continue
    return None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bucket = ""
    key = ""
    try:
        bucket, key = _event_object(event)
        _write_result(bucket, key, {"status": "PROCESSING", "model": MODEL_NAME})
        image, content_type, metadata = _validate_and_load(bucket, key)
        content_hash = hashlib.sha256(image).hexdigest()
        result = _reuse(bucket, content_hash)
        reused = result is not None
        if result is None:
            visual = _analyze(image, content_type)
            model_used = str(visual.pop("_model_used", MODEL_NAME))
            final_status = "COMPLETED" if bool(visual.get("image_sufficient")) else "IMAGE_INSUFFICIENT"
            result = {
                "status": final_status,
                "content_hash": content_hash,
                "model": model_used,
                "quality_assessment": visual["quality"],
                "observed_symptoms": {"observations": visual["observations"]},
                "candidate_issues": visual["candidate_issues"],
                "evidence": {
                    "source": "GEMINI_VISUAL_OBSERVATION",
                    "authoritative": False,
                    "follow_up_questions": visual.get("follow_up_questions", []),
                },
                "processed_at": datetime.now(UTC).isoformat(),
            }
            boto3.client("s3", region_name=AWS_REGION).put_object(
                Bucket=bucket,
                Key=_hash_key(content_hash, model_used),
                Body=json.dumps(result, ensure_ascii=False).encode(),
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )
        result["attachment_id"] = metadata["attachment-id"]
        result["reused"] = reused
        _write_result(bucket, key, result)
        logger.info("image_analysis_completed", extra={"status": result["status"]})
        return {"statusCode": 200, "status": result["status"], "reused": reused}
    except ImagePipelineError as exc:
        if bucket and key:
            _write_result(
                bucket,
                key,
                {
                    "status": "FAILED",
                    "error_code": exc.code,
                    "model": MODEL_NAME,
                    "processed_at": datetime.now(UTC).isoformat(),
                },
            )
        logger.warning("image_analysis_rejected", extra={"code": exc.code})
        return {"statusCode": 422, "status": "FAILED", "error_code": exc.code}
