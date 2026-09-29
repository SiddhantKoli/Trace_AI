from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    """Create tables and apply the additive mode migration for SQLite."""
    Base.metadata.create_all(bind=engine)

    if engine.dialect.name != "sqlite":
        return

    columns = {column["name"] for column in inspect(engine).get_columns("analysis_runs")}
    if "data_mode" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE analysis_runs "
                    "ADD COLUMN data_mode VARCHAR(10) NOT NULL DEFAULT 'demo'"
                )
            )
