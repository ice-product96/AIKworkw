"""Create admin user: py -m scripts.create_admin admin@example.com password"""

import asyncio
import sys

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models import User, UserRole


async def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: py -m scripts.create_admin <email> <password>")
        sys.exit(1)
    email, password = sys.argv[1], sys.argv[2]
    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print("User already exists")
            return
        user = User(email=email, password_hash=hash_password(password), role=UserRole.admin)
        session.add(user)
        await session.commit()
        print(f"Admin created: {email}")


if __name__ == "__main__":
    asyncio.run(main())
