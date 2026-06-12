# 匯入目前時間工具
from datetime import datetime

# 匯入支出相關函式
from services.accounting import (
    get_today_total,
    get_category_summary,
    get_month_total,
    get_month_category_summary,
)

# 匯入收入相關函式
from services.income import (
    get_today_income_total,
    get_income_category_summary,
    get_month_income_total,
    get_month_income_category_summary,
)


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


# 建立全部支出統計報表文字
def build_expense_summary_report():
    # 取得所有支出類別統計
    summary = get_category_summary()

    # 如果沒有資料，直接回傳提示
    if not summary:
        return "☁️ 目前還沒有任何支出統計資料"

    # 建立標題
    lines = ["☁️ 大耳狗支出分類統計"]

    # 依照金額由大到小排序
    sorted_items = sorted(summary.items(), key=lambda item: item[1], reverse=True)

    # 逐行加入統計內容
    for category, total in sorted_items:
        lines.append(f"{category}：{total} 元")

    return "\n".join(lines)


# 建立全部收入統計報表文字
def build_income_summary_report():
    # 取得所有收入類別統計
    summary = get_income_category_summary()

    # 如果沒有資料，直接回傳提示
    if not summary:
        return "☁️ 目前還沒有任何收入統計資料"

    # 建立標題
    lines = ["☁️ 大耳狗收入分類統計"]

    # 依照金額由大到小排序
    sorted_items = sorted(summary.items(), key=lambda item: item[1], reverse=True)

    # 逐行加入統計內容
    for category, total in sorted_items:
        lines.append(f"{category}：{total} 元")

    return "\n".join(lines)


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