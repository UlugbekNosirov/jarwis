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
Siz foydalanuvchining shaxsiy yordamchisi "Jarvis"siz.
Vazifangiz: foydalanuvchiga sadoqatli, xushmuomala va aniq yordam berish.
"""

chat_sessions = {}
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

def get_or_create_chat(chat_id: int):
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
    if OWNER_ID and str(message.from_user.id) != OWNER_ID:
        return
    await message.answer("Salom, janob! Men Jarvisman.")

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
        logging.error(f"Xato: {e}")
        await message.answer("Xatolik yuz berdi, janob.")

# Render bepul Web Service talab qiladigan soxta veb-sahifa
async def handle_ping(request):
    return web.Response(text="Jarvis is running 24/7!")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Kichik veb-serverni ishga tushirish (Render talabi)
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())