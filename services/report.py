# 匯入目前時間工具
from datetime import datetime, timedelta

# 匯入支出相關函式
from services.accounting import (
    get_today_total,
    get_month_total,
    get_month_category_summary,
    get_all_expenses,
)

# 匯入收入相關函式
from services.income import (
    get_today_income_total,
    get_month_income_total,
    get_month_income_category_summary,
    get_all_incomes,
)

# 這個函式用來把資料建立時間格式化成易讀文字
# 如果有時間就轉成 年-月-日 時:分
# 如果沒有時間就回傳「無」
def format_datetime_text(dt):
    if dt is None:
        return "無"

    return dt.strftime("%Y-%m-%d %H:%M")


# 建立今日收支報表文字
def build_today_report():
    # 取得今天的收入與支出總額
    total_income = get_today_income_total()
    total_expense = get_today_total()

    # 計算今日結餘
    balance = total_income - total_expense

    # 組合成回覆文字
    report_text = (
        "☁️ 大耳狗今日收支報表\n"
        f"今日收入：{total_income} 元\n"
        f"今日支出：{total_expense} 元\n"
        f"今日結餘：{balance} 元"
    )

    return report_text


# 建立本月完整收支報表
def build_month_report():
    # 取得目前年月
    now = datetime.now()
    year = now.year
    month = now.month

    # 取得本月總收入與總支出
    month_income = get_month_income_total(year, month)
    month_expense = get_month_total(year, month)

    # 計算本月結餘
    balance = month_income - month_expense

    # 取得本月收入與支出的分類統計
    income_summary = get_month_income_category_summary(year, month)
    expense_summary = get_month_category_summary(year, month)

    # 建立報表開頭
    lines = [
        f"☁️ 大耳狗 {year}/{month} 本月報表",
        f"總收入：{month_income} 元",
        f"總支出：{month_expense} 元",
        f"本月結餘：{balance} 元",
        "",
        "【支出排行】"
    ]

    # 如果有支出資料，依金額由大到小顯示
    if expense_summary:
        sorted_expenses = sorted(expense_summary.items(), key=lambda item: item[1], reverse=True)

        for index, (category, total) in enumerate(sorted_expenses, start=1):
            lines.append(f"{index}. {category}：{total} 元")
    else:
        lines.append("目前沒有本月支出資料")

    # 加入收入排行標題
    lines.append("")
    lines.append("【收入排行】")

    # 如果有收入資料，依金額由大到小顯示
    if income_summary:
        sorted_incomes = sorted(income_summary.items(), key=lambda item: item[1], reverse=True)

        for index, (category, total) in enumerate(sorted_incomes, start=1):
            lines.append(f"{index}. {category}：{total} 元")
    else:
        lines.append("目前沒有本月收入資料")

    return "\n".join(lines)


# 建立本月支出報表
def build_month_expense_report():
    # 取得目前年月
    now = datetime.now()
    year = now.year
    month = now.month

    # 取得本月總支出
    month_expense = get_month_total(year, month)

    # 取得本月支出分類統計
    expense_summary = get_month_category_summary(year, month)

    # 建立報表開頭
    lines = [
        f"☁️ 大耳狗 {year}/{month} 本月支出報表",
        f"總支出：{month_expense} 元",
        "",
        "【支出排行】"
    ]

    # 如果有資料就排序顯示
    if expense_summary:
        sorted_expenses = sorted(expense_summary.items(), key=lambda item: item[1], reverse=True)

        for index, (category, total) in enumerate(sorted_expenses, start=1):
            lines.append(f"{index}. {category}：{total} 元")
    else:
        lines.append("目前沒有本月支出資料")

    return "\n".join(lines)


# 建立本月收入報表
def build_month_income_report():
    # 取得目前年月
    now = datetime.now()
    year = now.year
    month = now.month

    # 取得本月總收入
    month_income = get_month_income_total(year, month)

    # 取得本月收入分類統計
    income_summary = get_month_income_category_summary(year, month)

    # 建立報表開頭
    lines = [
        f"☁️ 大耳狗 {year}/{month} 本月收入報表",
        f"總收入：{month_income} 元",
        "",
        "【收入排行】"
    ]

    # 如果有資料就排序顯示
    if income_summary:
        sorted_incomes = sorted(income_summary.items(), key=lambda item: item[1], reverse=True)

        for index, (category, total) in enumerate(sorted_incomes, start=1):
            lines.append(f"{index}. {category}：{total} 元")
    else:
        lines.append("目前沒有本月收入資料")

    return "\n".join(lines)


# 建立近三天支出清單
# 只顯示建立時間在近三天內的資料，並附上 ID 方便修改或刪除
def build_recent_expense_list(days=3):
    # 取得全部支出資料
    expenses = get_all_expenses()

    # 如果沒有支出資料，回傳提示
    if not expenses:
        return "☁️ 目前還沒有任何支出資料"

    # 計算近三天的時間門檻
    cutoff_time = datetime.now() - timedelta(days=days)

    # 只保留近三天內的支出資料
    recent_expenses = [
        expense for expense in expenses
        if expense.created_at is not None and expense.created_at >= cutoff_time
    ]

    # 讓最新資料排前面
    recent_expenses.sort(key=lambda expense: expense.created_at, reverse=True)

    # 如果近三天沒有資料，回傳提示
    if not recent_expenses:
        return f"☁️ 近 {days} 天內沒有任何支出資料"

    # 建立回覆開頭
    lines = [
        f"☁️ 近 {days} 天支出明細",
        "以下都有附上 ID，之後修改或刪除時比較不用猜。"
    ]

    # 逐筆加入明細內容
    for expense in recent_expenses:
        lines.append("--------------------")
        lines.append(f"ID：{expense.id}")
        lines.append(f"類別：{expense.category}")
        lines.append(f"金額：{expense.amount} 元")
        lines.append(f"備註：{expense.note or '無'}")
        lines.append(f"時間：{format_datetime_text(expense.created_at)}")

    # 補上提示訊息
    lines.append("--------------------")
    lines.append("之後可用這些 ID 來做查看、修改或刪除。")

    return "\n".join(lines)


# 建立近三天收入清單
# 只顯示建立時間在近三天內的資料，並附上 ID 方便修改或刪除
def build_recent_income_list(days=3):
    # 取得全部收入資料
    incomes = get_all_incomes()

    # 如果沒有收入資料，回傳提示
    if not incomes:
        return "☁️ 目前還沒有任何收入資料"

    # 計算近三天的時間門檻
    cutoff_time = datetime.now() - timedelta(days=days)

    # 只保留近三天內的收入資料
    recent_incomes = [
        income for income in incomes
        if income.created_at is not None and income.created_at >= cutoff_time
    ]

    # 讓最新資料排前面
    recent_incomes.sort(key=lambda income: income.created_at, reverse=True)

    # 如果近三天沒有資料，回傳提示
    if not recent_incomes:
        return f"☁️ 近 {days} 天內沒有任何收入資料"

    # 建立回覆開頭
    lines = [
        f"☁️ 近 {days} 天收入明細",
        "以下都有附上 ID，之後修改或刪除時比較不用猜。"
    ]

    # 逐筆加入明細內容
    for income in recent_incomes:
        lines.append("--------------------")
        lines.append(f"ID：{income.id}")
        lines.append(f"類別：{income.category}")
        lines.append(f"金額：{income.amount} 元")
        lines.append(f"備註：{income.note or '無'}")
        lines.append(f"時間：{format_datetime_text(income.created_at)}")

    # 補上提示訊息
    lines.append("--------------------")
    lines.append("之後可用這些 ID 來做查看、修改或刪除。")

    return "\n".join(lines)