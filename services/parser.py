# 這個函式負責把使用者輸入的一整句記帳文字拆解成資料
# 例如："餐飲 150 午餐" -> 類別=餐飲、金額=150、備註=午餐

def parse_expense_text(text):
    # 先把字串前後空白去掉，再依照空白切開
    parts = text.strip().split()

    # 至少要有兩個欄位：類別 + 金額
    # 例如只有「餐飲」這種格式就不合法
    if len(parts) < 2:
        return None

    # 第一個欄位視為類別
    category = parts[0]

    # 第二個欄位必須是整數金額
    try:
        amount = int(parts[1])
    except ValueError:
        # 如果第二個欄位不是數字，代表格式錯誤
        return None

    # 預設備註為空字串
    note = ""

    # 如果第三個欄位之後還有內容，就把它們合併成備註
    # 例如："餐飲 150 牛肉麵 午餐" -> 備註會是 "牛肉麵 午餐"
    if len(parts) > 2:
        note = " ".join(parts[2:])

    # 回傳整理好的結果，方便後續直接存進資料庫
    return {
        "category": category,
        "amount": amount,
        "note": note
    }