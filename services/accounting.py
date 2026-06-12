# 匯入日期與時間工具
from datetime import date, datetime, time

# 匯入 SQLAlchemy 的聚合函式
from sqlalchemy import func

# 匯入 Expense Model 與資料庫 Session
from models.expense import Expense
from models.database import Session


# 新增一筆支出資料
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
def get_all_expenses():
    session = Session()

    try:
        # 依照建立時間由舊到新排序
        expenses = session.query(Expense).order_by(Expense.created_at.asc()).all()
        return expenses

    except Exception as e:
        print(f"查詢全部支出失敗: {e}")
        return []

    finally:
        session.close()


# 取得今天的所有支出資料
def get_today_expenses():
    session = Session()

    # 今天的開始時間與結束時間
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
        # 篩選今天建立的資料
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
        # 加總今天的 amount
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
        # 依照 category 分組並加總
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

    # 下個月第一天，用來當作查詢上界
    if month == 12:
        next_month_start = datetime(year + 1, 1, 1)
    else:
        next_month_start = datetime(year, month + 1, 1)

    try:
        # 篩選本月建立的支出資料
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
        # 加總本月支出
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
        # 依類別分組並加總本月支出
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