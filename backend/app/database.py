import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# 鍐欐杩炴帴涓?# SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:xiaoyuhan789290@localhost:5432/forjob_new"
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:xiaoyuhan789290@localhost:5432/forjob_new"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=True 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


