import aiosqlite

DB_PATH = "game.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                last_card_time REAL DEFAULT 0,
                last_bonus_time REAL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                card_name TEXT,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, card_name)
            )
        """)
        await db.commit()

async def get_player(user_id, username=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO players (user_id, username) VALUES (?, ?)", (user_id, username or ""))
                await db.commit()
                async with db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cur2:
                    return dict(await cur2.fetchone())
            return dict(row)

async def update_username(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE players SET username = ? WHERE user_id = ?", (username or "", user_id))
        await db.commit()

async def find_player_by_username(username):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM players WHERE LOWER(username) = LOWER(?)", (username,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def add_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE players SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def set_last_card_time(user_id, timestamp):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE players SET last_card_time = ? WHERE user_id = ?", (timestamp, user_id))
        await db.commit()

async def set_last_bonus_time(user_id, timestamp):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE players SET last_bonus_time = ? WHERE user_id = ?", (timestamp, user_id))
        await db.commit()

async def reset_player(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE players SET balance = 0, last_card_time = 0, last_bonus_time = 0 WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
        await db.commit()

async def add_to_inventory(user_id, card_name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT count FROM inventory WHERE user_id = ? AND card_name = ?", (user_id, card_name)) as cur:
            row = await cur.fetchone()
        if row:
            await db.execute("UPDATE inventory SET count = count + 1 WHERE user_id = ? AND card_name = ?", (user_id, card_name))
            await db.commit()
            return False
        else:
            await db.execute("INSERT INTO inventory (user_id, card_name, count) VALUES (?, ?, 1)", (user_id, card_name))
            await db.commit()
            return True

async def get_card_count(user_id, card_name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT count FROM inventory WHERE user_id = ? AND card_name = ?", (user_id, card_name)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def remove_from_inventory(user_id, card_name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT count FROM inventory WHERE user_id = ? AND card_name = ?", (user_id, card_name)) as cur:
            row = await cur.fetchone()
        if not row: return
        if row[0] > 1:
            await db.execute("UPDATE inventory SET count = count - 1 WHERE user_id = ? AND card_name = ?", (user_id, card_name))
        else:
            await db.execute("DELETE FROM inventory WHERE user_id = ? AND card_name = ?", (user_id, card_name))
        await db.commit()