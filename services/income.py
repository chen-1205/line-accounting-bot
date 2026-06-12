# 匯入日期與時間工具
from datetime import date, datetime, time

# 匯入 SQLAlchemy 的聚合函式
from sqlalchemy import func

# 匯入 Income Model 與資料庫 Session
from models.income import Income
from models.database import Session


# 新增一筆收入資料
def add_income(category, amount, note=""):
    # 建立資料庫連線 session
    session = Session()

    try:
        # 建立 Income 物件
        income = Income(
            category=category,
            amount=amount,
            note=note
        )

        # 寫入資料庫
        session.add(income)
        session.commit()

        # 重新讀取這筆資料
        session.refresh(income)

        return income

    except Exception as e:
        # 發生錯誤時回滾交易
        session.rollback()
        print(f"新增收入失敗: {e}")
        return None

    finally:
        # 關閉資料庫連線
        session.close()


# 取得所有收入資料
def get_all_incomes():
    session = Session()

    try:
        # 依照建立時間由舊到新排序
        incomes = session.query(Income).order_by(Income.created_at.asc()).all()
        return incomes

    except Exception as e:
        print(f"查詢全部收入失敗: {e}")
        return []

    finally:
        session.close()


# 取得今天的所有收入資料
def get_today_incomes():
    session = Session()

    # 今天的開始與結束時間
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
        # 篩選今天建立的收入
        incomes = session.query(Income).filter(
            Income.created_at >= today_start,
            Income.created_at <= today_end
        ).order_by(Income.created_at.asc()).all()

        return incomes

    except Exception as e:
        print(f"查詢今日收入失敗: {e}")
        return []

    finally:
        session.close()


# 取得今天總收入
def get_today_income_total():
    session = Session()

    # 今天的開始與結束時間
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
        # 加總今天收入
        total = session.query(func.sum(Income.amount)).filter(
            Income.created_at >= today_start,
            Income.created_at <= today_end
        ).scalar()

        return total or 0

    except Exception as e:
        print(f"查詢今日總收入失敗: {e}")
        return 0

    finally:
        session.close()


# 取得所有收入的類別統計
def get_income_category_summary():
    session = Session()

    try:
        # 依類別分組並加總
        results = session.query(
            Income.category,
            func.sum(Income.amount)
        ).group_by(Income.category).all()

        # 轉成字典
        summary = {}
        for category, total in results:
            summary[category] = total

        return summary

    except Exception as e:
        print(f"查詢收入類別統計失敗: {e}")
        return {}

    finally:
        session.close()


# 取得本月所有收入資料
def get_month_incomes(year=None, month=None):
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
        # 篩選本月收入
        incomes = session.query(Income).filter(
            Income.created_at >= month_start,
            Income.created_at < next_month_start
        ).order_by(Income.created_at.asc()).all()

        return incomes

    except Exception as e:
        print(f"查詢本月收入失敗: {e}")
        return []

    finally:
        session.close()


# 取得本月總收入
def get_month_income_total(year=None, month=None):
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
        # 加總本月收入
        total = session.query(func.sum(Income.amount)).filter(
            Income.created_at >= month_start,
            Income.created_at < next_month_start
        ).scalar()

        return total or 0

    except Exception as e:
        print(f"查詢本月總收入失敗: {e}")
        return 0

    finally:
        session.close()


# 取得本月收入的類別統計
def get_month_income_category_summary(year=None, month=None):
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
        # 依類別分組並加總本月收入
        results = session.query(
            Income.category,
            func.sum(Income.amount)
        ).filter(
            Income.created_at >= month_start,
            Income.created_at < next_month_start
        ).group_by(Income.category).all()

        # 轉成字典
        summary = {}
        for category, total in results:
            summary[category] = total

        return summary

    except Exception as e:
        print(f"查詢本月收入類別統計失敗: {e}")
        return {}

    finally:
        session.close()