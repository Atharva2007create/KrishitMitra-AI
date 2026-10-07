"""Start the API with an RDS credential obtained from Secrets Manager."""

import argparse
import json
import os
from urllib.parse import quote_plus

import boto3  # type: ignore[import-untyped]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-arn", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--database", default="krishimitra")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--port", default="8000")
    args = parser.parse_args()

    response = boto3.client("secretsmanager", region_name=args.region).get_secret_value(
        SecretId=args.secret_arn
    )
    secret = json.loads(response["SecretString"])
    username = quote_plus(secret["username"])
    password = quote_plus(secret["password"])
    database_port = int(secret.get("port", 5432))
    os.environ["DATABASE_URL"] = (
        f"postgresql+asyncpg://{username}:{password}@{args.host}:{database_port}/{args.database}"
    )
    os.execvp(
        "uvicorn",
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", args.port],
    )


if __name__ == "__main__":
    main()
