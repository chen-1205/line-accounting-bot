from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

from sqlalchemy.orm import declarative_base

from datetime import datetime

Base = declarative_base()

class Income(Base):

    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True)

    category = Column(String)

    amount = Column(Integer)

    created_at = Column(
        DateTime,
        default=datetime.now
    )