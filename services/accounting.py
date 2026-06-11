from datetime import date, datetime, time
from sqlalchemy import func

from models.expense import Expense
from models.database import Session


def add_expense(category, amount, note=""):
    session = Session()

    try:
        expense = Expense(
            category=category,
            amount=amount,
            note=note
        )

        session.add(expense)
        session.commit()
        session.refresh(expense)

        return expense

    except Exception as e:
        session.rollback()
        print(f"新增支出失敗: {e}")
        return None

    finally:
        session.close()



def get_all_expenses():
    session = Session()

    try:
        expenses = session.query(Expense).order_by(Expense.created_at.asc()).all()
        return expenses

    except Exception as e:
        print(f"查詢支出失敗: {e}")
        return []

    finally:
        session.close()



def get_today_expenses():
    session = Session()

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
        expenses = session.query(Expense).filter(
            Expense.created_at >= today_start,
            Expense.created_at <= today_end
        ).order_by(Expense.created_at.asc()).all()
        return expenses

    except Exception as e:
        print(f"查詢今日支出失敗: {e}")
        return []

    finally:
        session.close()



def get_today_total():
    session = Session()

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
        total = session.query(func.sum(Expense.amount)).filter(
            Expense.created_at >= today_start,
            Expense.created_at <= today_end
        ).scalar()

        return total or 0

    except Exception as e:
        print(f"查詢今日總支出失敗: {e}")
        return 0

    finally:
        session.close()



def get_category_summary():
    session = Session()

    try:
        results = session.query(
            Expense.category,
            func.sum(Expense.amount)
        ).group_by(Expense.category).all()

        summary = {}
        for category, total in results:
            summary[category] = total

        return summary

    except Exception as e:
        print(f"查詢類別統計失敗: {e}")
        return {}

    finally:
        session.close()



def print_all_expenses():
    expenses = get_all_expenses()

    if not expenses:
        print("目前沒有任何支出資料")
        return

    for expense in expenses:
        print(
            expense.id,
            expense.category,
            expense.amount,
            expense.note,
            expense.created_at
        )



def print_today_expenses():
    expenses = get_today_expenses()

    if not expenses:
        print("今天沒有任何支出資料")
        return

    for expense in expenses:
        print(
            expense.id,
            expense.category,
            expense.amount,
            expense.note,
            expense.created_at
        )

    print(f"今日總支出：{get_today_total()}")



def print_category_summary():
    summary = get_category_summary()

    if not summary:
        print("目前沒有任何類別統計資料")
        return

    for category, total in summary.items():
        print(f"{category}：{total}")