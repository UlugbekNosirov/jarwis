import os
import asyncio
import logging
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatAction
from google import genai
from google.genai import types as genai_types

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
OWNER_ID = os.getenv("OWNER_ID")

client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
Siz foydalanuvchining shaxsiy aqlli yordamchisi "Jarvis"siz.
Vazifangiz: sadoqatli, xushmuomala va aniq yordam berish. Murojaat: 'Janob'.
"""

chat_sessions = {}
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

def get_or_create_chat(chat_id: int):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = client.chats.create(
            model="gemini-1.5-flash",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
    return chat_sessions[chat_id]

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        return
    await message.answer(f"Xush ko'rdik, janob {message.from_user.first_name}. Men Jarvisman.")

@dp.message()
async def message_handler(message: types.Message):
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    chat = get_or_create_chat(message.chat.id)

    try:
        response = await asyncio.to_thread(chat.send_message, message.text)
        await message.answer(response.text)
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer(f"Texnik nosozlik yuz berdi: {e}")

# Render tiriklik signali (Health Check)
async def handle_ping(request):
    return web.Response(text="Jarvis is alive and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Veb-server {port}-portda faol.")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # 1. Veb serverni alohida fon vazifasi sifatida yoqish
    await start_web_server()
    
    # 2. Webhook tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Pollingni boshlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")