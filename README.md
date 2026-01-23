# 🧠 Mantiqiy Xotira O'yini Bot

Bu bot Telegram orqali mantiqiy xotira o'yinini o'ynash imkonini beradi. Bot foydalanuvchilarni SQLite bazasiga saqlaydi va admin uchun maxsus buyruqlar bilan ta'minlangan.

## 📋 Talablar

- Python 3.7+
- Telegram Bot Token

## 🚀 O'rnatish

1. **Repository ni klon qiling yoki yuklab oling:**
   ```bash
   cd game
   ```

2. **Virtual environment yarating va faollashtiring:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows uchun: venv\Scripts\activate
   ```

3. **Kerakli paketlarni o'rnating:**
   ```bash
   pip install aiogram aiosqlite reportlab python-dotenv
   ```

4. **Environment sozlamalarini yarating:**
   ```bash
   cp .env.example .env
   ```

5. **`.env` faylini ochib, quyidagilarni to'ldiring:**
   ```env
   BOT_TOKEN=your_bot_token_here
   ADMIN_IDS=123456789,987654321
   DB_NAME=users.db
   ```

## 🔑 Admin ID ni topish

O'z Telegram ID ingizni bilish uchun quyidagi usullardan birini ishlating:

1. **@userinfobot** ga yozing - u sizga ID ni ko'rsatadi
2. Yoki botga `/start` yuborib, loglarda `message.from_user.id` ni ko'ring

Keyin `.env` faylida `ADMIN_IDS` ga o'z ID ingizni qo'shing:
```env
ADMIN_IDS=123456789
```

Agar bir nechta admin bo'lsa, vergul bilan ajrating:
```env
ADMIN_IDS=123456789,987654321,111222333
```

## 🎮 Botni ishga tushirish

```bash
python main.py
```

## 📝 Buyruqlar

### Foydalanuvchilar uchun:

- `/start` - O'yinni boshlash. Bot sizni avtomatik ravishda bazaga saqlaydi.

### Admin uchun:

- `/alluser` - Jami foydalanuvchilar sonini ko'rsatadi
- `/alluserdocs` - Barcha foydalanuvchilar ma'lumotlarini PDF fayl sifatida yuboradi

**Eslatma:** Admin buyruqlari faqat `.env` faylida `ADMIN_IDS` ro'yxatida bo'lgan foydalanuvchilar uchun ishlaydi.

## 🎯 O'yin qoidalari

1. Bot sizga bir nechta sonlarni ko'rsatadi
2. Siz ularni to'g'ri tartibda tanlashingiz kerak
3. Har bir bosqichda sonlar soni ortadi (4, 5, 6, 7, 8)
4. Xato javob berilsa, o'yin tugaydi
5. Barcha 5 bosqichdan muvaffaqiyatli o'tsangiz, g'olib bo'lasiz!

## 💾 Ma'lumotlar bazasi

Bot SQLite ma'lumotlar bazasidan foydalanadi. `users.db` fayli avtomatik ravishda yaratiladi va quyidagi ma'lumotlarni saqlaydi:

- `user_id` - Telegram user ID
- `username` - Telegram username
- `first_name` - Ism
- `last_name` - Familiya
- `created_at` - Qo'shilgan sana va vaqt

### Bot foydalanuvchilar ma'lumotlarini qanday oladi?

Bot har bir foydalanuvchi `/start` buyrug'ini bosganda quyidagi ma'lumotlarni avtomatik ravishda to'playdi va bazaga saqlaydi:

1. **User ID** - Telegram foydalanuvchi identifikatori (unique)
2. **Username** - Telegram username (@username)
3. **First Name** - Foydalanuvchi ismi
4. **Last Name** - Foydalanuvchi familiyasi
5. **Created At** - Botga qo'shilgan sana va vaqt

Bu ma'lumotlar `message.from_user` obyektidan olinadi va SQLite bazasiga saqlanadi. Har bir foydalanuvchi faqat bir marta saqlanadi (UNIQUE constraint).



## 🛠️ Texnik ma'lumotlar

- **Framework:** aiogram 3.x
- **Ma'lumotlar bazasi:** SQLite (aiosqlite)
- **PDF yaratish:** reportlab
- **FSM:** aiogram FSM
- **Environment:** python-dotenv

## 📁 Fayl struktura

```
game/
├── main.py          # Asosiy bot kodi
├── database.py      # Ma'lumotlar bazasi funksiyalari
├── admin.py         # Admin buyruqlari va funksiyalari
├── .env             # Environment sozlamalari (yaratish kerak)
├── .env.example     # Environment sozlamalari namunasi
├── users.db         # SQLite ma'lumotlar bazasi (avtomatik yaratiladi)
├── venv/            # Virtual environment
├── .gitignore       # Git ignore fayli
└── README.md        # Bu fayl
```

## ⚠️ Xavfsizlik

- `.env` faylini hech qachon public repository ga qo'ymang
- `.env` fayl `.gitignore` da bo'lishi kerak
- Bot tokenini faqat `.env` faylida saqlang
- `ADMIN_IDS` ro'yxatini to'g'ri sozlang
- `users.db` faylini `.gitignore` ga qo'shing

## 🐛 Muammolarni hal qilish

**Bot ishlamayapti:**
- `.env` fayl mavjudligini va to'g'ri sozlanganligini tekshiring
- Token to'g'ri ekanligini tekshiring
- Barcha paketlar o'rnatilganligini tekshiring: `pip list`

**Admin buyruqlari ishlamayapti:**
- `.env` faylda `ADMIN_IDS` ga o'z ID ingizni qo'shganingizni tekshiring
- ID to'g'ri formatda ekanligini tekshiring (vergul bilan ajratilgan)
- Botni qayta ishga tushiring



**Ma'lumotlar bazasi ishlamayapti:**
- `aiosqlite` paketi o'rnatilganligini tekshiring
- `users.db` fayl yaratilganligini tekshiring
- Loglarni ko'rib chiqing

## 📞 Yordam

Agar muammo bo'lsa, loglarni tekshiring:
```bash
python main.py
```

## 📝 Litsenziya

Bu loyiha shaxsiy foydalanish uchun yaratilgan.

---

**Yaratilgan:** 2024
**Versiya:** 2.0
