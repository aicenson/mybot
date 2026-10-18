import asyncio
import hashlib
import ssl
from aiohttp import web
import socket
from datetime import datetime
import aiohttp
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

BOT_TOKEN = "8720644170:AAGekHPsZvTvXaKiibfDEuMPQ1vqF9vwMJQ"

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я бот проверки.\n\n/pass <пароль>\n/nick <ник>\n/ssl <домен>")

@router.message(Command("pass"))
async def check_pass(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.answer("Использование: /pass пароль")
    password = parts[1].strip()
    try: await message.delete()
    except: pass
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.pwnedpasswords.com/range/{prefix}") as resp:
            text = await resp.text()
    count = 0
    for line in text.splitlines():
        p = line.split(":")
        if len(p) == 2 and p[0] == suffix: count = int(p[1]); break
    if count: await message.answer(f"⚠️ Пароль найден в утечках {count} раз. Смени его.")
    else: await message.answer("✅ Пароль чист.")

@router.message(Command("nick"))
async def check_nick(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.answer("Использование: /nick ник")
    nick = parts[1].strip()
    platforms = {"GitHub": f"https://github.com/{nick}", "Instagram": f"https://instagram.com/{nick}", "TikTok": f"https://tiktok.com/@{nick}", "Twitch": f"https://twitch.tv/{nick}", "Steam": f"https://steamcommunity.com/id/{nick}"}
    found = []
    async with aiohttp.ClientSession() as session:
        for name, url in platforms.items():
            try:
                async with session.get(url, allow_redirects=True, timeout=10) as resp:
                    if resp.status == 200: found.append(f"• {name}: {url}")
            except: continue
    await message.answer("Найдено:\n" + "\n".join(found) if found else "Ничего не найдено.")

@router.message(Command("ssl"))
async def check_ssl(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.answer("Использование: /ssl domain.com")
    domain = parts[1].strip().replace("https://", "").replace("http://", "").strip("/")
    def _check():
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock: cert = ssock.getpeercert()
        expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return (expiry - datetime.now()).days
    try:
        days = await asyncio.to_thread(_check)
        await message.answer(f"✅ SSL действителен. Осталось дней: {days}")
    except Exception as e: await message.answer(f"Ошибка: {e}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
