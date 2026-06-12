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
    get_today_total,
    get_category_summary,
)

# 匯入收入服務
from services.income import (
    add_income,
    get_today_income_total,
    get_income_category_summary,
)

# 匯入報表服務
from services.report import (
    build_today_report,
    build_expense_summary_report,
    build_income_summary_report,
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
# 這裡會自動建立 expenses 與 incomes
ExpenseBase.metadata.create_all(engine)
IncomeBase.metadata.create_all(engine)

# 建立 Flask 應用程式
app = Flask(__name__)


# 這個函式用來解析收入格式
# 格式範例：收入 薪水 45000 五月薪水
def parse_income_text(text):
    # 先依照空白切開文字
    parts = text.strip().split()

    # 至少要有：收入 類別 金額
    if len(parts) < 3:
        return None

    # 第一個欄位必須是「收入」
    if parts[0] != "收入":
        return None

    # 第二個欄位視為收入類別
    category = parts[1]

    # 第三個欄位必須是金額
    try:
        amount = int(parts[2])
    except ValueError:
        return None

    # 第四個欄位之後視為備註
    note = ""
    if len(parts) > 3:
        note = " ".join(parts[3:])

    # 回傳解析結果
    return {
        "category": category,
        "amount": amount,
        "note": note
    }


# 這個 API 用來測試 Flask 是否成功啟動
@app.route("/")
def home():
    return "☁️ 大耳狗記帳小管家啟動中！Render 部署成功！"


# 這個 API 用來接收表單格式的支出資料
@app.route("/add", methods=["POST"])
def add():
    # 從表單中取得類別、金額、備註
    category = request.form.get("category")
    amount = request.form.get("amount")
    note = request.form.get("note", "")

    # 檢查必要欄位
    if not category or not amount:
        return "缺少 category 或 amount", 400

    # 金額轉整數
    try:
        amount = int(amount)
    except ValueError:
        return "amount 必須是整數", 400

    # 寫入支出資料
    expense = add_expense(category, amount, note)

    # 如果寫入失敗，回傳錯誤
    if expense is None:
        return "新增失敗", 500

    return f"已新增支出：{expense.category} {expense.amount} {expense.note}"


# 這個 API 用來接收表單格式的收入資料
@app.route("/add_income", methods=["POST"])
def add_income_api():
    # 從表單中取得類別、金額、備註
    category = request.form.get("category")
    amount = request.form.get("amount")
    note = request.form.get("note", "")

    # 檢查必要欄位
    if not category or not amount:
        return "缺少 category 或 amount", 400

    # 金額轉整數
    try:
        amount = int(amount)
    except ValueError:
        return "amount 必須是整數", 400

    # 寫入收入資料
    income = add_income(category, amount, note)

    # 如果寫入失敗，回傳錯誤
    if income is None:
        return "新增失敗", 500

    return f"已新增收入：{income.category} {income.amount} {income.note}"


# 這個 API 用來查詢今天總支出
@app.route("/today")
def today():
    total = get_today_total()
    return f"今日總支出：{total}"


# 這個 API 用來查詢今天總收入
@app.route("/today_income")
def today_income():
    total = get_today_income_total()
    return f"今日總收入：{total}"


# 這個 API 用來查詢支出分類統計
@app.route("/summary")
def summary():
    data = get_category_summary()

    # 如果沒有資料，回傳提示
    if not data:
        return "目前沒有任何支出統計資料"

    # 整理回傳文字
    lines = []
    for category, total in data.items():
        lines.append(f"{category}：{total}")

    return "\n".join(lines)


# 這個 API 用來查詢收入分類統計
@app.route("/income_summary")
def income_summary():
    data = get_income_category_summary()

    # 如果沒有資料，回傳提示
    if not data:
        return "目前沒有任何收入統計資料"

    # 整理回傳文字
    lines = []
    for category, total in data.items():
        lines.append(f"{category}：{total}")

    return "\n".join(lines)


# 這個 API 是給 LINE 平台呼叫的 webhook 入口
@app.route("/callback", methods=["POST"])
def callback():
    # 從 Header 中取出 LINE 的簽章
    signature = request.headers.get("X-Line-Signature")

    # 取得 webhook 原始內容
    body = request.get_data(as_text=True)

    # 印出除錯資訊
    print("=== CALLBACK START ===")
    print("Signature:", signature)
    print("Body:", body)

    # 如果沒有簽章，直接報錯
    if signature is None:
        print("沒有收到 X-Line-Signature")
        abort(400)

    # 驗證簽章並處理事件
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook 處理失敗: {e}")
        abort(400)

    print("=== CALLBACK OK ===")
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

    # 2. 支出統計
    elif user_text == "統計":
        reply_text = build_expense_summary_report()

    # 3. 收入統計
    elif user_text == "收入統計":
        reply_text = build_income_summary_report()

    # 4. 本月完整報表
    elif user_text in ["本月報表", "本月收支"]:
        reply_text = build_month_report()

    # 5. 本月支出報表
    elif user_text == "本月支出":
        reply_text = build_month_expense_report()

    # 6. 本月收入報表
    elif user_text == "本月收入":
        reply_text = build_month_income_report()

    # 7. 收入記帳
    elif user_text.startswith("收入 "):
        # 解析收入格式
        parsed_income = parse_income_text(user_text)

        # 如果格式錯誤，就回覆正確格式
        if parsed_income is None:
            reply_text = (
                "☁️ 大耳狗看不懂這筆收入喔！\n"
                "請使用這種格式：收入 類別 金額 備註\n"
                "例如：收入 薪水 45000 五月薪水"
            )
        else:
            # 寫入收入資料
            income = add_income(
                parsed_income["category"],
                parsed_income["amount"],
                parsed_income["note"]
            )

            # 根據寫入結果回覆
            if income is None:
                reply_text = "☁️ 大耳狗記收入失敗了，請稍後再試一次。"
            else:
                reply_text = (
                    "☁️ 大耳狗幫你記好收入了！\n"
                    f"類別：{income.category}\n"
                    f"金額：{income.amount} 元\n"
                    f"備註：{income.note or '無'}"
                )

    # 8. 一般支出記帳
    else:
        # 用原本的 parser 解析支出格式
        parsed_expense = parse_expense_text(user_text)

        # 如果格式錯誤，回覆提示
        if parsed_expense is None:
            reply_text = (
                "☁️ 大耳狗看不懂這筆記帳喔！\n"
                "支出格式：類別 金額 備註\n"
                "例如：餐飲 150 午餐\n\n"
                "收入格式：收入 類別 金額 備註\n"
                "例如：收入 薪水 45000 五月薪水"
            )
        else:
            # 寫入支出資料
            expense = add_expense(
                parsed_expense["category"],
                parsed_expense["amount"],
                parsed_expense["note"]
            )

            # 根據寫入結果回覆
            if expense is None:
                reply_text = "☁️ 大耳狗記支出失敗了，請稍後再試一次。"
            else:
                reply_text = (
                    "☁️ 大耳狗幫你記好支出了！\n"
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