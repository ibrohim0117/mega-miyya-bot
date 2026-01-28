import os
import logging
import edge_tts
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from database import save_voice

VOICE_DIR = "voice_files"
VOICE_NAME = "uz-UZ-SardorNeural"

os.makedirs(VOICE_DIR, exist_ok=True)

async def text_to_speech(text: str, user_id: int) -> str:
    file_path = os.path.join(VOICE_DIR, f"voice_{user_id}.mp3")
    communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME)
    await communicate.save(file_path)
    return file_path

def cleanup_voice_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging.error(f"Voice faylni o'chirishda xatolik: {e}")

def register_voice_handlers(dp):
    @dp.message(Command("text_to_voice"))
    async def cmd_text_to_voice(message: types.Message):
        await message.answer(
            "🎙 Menga istalgan matn yuboring — men uni OVOZLI qilib beraman!\n\n"
            "Bekor qilish uchun /cancel buyrug'ini yuboring."
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: types.Message):
        await message.answer("❌ Bekor qilindi.")

    @dp.message(F.text & F.reply_to_message)
    async def reply_text_to_voice(message: types.Message):
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
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
                
            except Exception as e:
                logging.error(f"Text to voice xatolik: {e}")
                await processing_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")
                
            finally:
                if file_path:
                    cleanup_voice_file(file_path)
