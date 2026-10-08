import asyncio
import json
from typing import Any

import boto3  # type: ignore[import-untyped]


class StorageError(RuntimeError):
    pass


class GovernmentDocumentStore:
    def __init__(self, bucket: str, region: str) -> None:
        if not bucket:
            raise StorageError("AWS_S3_BUCKET_DOCUMENTS is required")
        self.bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    async def put_original(self, key: str, content: bytes, mime_type: str, checksum: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=mime_type,
                Metadata={"sha256": checksum, "evidence": "official-original"},
                ServerSideEncryption="AES256",
            )
        except Exception as exc:
            raise StorageError("Failed to store original government evidence") from exc

    async def put_processed(self, key: str, payload: dict[str, Any]) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )
        except Exception as exc:
            raise StorageError("Failed to store processed government evidence") from exc
