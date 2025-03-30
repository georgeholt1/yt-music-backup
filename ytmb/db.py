from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import DB_URI

engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)


def initialize_database():
    Base.metadata.create_all(engine)
