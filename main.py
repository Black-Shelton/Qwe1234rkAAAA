import asyncio
import os
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
from aiohttp import web

import database as db
from config import BOT_TOKEN, ADMIN_IDS
from cards_data import CARDS, find_card_by_name
from images_data import ensure_images

COOLDOWN = 3600        # КД призыва (1 час)
BONUS_COOLDOWN = 86400  # КД бонуса (24 часа)


def is_admin(user_id):
    return user_id in ADMIN_IDS


def register_menu_handlers(dp):

    # ПРИЗЫВ (Открытие карты)
    @dp.message(
        F.text.lower() == "призыв",
        F.forward_from.is_(None),
        F.forward_from_chat.is_(None),
    )
    async def trigger_card(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        player = await db.get_player(user_id, username)
        await db.update_username(user_id, username)

        now = time.time()
        if now - player["last_card_time"] < COOLDOWN:
            rem = int(COOLDOWN - (now - player["last_card_time"]))
            await message.reply(f"⏳ Подожди {rem // 60}м {rem % 60}с")
            return

        total_chance = sum(c["chance"] for c in CARDS)
        roll = random.uniform(0, total_chance)
        current = 0
        card = CARDS[-1]
        for c in CARDS:
            current += c["chance"]
            if roll <= current:
                card = c
                break

        is_new = await db.add_to_inventory(user_id, card["name"])
        total_count = await db.get_card_count(user_id, card["name"])
        await db.set_last_card_time(user_id, now)

        status = "🆕 Новая карта!" if is_new else "♻️ Дубликат"

        caption = (
            f"{status}\n\n"
            f"🎴 Карта: <b>{card['name']}</b>\n"
            f"У тебя: <b>×{total_count}</b>"
        )

        media_path = os.path.join("images", card.get("file", ""))
        if os.path.exists(media_path):
            await message.reply_photo(photo=FSInputFile(media_path), caption=caption, parse_mode="HTML")
        else:
            await message.reply(caption, parse_mode="HTML")

    # БОНУС
    @dp.message(F.text.lower() == "бонус")
    async def cmd_bonus(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        player = await db.get_player(user_id, username)
        await db.update_username(user_id, username)

        now = time.time()
        if now - player["last_bonus_time"] < BONUS_COOLDOWN:
            rem = int(BONUS_COOLDOWN - (now - player["last_bonus_time"]))
            await message.reply(f"⏳ Бонус будет доступен через {rem // 3600}ч {(rem % 3600) // 60}м")
            return

        coins = random.randint(100, 500)
        await db.add_balance(user_id, coins)
        await db.set_last_bonus_time(user_id, now)

        new_bal = player["balance"] + coins
        await message.reply(f"🎁 <b>Бонус!</b>\n\n+{coins} 🪙\nБаланс: <b>{new_bal}</b> 🪙", parse_mode="HTML")

    # ПРОФИЛЬ (чтобы смотреть баланс)
    @dp.message(F.text.lower() == "профиль")
    async def cmd_profile(message: types.Message):
        player = await db.get_player(message.from_user.id, message.from_user.username)
        await message.answer(f"👤 <b>Профиль</b>\n\nМонеты: <b>{player['balance']}</b> 🪙", parse_mode="HTML")


def register_admin_handlers(dp):

    @dp.message(F.text.lower().startswith("вд монеты"))
    async def give_coins(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.text.split()

        if message.reply_to_message:
            if len(parts) != 3:
                return await message.reply("❌ вд монеты 100 (ответом)")
            amount = int(parts[2])
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            await db.get_player(target_id, message.reply_to_message.from_user.username)
        else:
            if len(parts) != 4 or not parts[2].startswith("@"):
                return await message.reply("❌ вд монеты @user 100")
            amount = int(parts[3])
            target = await db.find_player_by_username(parts[2][1:])
            if not target:
                return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]

        await db.add_balance(target_id, amount)
        await message.reply(f"✅ Выдано <b>{amount}</b> 🪙 игроку <b>{target_name}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("вд карту"))
    async def give_card(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        rest = message.text[len("вд карту"):].strip()

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            await db.get_player(target_id, message.reply_to_message.from_user.username)
            card_name = rest.strip('"').strip("'")
        else:
            parts = rest.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].startswith("@"):
                return await message.reply("❌ вд карту @user \"название\"")
            target = await db.find_player_by_username(parts[0][1:])
            if not target:
                return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            card_name = parts[1].strip('"').strip("'")

        card = find_card_by_name(card_name)
        if not card:
            return await message.reply(f"❌ Карта «{card_name}» не найдена")

        await db.add_to_inventory(target_id, card["name"])
        total = await db.get_card_count(target_id, card["name"])
        await message.reply(f"✅ Выдана <b>{card['name']}</b> игроку <b>{target_name}</b>\nУ него: <b>×{total}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("забрать карту"))
    async def take_card(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        rest = message.text[len("забрать карту"):].strip()

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            card_name = rest.strip('"').strip("'")
        else:
            parts = rest.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].startswith("@"):
                return await message.reply("❌ забрать карту @user \"название\"")
            target = await db.find_player_by_username(parts[0][1:])
            if not target:
                return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]
            card_name = parts[1].strip('"').strip("'")

        count = await db.get_card_count(target_id, card_name)
        if count <= 0:
            return await message.reply(f"❌ У игрока нет карты «{card_name}»")

        await db.remove_from_inventory(target_id, card_name)
        new_count = await db.get_card_count(target_id, card_name)
        await message.reply(f"✅ Забрана <b>{card_name}</b> у <b>{target_name}</b>\nОсталось: <b>×{new_count}</b>", parse_mode="HTML")

    @dp.message(F.text.lower().startswith("обнуление"))
    async def reset_user(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        parts = message.text.split()

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            if len(parts) != 2 or not parts[1].startswith("@"):
                return await message.reply("❌ обнуление @user")
            target = await db.find_player_by_username(parts[1][1:])
            if not target:
                return await message.reply("❌ Игрок не найден")
            target_id, target_name = target["user_id"], target["username"]

        await db.reset_player(target_id)
        await message.reply(f"✅ Игрок <b>{target_name}</b> обнулён", parse_mode="HTML")


async def _run_health_server():
    # Render Web Service требует открытый порт, иначе считает деплой неудачным.
    app = web.Application()
    app.router.add_get("/", lambda request: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server слушает порт {port}")


async def main():
    ensure_images()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_menu_handlers(dp)
    register_admin_handlers(dp)

    await db.init_db()

    print("Бот запущен...")
    if ADMIN_IDS:
        print(f"Админы: {ADMIN_IDS}")
    else:
        print("⚠️ ADMIN_IDS не задан")

    await _run_health_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
