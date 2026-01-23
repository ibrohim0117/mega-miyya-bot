import aiosqlite
import logging
from datetime import datetime

DB_NAME = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def save_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            await db.commit()
    except Exception as e:
        logging.error(f"Foydalanuvchini saqlashda xatolik: {e}")

async def get_user_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, username, first_name, last_name, created_at FROM users ORDER BY created_at") as cursor:
            return await cursor.fetchall()

async def get_user_by_id(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, username, first_name, last_name, created_at FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()
