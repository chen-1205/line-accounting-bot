# 匯入剛剛寫好的文字解析函式
from services.parser import parse_expense_text

# 測試案例 1：有類別、金額、備註
text1 = "餐飲 150 午餐"

# 測試案例 2：有類別、金額、備註
text2 = "交通 30 捷運"

# 測試案例 3：只有類別和金額，沒有備註
text3 = "飲料 60"

# 測試案例 4：格式錯誤，第二個欄位不是數字
text4 = "餐飲 午餐"

# 印出解析結果，確認函式有沒有正常運作
print(parse_expense_text(text1))
print(parse_expense_text(text2))
print(parse_expense_text(text3))
print(parse_expense_text(text4))