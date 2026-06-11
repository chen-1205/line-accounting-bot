from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

from sqlalchemy.orm import declarative_base

from datetime import datetime

Base = declarative_base()

class Expense(Base):

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    category = Column(String)

    amount = Column(Integer)

    note = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.now
    )