# 匯入日期與時間工具
from datetime import date, datetime, time

# 匯入 SQLAlchemy 的聚合函式
from sqlalchemy import func

# 匯入 Expense Model 與資料庫 Session
from models.expense import Expense
from models.database import Session


# 新增一筆支出資料
# category：支出類別，例如餐飲、交通
# amount：支出金額
# note：備註，可不填
def add_expense(category, amount, note=""):
    # 建立資料庫連線 session
    session = Session()

    try:
        # 建立 Expense 物件
        expense = Expense(
            category=category,
            amount=amount,
            note=note
        )

        # 寫入資料庫
        session.add(expense)
        session.commit()

        # 重新讀取這筆資料，確保 id 等欄位完整
        session.refresh(expense)

        return expense

    except Exception as e:
        # 發生錯誤時回滾交易
        session.rollback()
        print(f"新增支出失敗: {e}")
        return None

    finally:
        # 關閉資料庫連線
        session.close()


# 取得所有支出資料
# 會依照建立時間由舊到新排序
def get_all_expenses():
    session = Session()

    try:
        expenses = session.query(Expense).order_by(Expense.created_at.asc()).all()
        return expenses

    except Exception as e:
        print(f"查詢全部支出失敗: {e}")
        return []

    finally:
        session.close()


# 根據 id 取得單筆支出資料
def get_expense_by_id(expense_id):
    session = Session()

    try:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        return expense

    except Exception as e:
        print(f"查詢單筆支出失敗: {e}")
        return None

    finally:
        session.close()


# 修改一筆支出資料
def update_expense(expense_id, category, amount, note=""):
    session = Session()

    try:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()

        # 如果找不到這筆資料，直接回傳 None
        if expense is None:
            return None

        # 更新欄位內容
        expense.category = category
        expense.amount = amount
        expense.note = note

        # 寫回資料庫
        session.commit()
        session.refresh(expense)

        return expense

    except Exception as e:
        session.rollback()
        print(f"修改支出失敗: {e}")
        return None

    finally:
        session.close()


# 刪除一筆支出資料
# 成功刪除回傳 True，找不到資料或失敗回傳 False
def delete_expense(expense_id):
    session = Session()

    try:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()

        # 如果找不到資料，回傳 False
        if expense is None:
            return False

        # 刪除資料
        session.delete(expense)
        session.commit()

        return True

    except Exception as e:
        session.rollback()
        print(f"刪除支出失敗: {e}")
        return False

    finally:
        session.close()


# 取得今天的所有支出資料
def get_today_expenses():
    session = Session()

    # 今天的開始時間與結束時間
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


# 取得今天總支出
def get_today_total():
    session = Session()

    # 今天的開始時間與結束時間
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


# 取得所有支出的類別統計
def get_category_summary():
    session = Session()

    try:
        results = session.query(
            Expense.category,
            func.sum(Expense.amount)
        ).group_by(Expense.category).all()

        # 轉成字典格式回傳
        summary = {}
        for category, total in results:
            summary[category] = total

        return summary

    except Exception as e:
        print(f"查詢支出類別統計失敗: {e}")
        return {}

    finally:
        session.close()


# 取得本月所有支出資料
def get_month_expenses(year=None, month=None):
    session = Session()

    # 如果沒有指定年月，就使用現在的年月
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 本月第一天
    month_start = datetime(year, month, 1)

    # 下個月第一天，用來當查詢上界
    if month == 12:
        next_month_start = datetime(year + 1, 1, 1)
    else:
        next_month_start = datetime(year, month + 1, 1)

    try:
        expenses = session.query(Expense).filter(
            Expense.created_at >= month_start,
            Expense.created_at < next_month_start
        ).order_by(Expense.created_at.asc()).all()

        return expenses

    except Exception as e:
        print(f"查詢本月支出失敗: {e}")
        return []

    finally:
        session.close()


# 取得本月總支出
def get_month_total(year=None, month=None):
    session = Session()

    # 如果沒有指定年月，就使用現在的年月
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 本月第一天
    month_start = datetime(year, month, 1)

    # 下個月第一天
    if month == 12:
        next_month_start = datetime(year + 1, 1, 1)
    else:
        next_month_start = datetime(year, month + 1, 1)

    try:
        total = session.query(func.sum(Expense.amount)).filter(
            Expense.created_at >= month_start,
            Expense.created_at < next_month_start
        ).scalar()

        return total or 0

    except Exception as e:
        print(f"查詢本月總支出失敗: {e}")
        return 0

    finally:
        session.close()


# 取得本月支出的類別統計
def get_month_category_summary(year=None, month=None):
    session = Session()

    # 如果沒有指定年月，就使用現在的年月
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 本月第一天
    month_start = datetime(year, month, 1)

    # 下個月第一天
    if month == 12:
        next_month_start = datetime(year + 1, 1, 1)
    else:
        next_month_start = datetime(year, month + 1, 1)

    try:
        results = session.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.created_at >= month_start,
            Expense.created_at < next_month_start
        ).group_by(Expense.category).all()

        # 轉成字典
        summary = {}
        for category, total in results:
            summary[category] = total

        return summary

    except Exception as e:
        print(f"查詢本月支出類別統計失敗: {e}")
        return {}

    finally:
        session.close()


# 列印全部支出資料
# 這個函式主要是本機開發時方便除錯
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