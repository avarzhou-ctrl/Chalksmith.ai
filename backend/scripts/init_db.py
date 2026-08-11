"""Create the v2 schema using the configured database connection."""

from backend.app.db.session import create_db_and_tables


if __name__ == "__main__":
    create_db_and_tables()
    print("Chalksmith v2 database schema is ready.")
