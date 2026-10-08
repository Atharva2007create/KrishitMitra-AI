"""Run Alembic against an RDS database whose credentials live in Secrets Manager."""

import argparse
import asyncio
import json
import os
from urllib.parse import quote_plus

import boto3  # type: ignore[import-untyped]
from alembic.config import Config

from alembic import command


async def post_migration_tasks(seed: bool, verify: bool) -> None:
    from sqlalchemy import text

    from app.db.connection import engine
    from scripts.seed_government_sources import main as seed_sources

    if seed:
        await seed_sources()
    if verify:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            tables = await connection.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN "
                    "('users','farmer_profiles','farms','crop_cycles','chat_sessions',"
                    "'messages','government_sources','source_documents','image_analyses',"
                    "'feedback','audit_logs','ingestion_jobs','knowledge_chunks')"
                )
            )
            sources = await connection.scalar(text("SELECT count(*) FROM government_sources"))
            vector_dimension = await connection.scalar(
                text(
                    "SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a "
                    "JOIN pg_class c ON c.oid=a.attrelid "
                    "WHERE c.relname='knowledge_chunks' AND a.attname='embedding'"
                )
            )
            indexes = await connection.scalar(
                text(
                    "SELECT count(*) FROM pg_indexes WHERE tablename='knowledge_chunks' "
                    "AND indexname IN ('ix_knowledge_chunks_embedding_hnsw',"
                    "'ix_knowledge_chunks_search_vector')"
                )
            )
        print(
            f"Verified revision={revision}, core_tables={int(tables or 0)}, "
            f"government_sources={int(sources or 0)}, vector={vector_dimension}, "
            f"rag_indexes={int(indexes or 0)}."
        )
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-arn", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--database", default="krishimitra")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--seed-sources", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    response = boto3.client("secretsmanager", region_name=args.region).get_secret_value(
        SecretId=args.secret_arn
    )
    secret = json.loads(response["SecretString"])
    username = quote_plus(secret["username"])
    password = quote_plus(secret["password"])
    port = int(secret.get("port", 5432))
    os.environ["DATABASE_URL"] = (
        f"postgresql+asyncpg://{username}:{password}@{args.host}:{port}/{args.database}"
    )
    try:
        command.upgrade(Config("alembic.ini"), "head")
        asyncio.run(post_migration_tasks(args.seed_sources, args.verify))
    finally:
        os.environ.pop("DATABASE_URL", None)
    print("RDS migration completed successfully; credentials were not displayed.")


if __name__ == "__main__":
    main()
