from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Budget(Base):

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)

    category = Column(String)

    budget = Column(Integer)