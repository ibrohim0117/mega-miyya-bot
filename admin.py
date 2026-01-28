import logging
from datetime import datetime
from io import BytesIO
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from database import get_user_count, get_all_users, get_user_voices, get_user_by_id
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
