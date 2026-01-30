import logging
import os
import shutil
import asyncio
from datetime import datetime
from io import BytesIO
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from database import get_user_count, get_all_users, get_user_voices, get_user_by_id, get_all_user_ids, DB_NAME
import html

ADMIN_IDS = []

def set_admin_ids(admin_ids: list):
    global ADMIN_IDS
    ADMIN_IDS = admin_ids

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def escape_html(text: str) -> str:
    return html.escape(str(text)) if text else 'N/A'

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_broadcast_type = State()
    waiting_broadcast_text = State()
    waiting_broadcast_photo = State()
    waiting_broadcast_video = State()

async def generate_users_pdf():
    users = await get_all_users()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.5*inch, rightMargin=0.5*inch)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1
    )
    
    story.append(Paragraph("Foydalanuvchilar Ro'yxati", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    data = [['ID', 'Username', 'Ism', 'Familiya', 'Qo\'shilgan sana']]
    
    if not users:
        data.append(['Ma\'lumot yo\'q', '', '', '', ''])
    else:
        for user in users:
            user_id, username, first_name, last_name, created_at = user
            data.append([
                str(user_id),
                username or 'N/A',
                first_name or 'N/A',
                last_name or 'N/A',
                created_at
            ])
    
    table = Table(data, colWidths=[0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

def register_admin_handlers(dp, bot):
    @dp.message(Command("alluser"))
    async def cmd_alluser(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu buyruq faqat admin uchun!")
            return
        
        count = await get_user_count()
        await message.answer(f"📊 <b>Jami foydalanuvchilar soni:</b> {count}", parse_mode=ParseMode.HTML)

    @dp.message(Command("alluserdocs"))
    async def cmd_alluserdocs(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu buyruq faqat admin uchun!")
            return
        
        try:
            await message.answer("⏳ PDF yaratilmoqda...")
            pdf_buffer = await generate_users_pdf()
            
            await message.answer_document(
                document=types.BufferedInputFile(
                    file=pdf_buffer.getvalue(),
                    filename=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                ),
                caption="📄 Barcha foydalanuvchilar ma'lumotlari"
            )
        except Exception as e:
            logging.error(f"PDF yaratishda xatolik: {e}")
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

    @dp.message(Command("get_bot_db"))
    async def cmd_get_bot_db(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu buyruq faqat admin uchun!")
            return
        
        try:
            if not os.path.exists(DB_NAME):
                await message.answer("❌ Ma'lumotlar bazasi fayli topilmadi!")
                return
            
            await message.answer("⏳ Ma'lumotlar bazasi yuklanmoqda...")
            
            backup_filename = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DB_NAME, backup_filename)
            
            with open(backup_filename, 'rb') as db_file:
                await message.answer_document(
                    document=types.BufferedInputFile(
                        file=db_file.read(),
                        filename=backup_filename
                    ),
                    caption=f"💾 Ma'lumotlar bazasi nusxasi\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            os.remove(backup_filename)
            
        except Exception as e:
            logging.error(f"DB yuborishda xatolik: {e}")
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
            if os.path.exists(backup_filename):
                try:
                    os.remove(backup_filename)
                except:
                    pass

    @dp.message(Command("send_message"))
    async def cmd_send_message(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu buyruq faqat admin uchun!")
            return

        await state.clear()
        await state.set_state(AdminStates.waiting_broadcast_type)

        kb = InlineKeyboardBuilder()
        kb.button(text="📝 Text", callback_data="broadcast:text")
        kb.button(text="🖼 Rasm + caption", callback_data="broadcast:photo")
        kb.button(text="🎞 Video + caption", callback_data="broadcast:video")
        kb.adjust(1)

        await message.answer(
            "Qaysi turdagi xabar yuborasiz?\n\nBekor qilish: /cancel",
            reply_markup=kb.as_markup(),
        )

    @dp.callback_query(AdminStates.waiting_broadcast_type, F.data.startswith("broadcast:"))
    async def cb_broadcast_type(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Admin emas", show_alert=True)
            return

        kind = callback.data.split(":", 1)[1]
        await state.update_data(broadcast_kind=kind)

        if kind == "text":
            await state.set_state(AdminStates.waiting_broadcast_text)
            await callback.message.answer("📝 Matn yuboring.\n\nBekor qilish: /cancel")
        elif kind == "photo":
            await state.set_state(AdminStates.waiting_broadcast_photo)
            await callback.message.answer("🖼 Rasm yuboring (caption bo‘lsa ham bo‘ladi).\n\nBekor qilish: /cancel")
        elif kind == "video":
            await state.set_state(AdminStates.waiting_broadcast_video)
            await callback.message.answer("🎞 Video yuboring (caption bo‘lsa ham bo‘ladi).\n\nBekor qilish: /cancel")
        else:
            await callback.message.answer("❌ Noma’lum tur.")
            await state.clear()

        try:
            await callback.answer()
        except Exception:
            pass

    @dp.message(Command("cancel"), AdminStates.waiting_broadcast_type, AdminStates.waiting_broadcast_text, AdminStates.waiting_broadcast_photo, AdminStates.waiting_broadcast_video)
    async def cmd_cancel_broadcast(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer("❌ Bekor qilindi.")

    async def _broadcast_send(kind: str, text: str | None, file_id: str | None, caption: str | None) -> tuple[int, int]:
        user_ids = await get_all_user_ids()
        ok = 0
        fail = 0

        for uid in user_ids:
            try:
                if kind == "text":
                    await bot.send_message(uid, text or "")
                elif kind == "photo":
                    await bot.send_photo(uid, photo=file_id, caption=caption)
                elif kind == "video":
                    await bot.send_video(uid, video=file_id, caption=caption)
                else:
                    raise ValueError("Unknown broadcast kind")
                ok += 1
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                fail += 1
            except (TelegramForbiddenError, TelegramBadRequest) as e:
                logging.warning(f"Broadcast to {uid} failed: {e}")
                fail += 1
                await asyncio.sleep(0.02)
            except Exception as e:
                logging.exception(f"Broadcast unexpected error to {uid}: {e}")
                fail += 1
                await asyncio.sleep(0.02)

        return ok, fail

    @dp.message(AdminStates.waiting_broadcast_text, F.text)
    async def handle_broadcast_text(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return

        text = message.text
        if text.startswith("/"):
            return

        await message.answer("⏳ Yuborilmoqda...")
        ok, fail = await _broadcast_send(kind="text", text=text, file_id=None, caption=None)
        await state.clear()
        await message.answer(f"✅ Yuborildi: {ok}\n❌ Xato: {fail}")

    @dp.message(AdminStates.waiting_broadcast_photo, F.photo)
    async def handle_broadcast_photo(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return

        photo = message.photo[-1]
        file_id = photo.file_id
        caption = message.caption or None

        await message.answer("⏳ Yuborilmoqda...")
        ok, fail = await _broadcast_send(kind="photo", text=None, file_id=file_id, caption=caption)
        await state.clear()
        await message.answer(f"✅ Yuborildi: {ok}\n❌ Xato: {fail}")

    @dp.message(AdminStates.waiting_broadcast_video, F.video)
    async def handle_broadcast_video(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return

        file_id = message.video.file_id
        caption = message.caption or None

        await message.answer("⏳ Yuborilmoqda...")
        ok, fail = await _broadcast_send(kind="video", text=None, file_id=file_id, caption=caption)
        await state.clear()
        await message.answer(f"✅ Yuborildi: {ok}\n❌ Xato: {fail}")

    @dp.message(Command("get_data_voice"))
    async def cmd_get_data_voice(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu buyruq faqat admin uchun!")
            return
        
        await state.set_state(AdminStates.waiting_for_user_id)
        await message.answer(
            "🔍 Foydalanuvchi ID sini yuboring:\n\n"
            "Bekor qilish uchun /cancel buyrug'ini yuboring."
        )

    @dp.message(Command("cancel"), AdminStates.waiting_for_user_id)
    async def cmd_cancel_admin(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer("❌ Bekor qilindi.")

    @dp.message(AdminStates.waiting_for_user_id, F.text)
    async def process_user_id(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            return
        
        input_text = message.text
        
        if input_text.startswith("/"):
            return
        
        try:
            target_user_id = int(input_text.strip())
        except ValueError:
            await message.answer("❌ Noto'g'ri format! Faqat raqam yuboring.")
            return
        
        user = await get_user_by_id(target_user_id)
        if not user:
            await message.answer(f"❌ ID: {target_user_id} bo'yicha foydalanuvchi topilmadi!")
            await state.clear()
            return
        
        voices = await get_user_voices(target_user_id)
        
        username = escape_html(user[1])
        first_name = escape_html(user[2])
        
        if not voices:
            await message.answer(
                f"📋 <b>Foydalanuvchi:</b> {first_name} (@{username})\n"
                f"🆔 <b>ID:</b> {target_user_id}\n\n"
                f"🔇 Bu foydalanuvchi hali ovoz yubormagan.",
                parse_mode=ParseMode.HTML
            )
            await state.clear()
            return
        
        await message.answer(
            f"📋 <b>Foydalanuvchi:</b> {first_name} (@{username})\n"
            f"🆔 <b>ID:</b> {target_user_id}\n"
            f"🎙 <b>Jami ovozlar:</b> {len(voices)}\n\n"
            f"⏳ Ovozlar yuklanmoqda...",
            parse_mode=ParseMode.HTML
        )
        
        for idx, voice in enumerate(voices, 1):
            voice_id, voice_text, file_id, created_at = voice
            
            escaped_text = escape_html(voice_text[:200])
            suffix = '...' if len(voice_text) > 200 else ''
            
            try:
                await bot.send_voice(
                    chat_id=message.chat.id,
                    voice=file_id,
                    caption=f"🔢 #{idx}\n📝 <b>Matn:</b> {escaped_text}{suffix}\n📅 <b>Sana:</b> {created_at}",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                await message.answer(
                    f"🔢 #{idx}\n"
                    f"📝 <b>Matn:</b> {escaped_text}{suffix}\n"
                    f"📅 <b>Sana:</b> {created_at}\n"
                    f"❌ Ovozni yuborishda xatolik: {escape_html(str(e))}",
                    parse_mode=ParseMode.HTML
                )
        
        await message.answer(f"✅ Jami {len(voices)} ta ovoz yuborildi.")
        await state.clear()
