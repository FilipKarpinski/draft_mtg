import logging
import os

from sqlalchemy import select

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.db.database import db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_EMAIL = "admin@example"


def setup_admin_user() -> None:
    """Create admin user if it doesn't exist."""
    if not ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD not set in environment variables. Skipping admin user creation.")
        return

    try:
        with db_session() as db:
            # Check if admin user already exists
            admin_user = db.execute(select(User).where(User.username == ADMIN_USERNAME)).scalar_one_or_none()

            if admin_user:
                logger.info(f"Admin user '{ADMIN_USERNAME}' already exists.")
                return

            # Create new admin user
            new_admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_active=True,
                is_admin=True,
            )

            db.add(new_admin)
            db.commit()
            logger.info(f"Admin user '{ADMIN_USERNAME}' created successfully.")

    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise


if __name__ == "__main__":
    setup_admin_user()
