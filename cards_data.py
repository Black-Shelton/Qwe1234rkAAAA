# ============ ОБЫЧНЫЕ КАРТЫ ============
CARDS = [
    {"name": "noob",                          "file": "noob.png",                          "rarity": "Обычная",     "chance": 29.9895, "sell": 5,     "power": 1,    "income": 0},
    {"name": "sword noob",                    "file": "sword_noob.png",                    "rarity": "Обычная",     "chance": 29.9895, "sell": 5,     "power": 2,    "income": 0},
    {"name": "big noob",                      "file": "big_noob.png",                      "rarity": "Редкая",      "chance": 28,      "sell": 10,    "power": 10,   "income": 0},
    {"name": "guest",                         "file": "guest.png",                         "rarity": "Редкая",      "chance": 10,      "sell": 10,    "power": 15,   "income": 0},
    {"name": "Grappler Noob",                 "file": "Grappler_Noob.png",                 "rarity": "Эпическая",   "chance": 0.5,     "sell": 200,   "power": 80,   "income": 0},
    {"name": "Dummy",                         "file": "Dummy.png",                         "rarity": "Эпическая",   "chance": 0.5,     "sell": 220,   "power": 90,   "income": 0},
    {"name": "titan noob",                    "file": "titan_noob.png",                    "rarity": "Мифическая",  "chance": 0.4,     "sell": 100,   "power": 50,   "income": 0},
    {"name": "titan guest",                   "file": "titan_guest.png",                   "rarity": "Мифическая",  "chance": 0.4,     "sell": 100,   "power": 200,  "income": 0},
    {"name": "Noob Mech",                     "file": "Noob_Mech.png",                     "rarity": "Легендарная", "chance": 1,       "sell": 1200,  "power": 350,  "income": 0},
    {"name": "Medic And Scout",               "file": "Medic_And_Scout.png",               "rarity": "Мифическая",  "chance": 0.1,     "sell": 2000,  "power": 200,  "income": 0},
    {"name": "The Last Guest",                "file": "The_Last_Guest.png",                "rarity": "Мифическая",  "chance": 0.1,     "sell": 2500,  "power": 200,  "income": 0},
    {"name": "Flippidee",                     "file": "Flippidee.png",                     "rarity": "Секретная",   "chance": 0.01,    "sell": 5000,  "power": 260,  "income": 0},
    {"name": "Grim",                          "file": "Grim_Ronin.png",                    "rarity": "Секретная",   "chance": 0,       "sell": 8000,  "power": 300,  "income": 0},
    {"name": "Multiverse Upgrade Titan Noob", "file": "Titan_Noob_Multiverse.png",         "rarity": "Секретная",   "chance": 0.001,   "sell": 500,   "power": 550,  "income": 0},
]


# ============ ФУНКЦИЯ ПОИСКА ============
def find_card_by_name(name: str):
    """Ищет карту по точному названию (используется в админке для выдачи)"""
    for c in CARDS:
        if c["name"].lower() == name.lower():
            return c
    return None
