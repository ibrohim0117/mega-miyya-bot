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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS voices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
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

async def get_all_user_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_user_by_id(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, username, first_name, last_name, created_at FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def save_voice(user_id: int, text: str, file_id: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO voices (user_id, text, file_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, text, file_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            await db.commit()
    except Exception as e:
        logging.error(f"Ovozni saqlashda xatolik: {e}")

async def get_user_voices(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT id, text, file_id, created_at FROM voices 
            WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_all_voices():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT v.id, v.user_id, u.username, v.text, v.file_id, v.created_at 
            FROM voices v
            LEFT JOIN users u ON v.user_id = u.user_id
            ORDER BY v.created_at DESC
        """) as cursor:
            return await cursor.fetchall()

async def get_voice_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM voices") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0
