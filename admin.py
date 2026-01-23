import logging
from datetime import datetime
from io import BytesIO
from aiogram import types
from aiogram.filters import Command
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from database import get_user_count, get_all_users

ADMIN_IDS = []

def set_admin_ids(admin_ids: list):
    global ADMIN_IDS
    ADMIN_IDS = admin_ids

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

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
        await message.answer(f"📊 **Jami foydalanuvchilar soni:** {count}", parse_mode="Markdown")

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
