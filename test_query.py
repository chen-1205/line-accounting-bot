from expense import Expense
from database import Session

session = Session()

expenses = session.query(Expense).all()

for expense in expenses:
    print(
        expense.id,
        expense.category,
        expense.amount,
        expense.note,
        expense.created_at
    )