#a helper file so every test gets a fresh database 
#instead of touching our real payout_system.db

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models 

@pytest.fixture()
def db_session():
    engine=create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    session=Session()
    yield session
    session.close()