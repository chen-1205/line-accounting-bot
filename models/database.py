# 匯入 os，用來讀取 Render 或本機的環境變數
import os

# 匯入 SQLAlchemy 建立資料庫引擎與 Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 先從環境變數讀取 DATABASE_URL
# 在 Render 上部署時，這裡會拿到 PostgreSQL 的連線字串
database_url = os.getenv("DATABASE_URL")

# 如果有 DATABASE_URL，就代表目前在 Render 或其他雲端環境
# 這時候使用 PostgreSQL
if database_url:
    # 有些平台提供的 PostgreSQL 連線字串可能是 postgres:// 開頭
    # SQLAlchemy 需要的是 postgresql://，所以這裡順手做轉換
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # 建立 PostgreSQL 的資料庫引擎
    engine = create_engine(database_url, echo=True)
else:
    # 如果沒有 DATABASE_URL，就代表目前在本機開發環境
    # 這時候仍然使用 SQLite
    engine = create_engine("sqlite:///database.db", echo=True)

# 建立 Session 工廠，後續可以用 Session() 開啟資料庫連線
Session = sessionmaker(bind=engine)