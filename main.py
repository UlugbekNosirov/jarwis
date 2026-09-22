import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatAction
from google import genai
from google.genai import types as genai_types

# Sozlamalar va o'zgaruvchilarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
OWNER_ID = os.getenv("OWNER_ID")

if not BOT_TOKEN or not GEMINI_KEY:
    raise ValueError("Telegram Bot Token yoki Gemini API Key topilmadi! .env faylni tekshiring.")

# Gemini mijozini yaratish
client = genai.Client(api_key=GEMINI_KEY)

# Jarvis xarakteri uchun tizim yo'riqnomasi (System Instruction)
SYSTEM_INSTRUCTION = """
Siz foydalanuvchining shaxsiy yordamchisi "Jarvis"siz.
Vazifangiz:
- Foydalanuvchiga har doim xushmuomala, sadoqatli, intellektual va biroz Iron Man'dagi Jarvis ohangida javob berish.
- Murojaat qilganda 'Janob' yoki foydalanuvchi ismi bilan murojaat qiling.
- Javoblarni aniq, qisqa va tushunarli qilib taqdim eting.
- Foydalanuvchining shaxsiy topshiriqlarida ko'maklashing.
"""

# Foydalanuvchilarning chat sessiyalarini xotirada saqlash
# chat_id -> gemini_chat_session
chat_sessions = {}

# Bot va Dispatcher yaratish
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

def get_or_create_chat(chat_id: int):
    """Har bir foydalanuvchi uchun alohida kontekstli sessiya yaratish"""
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
    return chat_sessions[chat_id]

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    # Faqat bot egasiga javob berish tekshiruvi (agar OWNER_ID kiritilgan bo'lsa)
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        await message.answer("Kechirasiz, men faqat o'z egamga xizmat qiladigan shaxsiy yordamchiman.")
        return

    chat_sessions[message.chat.id] = client.chats.create(
        model="gemini-2.5-flash",
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )
    )
    user_name = message.from_user.first_name
    await message.answer(f"Xush ko'rdik, janob {user_name}. Men Jarvisman. Sizga qanday yordam bera olaman?")

@dp.message()
async def message_handler(message: types.Message):
    # Faqat bot egasiga javob berish
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        return

    # Foydalanuvchi yozyapti degan animatsiyani chiqarish
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    chat = get_or_create_chat(message.chat.id)

    try:
        # Xabarni Gemini'ga yuborish
        response = await asyncio.to_thread(chat.send_message, message.text)
        await message.answer(response.text)
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await message.answer("Kechirasiz, janob. So'rovingizni qayta ishlashda kutilmagan texnik nosozlik yuz berdi.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Jarvis ishga tushdi va buyruqlaringizni kutmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())