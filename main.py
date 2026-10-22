import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

from database.db import init_db, register_or_update_user
from services.tax_engine import compare_all_regimes, calculate_yatt, calculate_self_employed

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set. Create a .env file with BOT_TOKEN=<your token>.")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    register_or_update_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "🤖 **2026-yilgi O'zbekiston Soliq Maslahatchisi Botiga xush kelibsiz.**\n\n"
        "Hisob-kitob qilish uchun daromadingizni yuboring yoki quyidagi buyruqlardan foydalaning:\n"
        "👉 Masalan, yillik tushumni hisoblash uchun raqam yozing (masalan: `300000000` yoki `500 mln`)."
    )

@dp.message(lambda msg: msg.text and msg.text.replace(" ", "").replace("_", "").isdigit())
async def handle_revenue_calc(message: types.Message):
    try:
        revenue = float(message.text.replace(" ", "").replace("_", ""))
        cmp = compare_all_regimes(annual_revenue=revenue)
        best = cmp["best_option"]

        text = (
            f"📊 **Yillik tushum: {revenue:,.0f} so'm**\n\n"
            f"✅ **Eng maqbul rejim:** {best.category}\n"
            f"🔹 Jami soliq yuki: **{best.total_tax_burden:,.0f} so'm**\n"
            f"🔹 Samaradorlik darajasi: **{best.effective_rate_percent:.2f}%**\n\n"
            f"📌 **Tavsiyalar:**\n" + "\n".join([f"• {r}" for r in best.recommendations]) + "\n\n"
            f"⚖️ **Qonuniy asos:**\n" + "\n".join([f"• {n}" for n in best.legal_notes])
        )
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Hisoblashda xatolik yuz berdi: {str(e)}")

async def main():
    # Bazani ishga tushirish
    init_db()
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())