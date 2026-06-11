from expense import Base as ExpenseBase
from income import Base as IncomeBase
from models.budget import Base as BudgetBase
from database import engine

ExpenseBase.metadata.create_all(engine)
IncomeBase.metadata.create_all(engine)
BudgetBase.metadata.create_all(engine)

print("Database Created")