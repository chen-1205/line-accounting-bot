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

# 匯入你自己寫好的記帳服務
from services.accounting import (
    add_expense,
    get_today_total,
    get_category_summary,
)

# 匯入你自己寫好的文字解析器
from services.parser import parse_expense_text

# 匯入 Expense 的 Base 與資料庫 engine，用來在啟動時自動建立資料表
from models.expense import Base
from models.database import engine

# 載入專案根目錄中的 .env 檔案
load_dotenv()

# 從 .env 讀取 LINE Bot 的 Channel Secret
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# 從 .env 讀取 LINE Bot 的 Channel Access Token
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")

# 印出 .env 是否有成功讀到，方便除錯
print("CHANNEL_SECRET 已讀取：", bool(CHANNEL_SECRET))
print("CHANNEL_ACCESS_TOKEN 已讀取：", bool(CHANNEL_ACCESS_TOKEN))

# 建立 LINE Messaging API 的設定物件
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 建立 WebhookHandler，用來驗證 LINE 傳來的 webhook 簽章
handler = WebhookHandler(CHANNEL_SECRET)

# 在應用程式啟動時，自動建立 Expense 資料表
# 這樣即使在 Render 免費方案沒有使用 Shell，也能先完成基本資料表初始化
Base.metadata.create_all(engine)

# 建立 Flask 應用程式
app = Flask(__name__)


# 這個 API 用來測試 Flask 是否成功啟動
@app.route("/")
def home():
    return "☁️ 大耳狗記帳小管家啟動中！Render 部署成功！"


# 這個 API 用來接收表單格式的記帳資料
# 例如：category=餐飲、amount=150、note=午餐
@app.route("/add", methods=["POST"])
def add():
    # 從表單中取得類別、金額、備註
    category = request.form.get("category")
    amount = request.form.get("amount")
    note = request.form.get("note", "")

    # 如果缺少必要欄位，就直接回傳錯誤
    if not category or not amount:
        return "缺少 category 或 amount", 400

    # 將金額轉成整數，避免資料格式錯誤
    try:
        amount = int(amount)
    except ValueError:
        return "amount 必須是整數", 400

    # 呼叫記帳函式，把資料寫入資料庫
    expense = add_expense(category, amount, note)

    # 如果新增失敗，回傳伺服器錯誤
    if expense is None:
        return "新增失敗", 500

    # 新增成功後，回傳新增結果
    return f"已新增：{expense.category} {expense.amount} {expense.note}"


# 這個 API 用來接收一整句文字記帳
# 例如：text=餐飲 150 午餐
@app.route("/add_text", methods=["POST"])
def add_text():
    # 從表單中取得整句文字
    text = request.form.get("text", "")

    # 如果沒有傳入文字，就回傳錯誤
    if not text:
        return "缺少 text", 400

    # 呼叫文字解析器，把一句話拆成類別、金額、備註
    parsed = parse_expense_text(text)

    # 如果解析失敗，代表輸入格式不正確
    if parsed is None:
        return "格式錯誤，請使用：類別 金額 備註", 400

    # 把解析出來的資料寫入資料庫
    expense = add_expense(
        parsed["category"],
        parsed["amount"],
        parsed["note"],
    )

    # 如果新增失敗，回傳伺服器錯誤
    if expense is None:
        return "新增失敗", 500

    # 新增成功後，回傳結果
    return f"已新增：{expense.category} {expense.amount} {expense.note}"


# 這個 API 用來查詢今天的總支出
@app.route("/today")
def today():
    # 取得今天所有支出的加總
    total = get_today_total()
    return f"今日總支出：{total}"


# 這個 API 用來查詢所有類別的支出統計
@app.route("/summary")
def summary():
    # 取得各類別的總支出資料
    data = get_category_summary()

    # 如果目前沒有資料，就回傳提示訊息
    if not data:
        return "目前沒有任何統計資料"

    # 把每個類別整理成一行文字
    lines = []
    for category, total in data.items():
        lines.append(f"{category}：{total}")

    # 使用換行符號組合成最後回傳內容
    return "\n".join(lines)


# 這個 API 是給 LINE 平台呼叫的 webhook 入口
@app.route("/callback", methods=["POST"])
def callback():
    # 從 HTTP Header 中取出 LINE 傳來的簽章
    signature = request.headers.get("X-Line-Signature")

    # 取得 webhook 的原始內容
    body = request.get_data(as_text=True)

    # 印出收到的資料，方便除錯
    print("=== CALLBACK START ===")
    print("Signature:", signature)
    print("Body:", body)

    # 如果沒有簽章，代表請求格式有問題
    if signature is None:
        print("沒有收到 X-Line-Signature")
        abort(400)

    # 交給 LINE SDK 驗證簽章並分派事件
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook 處理失敗: {e}")
        abort(400)

    # 告訴 LINE 我們有成功收到 webhook
    print("=== CALLBACK OK ===")
    return "OK"


# 這個事件處理器專門接收「使用者傳來的文字訊息」
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 取得使用者實際傳來的文字內容
    user_text = event.message.text

    # 先處理查詢指令：今天
    if user_text == "今天":
        total = get_today_total()
        reply_text = f"☁️ 大耳狗今日總支出：{total} 元"

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        return

    # 再處理查詢指令：統計
    if user_text == "統計":
        summary_data = get_category_summary()

        if not summary_data:
            reply_text = "☁️ 目前還沒有任何統計資料"
        else:
            lines = ["☁️ 大耳狗分類統計"]
            for category, total in summary_data.items():
                lines.append(f"{category}：{total} 元")
            reply_text = "\n".join(lines)

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        return

    # 一般情況下，把文字當成記帳輸入來解析
    parsed = parse_expense_text(user_text)

    # 如果格式錯誤，就回覆使用者正確格式
    if parsed is None:
        reply_text = (
            "☁️ 大耳狗看不懂這筆記帳喔！\n"
            "請使用這種格式：類別 金額 備註\n"
            "例如：餐飲 150 午餐"
        )

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
        return

    # 解析成功後，把資料寫入資料庫
    expense = add_expense(
        parsed["category"],
        parsed["amount"],
        parsed["note"],
    )

    # 如果資料庫寫入失敗，就回覆錯誤訊息
    if expense is None:
        reply_text = "☁️ 大耳狗記帳失敗了，請稍後再試一次。"
    else:
        # 如果成功，就回覆記帳結果給使用者
        reply_text = (
            "☁️ 大耳狗幫你記好了！\n"
            f"類別：{expense.category}\n"
            f"金額：{expense.amount} 元\n"
            f"備註：{expense.note or '無'}"
        )

    # 使用 LINE Messaging API 回覆訊息
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