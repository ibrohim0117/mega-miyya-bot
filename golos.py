import os
import logging
import asyncio
import socket
import aiohttp
import edge_tts
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import save_voice

VOICE_DIR = "voice_files"
VOICE_NAME = "uz-UZ-SardorNeural"

TTS_PROXY = os.getenv("TTS_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
TTS_FORCE_IPV4 = os.getenv("TTS_FORCE_IPV4", "1") == "1"
TTS_CONNECT_TIMEOUT = int(os.getenv("TTS_CONNECT_TIMEOUT", "10"))
TTS_RECEIVE_TIMEOUT = int(os.getenv("TTS_RECEIVE_TIMEOUT", "60"))
TTS_RETRIES = max(1, int(os.getenv("TTS_RETRIES", "3")))
TTS_RETRY_DELAY = float(os.getenv("TTS_RETRY_DELAY", "1.5"))

os.makedirs(VOICE_DIR, exist_ok=True)

CYRILLIC_TO_LATIN = {
    'А': 'A', 'а': 'a',
    'Б': 'B', 'б': 'b',
    'В': 'V', 'в': 'v',
    'Г': 'G', 'г': 'g',
    'Д': 'D', 'д': 'd',
    'Е': 'E', 'е': 'e',
    'Ё': 'Yo', 'ё': 'yo',
    'Ж': 'J', 'ж': 'j',
    'З': 'Z', 'з': 'z',
    'И': 'I', 'и': 'i',
    'Й': 'Y', 'й': 'y',
    'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l',
    'М': 'M', 'м': 'm',
    'Н': 'N', 'н': 'n',
    'О': 'O', 'о': 'o',
    'П': 'P', 'п': 'p',
    'Р': 'R', 'р': 'r',
    'С': 'S', 'с': 's',
    'Т': 'T', 'т': 't',
    'У': 'U', 'у': 'u',
    'Ф': 'F', 'ф': 'f',
    'Х': 'X', 'х': 'x',
    'Ц': 'Ts', 'ц': 'ts',
    'Ч': 'Ch', 'ч': 'ch',
    'Ш': 'Sh', 'ш': 'sh',
    'Щ': 'Sh', 'щ': 'sh',
    'Ъ': "'", 'ъ': "'",
    'Ы': 'I', 'ы': 'i',
    'Ь': '', 'ь': '',
    'Э': 'E', 'э': 'e',
    'Ю': 'Yu', 'ю': 'yu',
    'Я': 'Ya', 'я': 'ya',
    'Ў': "O'", 'ў': "o'",
    'Қ': 'Q', 'қ': 'q',
    'Ғ': "G'", 'ғ': "g'",
    'Ҳ': 'H', 'ҳ': 'h',
}

def has_cyrillic(text: str) -> bool:
    for char in text:
        if char in CYRILLIC_TO_LATIN:
            return True
    return False

def cyrillic_to_latin(text: str) -> str:
    result = []
    for char in text:
        if char in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[char])
        else:
            result.append(char)
    return ''.join(result)

class VoiceStates(StatesGroup):
    waiting_for_text = State()

async def text_to_speech(text: str, user_id: int) -> str:
    if has_cyrillic(text):
        text = cyrillic_to_latin(text)
    
    file_path = os.path.join(VOICE_DIR, f"voice_{user_id}.mp3")
    connector = aiohttp.TCPConnector(family=socket.AF_INET) if TTS_FORCE_IPV4 else None
    try:
        last_err: Exception | None = None
        for attempt in range(1, TTS_RETRIES + 1):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=VOICE_NAME,
                    connector=connector,
                    proxy=TTS_PROXY,
                    connect_timeout=TTS_CONNECT_TIMEOUT,
                    receive_timeout=TTS_RECEIVE_TIMEOUT,
                )
                await communicate.save(file_path)
                last_err = None
                break
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
                last_err = e
                if attempt < TTS_RETRIES:
                    await asyncio.sleep(TTS_RETRY_DELAY * attempt)
                else:
                    raise
        if last_err is not None:
            raise last_err
    finally:
        if connector is not None:
            try:
                await connector.close()
            except Exception:
                pass
    return file_path

def cleanup_voice_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging.error(f"Voice faylni o'chirishda xatolik: {e}")

def register_voice_handlers(dp):
    @dp.message(Command("text_to_voice"))
    async def cmd_text_to_voice(message: types.Message, state: FSMContext):
        await state.set_state(VoiceStates.waiting_for_text)
        await message.answer(
            "🎙 Menga istalgan matn yuboring — men uni OVOZLI qilib beraman!\n\n"
            "Kirill yoki Lotin harflarida yozishingiz mumkin.\n"
            "Bekor qilish uchun /cancel buyrug'ini yuboring."
        )

    @dp.message(Command("cancel"), VoiceStates.waiting_for_text)
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("❌ Bekor qilindi.")

    @dp.message(VoiceStates.waiting_for_text, F.text)
    async def process_text_to_voice(message: types.Message, state: FSMContext):
        text = message.text
        
        if text.startswith("/"):
            return
        
        if len(text) > 3000:
            await message.answer("❌ Matn juda uzun! Maksimum 3000 ta belgi.")
            return
        
        processing_msg = await message.answer("⏳ Ovozga aylantirilmoqda...")
        file_path = None
        
        try:
            file_path = await text_to_speech(text, message.from_user.id)
            
            sent_voice = await message.answer_voice(
                voice=FSInputFile(file_path),
                caption="🔊 Sizning matnningiz ovozli versiyasi"
            )
            await processing_msg.delete()
            
            if sent_voice.voice:
                await save_voice(
                    user_id=message.from_user.id,
                    text=text,
                    file_id=sent_voice.voice.file_id
                )
            
            await state.clear()
            
        except Exception as e:
            logging.error(f"Text to voice xatolik: {e}")
            await processing_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")
            await state.clear()
            
        finally:
            if file_path:
                cleanup_voice_file(file_path)
