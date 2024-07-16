import loguru
from sqlalchemy import select

from services.database.db_connect import session_factory
from services.database.models import User


async def check_users():
    async with session_factory() as session:
        data = await session.execute(
            select(User).where(User.api_key == "test")
        )
        users_data = data.scalar()
        if users_data:
            loguru.logger.info("Users have already been created")
        else:
            first_user = User(api_key="test", name="Иван")
            second_user = User(api_key="test1", name="Катя")
            session.add_all([first_user, second_user])
            await session.commit()
            loguru.logger.info("Users have been added")
