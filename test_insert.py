from expense import Expense
from database import Session

session = Session()

expense = Expense(
    category="餐飲",
    amount=150,
    note="午餐"
)

session.add(expense)
session.commit()

print("新增成功")