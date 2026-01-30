import asyncio
import random
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from database import init_db, save_user
from admin import register_admin_handlers, set_admin_ids
from aiogram.client.session.aiohttp import AiohttpSession

from golos import register_voice_handlers

PROXY_URL = 'http://proxy.server:3128'
session = AiohttpSession(proxy=PROXY_URL)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip()]

os.makedirs("logs", exist_ok=True)

log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

file_handler = RotatingFileHandler(
    'logs/bot.log',
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

bot = Bot(token=TOKEN, session=session)
# bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

set_admin_ids(ADMIN_IDS)

LEVELS = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}

class GameStates(StatesGroup):
    showing = State()
    choosing = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await state.clear()
    await state.update_data(level=1)
    await message.answer("🧠 **Mantiqiy xotira o'yiniga xush kelibsiz!**\n\nMen sizga sonlarni ko'rsataman, siz ularni tartib bilan topishingiz kerak.")
    await start_new_level(message, state)

async def start_new_level(message: types.Message, state: FSMContext):
    data = await state.get_data()
    level = data.get("level", 1)
    count = LEVELS[level]
    
    sequence = [random.randint(1, 50) for _ in range(count)]
    await state.update_data(sequence=sequence, user_answers=[])
    
    msg = await message.answer(f"🚀 **{level}-bosqich boshlandi!**\nDiqqat qiling...")
    await asyncio.sleep(1)

    for idx, num in enumerate(sequence):
        try:
            await msg.edit_text(f"Eslab qoling: \n\n#️⃣  **{num}**", parse_mode="Markdown")
        except Exception:
            pass
        await asyncio.sleep(2.0)
    
    try:
        await msg.edit_text("🔢 Endi sonlarni to'g'ri tartibda tanlang!")
    except Exception:
        pass
    
    await state.set_state(GameStates.choosing)
    await send_game_keyboard(message.chat.id, sequence)

async def send_game_keyboard(chat_id, sequence):
    builder = InlineKeyboardBuilder()
    
    options = set(sequence)
    while len(options) < 10:
        options.add(random.randint(1, 50))
    
    buttons_list = list(options)
    random.shuffle(buttons_list)
    
    for num in buttons_list:
        builder.button(text=str(num), callback_data=f"ans_{num}")
    
    builder.adjust(3)
    await bot.send_message(chat_id, "Tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(GameStates.choosing, F.data.startswith("ans_"))
async def check_answer(callback: types.CallbackQuery, state: FSMContext):
    selected = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    level = data.get("level")
    sequence = data.get("sequence")
    user_answers = data.get("user_answers")

    if level is None or not sequence or user_answers is None:
        try:
            await callback.answer("Sessiya tugagan. Qayta boshlash: /start", show_alert=True)
        except Exception:
            pass
        try:
            await callback.message.delete()
        except Exception:
            pass
        return
    
    current_step = len(user_answers)
    if current_step >= len(sequence):
        try:
            await callback.answer("Bu o'yin allaqachon yakunlangan. /start", show_alert=True)
        except Exception:
            pass
        try:
            await callback.message.delete()
        except Exception:
            pass
        await state.clear()
        return
    
    if selected == sequence[current_step]:
        user_answers.append(selected)
        await state.update_data(user_answers=user_answers)
        
        if len(user_answers) == len(sequence):
            await callback.message.delete()
            if level < 5:
                await callback.message.answer(f"✅ To'g'ri! {level}-bosqich yakunlandi.")
                await state.update_data(level=level + 1)
                await start_new_level(callback.message, state)
            else:
                await callback.message.answer("🏆 **TABRIKLAYMIZ!**\nSiz barcha 5 ta bosqichdan muvaffaqiyatli o'tdingiz!")
                await state.clear()
        else:
            await callback.answer(f"To'g'ri! Yana {len(sequence) - len(user_answers)} ta qoldi.")
    else:
        await callback.message.delete()
        await callback.message.answer(f"❌ Xato qildingiz! To'g'ri javob: **{sequence[current_step]}** edi.\nO'yin tugadi. Qaytadan boshlash uchun: /start", parse_mode="Markdown")
        await state.clear()

register_admin_handlers(dp, bot)
register_voice_handlers(dp)

async def main():
    await init_db()
    logging.info("Ma'lumotlar bazasi ishga tushirildi")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
