from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from sqlalchemy.orm import declarative_base
from config import DATABASE_URL
db_url= DATABASE_URL

Base = declarative_base()

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind= engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()