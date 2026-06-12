# 匯入 os，用來讀取 .env 裡的環境變數
import os

# 匯入 Flask 相關功能
from flask import Flask, request, abort

# 匯入 dotenv，用來載入 .env 設定檔
from dotenv import load_dotenv

# 匯入 LINE Bot SDK v3 的 WebhookHandler
from linebot.v3 import WebhookHandler

# 匯入 Messaging API 需要的類別
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

# 匯入 LINE webhook 事件與文字訊息型別
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 匯入支出服務
from services.accounting import (
    add_expense,
    get_all_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense,
)

# 匯入收入服務
from services.income import (
    add_income,
    get_all_incomes,
    get_income_by_id,
    update_income,
    delete_income,
)

# 匯入報表服務
from services.report import (
    build_today_report,
    build_month_report,
    build_month_expense_report,
    build_month_income_report,
)

# 匯入文字解析器
from services.parser import parse_expense_text

# 匯入 Expense 的 Base 與資料庫 engine
from models.expense import Base as ExpenseBase

# 匯入 Income 的 Base
from models.income import Base as IncomeBase

# 匯入資料庫 engine
from models.database import engine

# 載入專案根目錄中的 .env 檔案
load_dotenv()

# 從 .env 讀取 LINE Bot 的 Channel Secret
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# 從 .env 讀取 LINE Bot 的 Channel Access Token
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

# 印出是否有成功讀到環境變數
print("CHANNEL_SECRET 已讀取：", bool(CHANNEL_SECRET))
print("CHANNEL_ACCESS_TOKEN 已讀取：", bool(CHANNEL_ACCESS_TOKEN))

# 建立 LINE Messaging API 的設定物件
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 建立 WebhookHandler，用來驗證 LINE 傳來的 webhook 簽章
handler = WebhookHandler(CHANNEL_SECRET)

# 建立資料表
ExpenseBase.metadata.create_all(engine)
IncomeBase.metadata.create_all(engine)

# 建立 Flask 應用程式
app = Flask(__name__)


# 收入類別關鍵字清單
# 只要第一個欄位是這些類別，就自動判斷為收入
INCOME_CATEGORIES = {
    "薪水", "薪資", "獎金", "分紅", "退款", "退費", "回饋", "利息",
    "股息", "租金", "租金收入", "收入", "營收", "兼職", "外快",
    "接案", "報酬", "津貼", "補助", "紅包", "零用錢", "賣貨",
    "出售", "轉售", "佣金", "傭金"
}


# 支出類別關鍵字清單
# 只要第一個欄位是這些類別，就自動判斷為支出
EXPENSE_CATEGORIES = {
    "餐飲", "早餐", "午餐", "晚餐", "宵夜", "飲料", "咖啡", "點心",
    "交通", "捷運", "公車", "計程車", "高鐵", "火車", "加油", "停車",
    "娛樂", "電影", "遊戲", "旅遊", "購物", "服飾", "生活", "日用品",
    "醫療", "保健", "保險", "房租", "水電", "瓦斯", "網路", "電話費",
    "學習", "書籍", "文具", "學費", "交際", "禮物", "寵物", "美容"
}


# 這個函式用來自動判斷類別屬於收入還是支出
# 有命中收入類別就回傳 income
# 有命中支出類別就回傳 expense
# 都沒命中時，預設當成支出處理
# 這樣使用者就不用再手動輸入「收入」兩個字

def detect_record_type(category):
    # 先把類別前後空白去掉
    category = category.strip()

    # 優先判斷是否為收入類別
    if category in INCOME_CATEGORIES:
        return "income"

    # 再判斷是否為支出類別
    if category in EXPENSE_CATEGORIES:
        return "expense"

    # 如果都沒有命中，先預設當成支出
    return "expense"


# 這個函式用來解析「自動判斷收入或支出」的記帳格式
# 格式範例：
# 薪水 45000 五月薪水
# 餐飲 150 午餐
# 交通 30 捷運

def parse_record_text(text):
    # 先依照空白切開文字
    parts = text.strip().split()

    # 至少要有：類別 金額
    if len(parts) < 2:
        return None

    # 第一個欄位視為類別
    category = parts[0]

    # 第二個欄位必須是金額
    try:
        amount = int(parts[1])
    except ValueError:
        return None

    # 第三個欄位之後視為備註
    note = ""
    if len(parts) > 2:
        note = " ".join(parts[2:])

    # 自動判斷這筆是收入還是支出
    record_type = detect_record_type(category)

    # 回傳解析結果
    return {
        "type": record_type,
        "category": category,
        "amount": amount,
        "note": note
    }


# 這個函式用來把資料建立時間格式化成易讀文字
def format_datetime_text(dt):
    # 如果時間不存在，回傳預設文字
    if dt is None:
        return "無"

    # 轉成 年-月-日 時:分 的格式
    return dt.strftime("%Y-%m-%d %H:%M")


# 這個函式用來建立最近支出清單
def build_recent_expense_list(limit=10):
    # 取得全部支出資料
    expenses = get_all_expenses()

    # 如果沒有支出資料，回傳提示
    if not expenses:
        return "☁️ 目前還沒有任何支出資料"

    # 只取最後幾筆，並倒序顯示，讓最新資料排前面
    recent_expenses = expenses[-limit:]
    recent_expenses.reverse()

    # 建立回覆開頭
    lines = [
        f"☁️ 最近 {len(recent_expenses)} 筆支出明細",
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


# 這個函式用來建立最近收入清單
def build_recent_income_list(limit=10):
    # 取得全部收入資料
    incomes = get_all_incomes()

    # 如果沒有收入資料，回傳提示
    if not incomes:
        return "☁️ 目前還沒有任何收入資料"

    # 只取最後幾筆，並倒序顯示，讓最新資料排前面
    recent_incomes = incomes[-limit:]
    recent_incomes.reverse()

    # 建立回覆開頭
    lines = [
        f"☁️ 最近 {len(recent_incomes)} 筆收入明細",
    ]

    # 逐筆加入明細內容
    for income in recent_incomes:
        lines.append("--------------------")
        lines.append(f"ID：{income.id}")
        lines.append(f"類別：{income.category}")
        lines.append(f"金額：{income.amount} 元")
        lines.append(f"備註：{income.note or '無'}")
        lines.append(f"時間：{format_datetime_text(income.created_at)}")


    return "\n".join(lines)


# 這個 API 用來測試 Flask 是否成功啟動
@app.route("/")
def home():
    return "☁️ 大耳狗記帳小管家啟動中！"


# 這個 API 是給 LINE 平台呼叫的 webhook 入口
@app.route("/callback", methods=["POST"])
def callback():
    # 從 Header 中取出 LINE 的簽章
    signature = request.headers.get("X-Line-Signature")

    # 取得 webhook 原始內容
    body = request.get_data(as_text=True)

    # 如果沒有簽章，直接報錯
    if signature is None:
        abort(400)

    # 驗證簽章並處理事件
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook 處理失敗: {e}")
        abort(400)

    return "OK"


# 這個事件處理器專門處理使用者的文字訊息
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 取得使用者傳來的文字
    user_text = event.message.text.strip()

    # 預設回覆文字
    reply_text = ""

    # 1. 今日收支報表
    if user_text == "今天":
        reply_text = build_today_report()

    # 4. 本月完整報表
    elif user_text in ["本月報表", "本月收支"]:
        reply_text = build_month_report()

    # 5. 本月支出報表
    elif user_text == "本月支出":
        reply_text = build_month_expense_report()

    # 6. 本月收入報表
    elif user_text == "本月收入":
        reply_text = build_month_income_report()

    # 7. 最近支出明細
    elif user_text == "最近支出":
        reply_text = build_recent_expense_list()

    # 8. 最近收入明細
    elif user_text == "最近收入":
        reply_text = build_recent_income_list()

    # 9. 查看支出
    elif user_text.startswith("查看支出 "):
        parts = user_text.split()

        if len(parts) != 2 or not parts[1].isdigit():
            reply_text = "☁️ 格式錯誤，請使用：查看支出 ID"
        else:
            expense_id = int(parts[1])
            expense = get_expense_by_id(expense_id)

            if expense is None:
                reply_text = "☁️ 找不到這筆支出資料"
            else:
                reply_text = (
                    "☁️ 支出資料如下\n"
                    f"ID：{expense.id}\n"
                    f"類別：{expense.category}\n"
                    f"金額：{expense.amount} 元\n"
                    f"備註：{expense.note or '無'}\n"
                    f"時間：{format_datetime_text(expense.created_at)}"
                )

    # 10. 查看收入
    elif user_text.startswith("查看收入 "):
        parts = user_text.split()

        if len(parts) != 2 or not parts[1].isdigit():
            reply_text = "☁️ 格式錯誤，請使用：查看收入 ID"
        else:
            income_id = int(parts[1])
            income = get_income_by_id(income_id)

            if income is None:
                reply_text = "☁️ 找不到這筆收入資料"
            else:
                reply_text = (
                    "☁️ 收入資料如下\n"
                    f"ID：{income.id}\n"
                    f"類別：{income.category}\n"
                    f"金額：{income.amount} 元\n"
                    f"備註：{income.note or '無'}\n"
                    f"時間：{format_datetime_text(income.created_at)}"
                )

    # 11. 刪除支出
    elif user_text.startswith("刪除支出 "):
        parts = user_text.split()

        if len(parts) != 2 or not parts[1].isdigit():
            reply_text = "☁️ 格式錯誤，請使用：刪除支出 ID"
        else:
            expense_id = int(parts[1])
            success = delete_expense(expense_id)

            if success:
                reply_text = f"☁️ 已刪除支出 ID：{expense_id}"
            else:
                reply_text = "☁️ 找不到這筆支出資料，或刪除失敗"

    # 12. 刪除收入
    elif user_text.startswith("刪除收入 "):
        parts = user_text.split()

        if len(parts) != 2 or not parts[1].isdigit():
            reply_text = "☁️ 格式錯誤，請使用：刪除收入 ID"
        else:
            income_id = int(parts[1])
            success = delete_income(income_id)

            if success:
                reply_text = f"☁️ 已刪除收入 ID：{income_id}"
            else:
                reply_text = "☁️ 找不到這筆收入資料，或刪除失敗"

    # 13. 修改支出
    elif user_text.startswith("修改支出 "):
        parts = user_text.split()

        if len(parts) < 4:
            reply_text = "☁️ 格式錯誤，請使用：修改支出 ID 類別 金額 備註"
        else:
            expense_id_text = parts[1]
            category = parts[2]
            amount_text = parts[3]
            note = " ".join(parts[4:]) if len(parts) > 4 else ""

            if not expense_id_text.isdigit():
                reply_text = "☁️ 支出 ID 必須是數字"
            else:
                try:
                    amount = int(amount_text)
                except ValueError:
                    reply_text = "☁️ 金額必須是整數"
                else:
                    expense = update_expense(
                        int(expense_id_text),
                        category,
                        amount,
                        note
                    )

                    if expense is None:
                        reply_text = "☁️ 找不到這筆支出資料，或修改失敗"
                    else:
                        reply_text = (
                            "☁️ 大耳狗幫你修改好支出了！\n"
                            f"ID：{expense.id}\n"
                            f"類別：{expense.category}\n"
                            f"金額：{expense.amount} 元\n"
                            f"備註：{expense.note or '無'}"
                        )

    # 14. 修改收入
    elif user_text.startswith("修改收入 "):
        parts = user_text.split()

        if len(parts) < 4:
            reply_text = "☁️ 格式錯誤，請使用：修改收入 ID 類別 金額 備註"
        else:
            income_id_text = parts[1]
            category = parts[2]
            amount_text = parts[3]
            note = " ".join(parts[4:]) if len(parts) > 4 else ""

            if not income_id_text.isdigit():
                reply_text = "☁️ 收入 ID 必須是數字"
            else:
                try:
                    amount = int(amount_text)
                except ValueError:
                    reply_text = "☁️ 金額必須是整數"
                else:
                    income = update_income(
                        int(income_id_text),
                        category,
                        amount,
                        note
                    )

                    if income is None:
                        reply_text = "☁️ 找不到這筆收入資料，或修改失敗"
                    else:
                        reply_text = (
                            "☁️ 大耳狗幫你修改好收入了！\n"
                            f"ID：{income.id}\n"
                            f"類別：{income.category}\n"
                            f"金額：{income.amount} 元\n"
                            f"備註：{income.note or '無'}"
                        )

    # 15. 自動判斷收入或支出記帳
    else:
        # 解析使用者輸入的記帳內容
        # 例如：薪水 45000 五月薪水 / 餐飲 150 午餐
        parsed_record = parse_record_text(user_text)

        # 如果格式錯誤，回覆提示
        if parsed_record is None:
            reply_text = (
                "☁️ 大耳狗看不懂這筆記帳喔！\n"
                "請直接用這種格式：類別 金額 備註\n\n"
                "支出範例：餐飲 150 午餐\n"
                "收入範例：薪水 45000 五月薪水\n\n"
            )
        else:
            # 如果判斷為收入，就寫入收入資料
            if parsed_record["type"] == "income":
                income = add_income(
                    parsed_record["category"],
                    parsed_record["amount"],
                    parsed_record["note"]
                )

                # 根據寫入結果回覆
                if income is None:
                    reply_text = "☁️ 大耳狗記收入失敗了，請稍後再試一次。"
                else:
                    reply_text = (
                        "☁️ 大耳狗幫你記好收入了！\n"
                        f"ID：{income.id}\n"
                        f"類別：{income.category}\n"
                        f"金額：{income.amount} 元\n"
                        f"備註：{income.note or '無'}"
                    )

            # 否則一律當成支出處理
            else:
                expense = add_expense(
                    parsed_record["category"],
                    parsed_record["amount"],
                    parsed_record["note"]
                )

                # 根據寫入結果回覆
                if expense is None:
                    reply_text = "☁️ 大耳狗記支出失敗了，請稍後再試一次。"
                else:
                    reply_text = (
                        "☁️ 大耳狗幫你記好支出了！\n"
                        f"ID：{expense.id}\n"
                        f"類別：{expense.category}\n"
                        f"金額：{expense.amount} 元\n"
                        f"備註：{expense.note or '無'}"
                    )

    # 使用 LINE Messaging API 回覆使用者
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


# 直接執行這個檔案時，啟動 Flask 開發伺服器
if __name__ == "__main__":
    # Render 會提供 PORT 環境變數
    # 本機沒有 PORT 時，就預設使用 5050
    port = int(os.getenv("PORT", 5050))

    # host 要設成 0.0.0.0，Render 才能從外部連進來
    app.run(host="0.0.0.0", port=port, debug=True)