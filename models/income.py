# 匯入 SQLAlchemy 欄位型別
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

# 匯入 declarative_base，用來建立 ORM Model 的基底類別
from sqlalchemy.orm import declarative_base

# 匯入 datetime，讓 created_at 可以自動記錄建立時間
from datetime import datetime

# 建立 Income Model 專用的 Base
Base = declarative_base()


# 這個類別代表收入資料表
class Income(Base):
    # 資料表名稱
    __tablename__ = "incomes"

    # 主鍵 id
    id = Column(Integer, primary_key=True)

    # 收入類別，例如：薪水、獎金、退款
    category = Column(String)

    # 收入金額
    amount = Column(Integer)

    # 備註，例如：五月薪水、客戶退款
    note = Column(String)

    # 建立時間，預設使用目前時間
    created_at = Column(
        DateTime,
        default=datetime.now
    )