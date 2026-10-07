import argparse
import asyncio

import boto3  # type: ignore[import-untyped]
from sqlalchemy import select

from app.core.settings import get_settings
from app.db.connection import SessionFactory
from app.models.entities import User
from app.models.enums import UserRole


async def set_application_role(cognito_sub: str) -> None:
    async with SessionFactory() as session:
        user = await session.scalar(select(User).where(User.cognito_sub == cognito_sub))
        if user is not None:
            user.role = UserRole.ADMIN
            await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a trusted Cognito user to the admin group")
    parser.add_argument("--username", required=True, help="Existing Cognito username")
    parser.add_argument(
        "--cognito-sub",
        help="Existing application user's Cognito sub; updates its stored role when supplied",
    )
    args = parser.parse_args()
    settings = get_settings()
    if not settings.aws_cognito_user_pool_id:
        raise SystemExit("AWS_COGNITO_USER_POOL_ID is required")
    client = boto3.client("cognito-idp", region_name=settings.aws_region)
    client.admin_add_user_to_group(
        UserPoolId=settings.aws_cognito_user_pool_id,
        Username=args.username,
        GroupName=settings.aws_cognito_admin_group,
    )
    if args.cognito_sub:
        asyncio.run(set_application_role(args.cognito_sub))
    print("Admin group membership established; no password was handled or stored.")


if __name__ == "__main__":
    main()
