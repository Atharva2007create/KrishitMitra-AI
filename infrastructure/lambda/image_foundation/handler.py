import json
from typing import Any


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Phase 1 connectivity handler; image analysis is intentionally not implemented."""
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "status": "ok",
                "service": "krishimitra-image-foundation",
                "request_id": getattr(context, "aws_request_id", None),
            }
        ),
    }
