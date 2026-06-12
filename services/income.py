# 匯入日期與時間工具
from datetime import date, datetime, time

# 匯入 SQLAlchemy 的聚合函式
from sqlalchemy import func

# 匯入 Income Model 與資料庫 Session
from models.income import Income
from models.database import Session


# 新增一筆收入資料
# category：收入類別，例如薪水、獎金、退款
# amount：收入金額
# note：備註，可不填
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

        # 重新讀取這筆資料，確保 id 等欄位完整
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
# 會依照建立時間由舊到新排序
def get_all_incomes():
    session = Session()

    try:
        incomes = session.query(Income).order_by(Income.created_at.asc()).all()
        return incomes

    except Exception as e:
        print(f"查詢全部收入失敗: {e}")
        return []

    finally:
        session.close()


# 根據 id 取得單筆收入資料
# 之後做查看、修改、刪除時會很好用
def get_income_by_id(income_id):
    session = Session()

    try:
        income = session.query(Income).filter(Income.id == income_id).first()
        return income

    except Exception as e:
        print(f"查詢單筆收入失敗: {e}")
        return None

    finally:
        session.close()


# 修改一筆收入資料
# 會依照 id 找到資料後更新內容
# 找不到資料時回傳 None
def update_income(income_id, category, amount, note=""):
    session = Session()

    try:
        income = session.query(Income).filter(Income.id == income_id).first()

        # 如果找不到這筆資料，直接回傳 None
        if income is None:
            return None

        # 更新欄位內容
        income.category = category
        income.amount = amount
        income.note = note

        # 寫回資料庫
        session.commit()
        session.refresh(income)

        return income

    except Exception as e:
        session.rollback()
        print(f"修改收入失敗: {e}")
        return None

    finally:
        session.close()


# 刪除一筆收入資料
# 成功刪除回傳 True，找不到資料或失敗回傳 False
def delete_income(income_id):
    session = Session()

    try:
        income = session.query(Income).filter(Income.id == income_id).first()

        # 如果找不到資料，回傳 False
        if income is None:
            return False

        # 刪除資料
        session.delete(income)
        session.commit()

        return True

    except Exception as e:
        session.rollback()
        print(f"刪除收入失敗: {e}")
        return False

    finally:
        session.close()


# 取得今天的所有收入資料
# 會篩選今天建立的資料
def get_today_incomes():
    session = Session()

    # 今天的開始時間與結束時間
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
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
# 會把今天所有收入的 amount 加總起來
def get_today_income_total():
    session = Session()

    # 今天的開始時間與結束時間
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    try:
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
# 例如：薪水 45000、獎金 3000
def get_income_category_summary():
    session = Session()

    try:
        results = session.query(
            Income.category,
            func.sum(Income.amount)
        ).group_by(Income.category).all()

        # 轉成字典格式回傳
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
# 可指定 year、month；若不指定就使用現在的年月
def get_month_incomes(year=None, month=None):
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
# 用來做本月報表或本月收入查詢
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
# 例如本月薪水、獎金、退款各是多少
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


# 列印全部收入資料
# 這個函式主要是本機開發時方便除錯
def print_all_incomes():
    incomes = get_all_incomes()

    if not incomes:
        print("目前沒有任何收入資料")
        return

    for income in incomes:
        print(
            income.id,
            income.category,
            income.amount,
            income.note,
            income.created_at
        )