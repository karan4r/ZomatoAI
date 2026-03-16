from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_database_url

Base = declarative_base()


def get_engine(echo: bool = False):
    """
    Create a SQLAlchemy engine using the current DATABASE_URL.
    """
    return create_engine(get_database_url(), echo=echo, future=True)


def get_session_factory(echo: bool = False):
    """
    Return a configured sessionmaker bound to the engine.
    """
    engine = get_engine(echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


