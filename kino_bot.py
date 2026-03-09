import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

API_TOKEN = "7671140484:AAH3zhysqwsnUpur5os-AFfLoZE7uOZMv-k"
ADMIN_ID = 629917863
DATABASE = "movies.db"
LANGUAGES = {'uz': 'O\'zbek', 'ru': 'Русский', 'en': 'English'}
CATEGORIES = ['Filmlar', 'Seriallar', 'Multfilmlar']

TEXTS = {
    'uz': {
        'start': 'Assalomu alaykum\n\nBizning 《 📽 @TVKINOLARUZ_BOT 》 botimizga xush kelibsiz.\n\n/top - 🏆 Top kinolar\n/last - 🎥 Oxirgi yuklanganlar\n/search - 🔍 Qidirish\n/favorites - ⭐ Sevimlilar\n/profile - 👤 Profil\n/help - ☔️ Qollap quvvatlash\n\n🎞 Kino kodi yuboring:',
        'subscribe': 'Kechirasiz, botimizdan foydalanish uchun ushbu kanallarga obuna bo\'lishingiz kerak.',
        'admin': '⚙️ ADMIN PANEL',
        'help': '☔️ Qollap quvvatlash:\n\n@bek_922',
        'profile': 'PROFIL',
        'lang_info': '🌍 TIL TANLASH',
        'night_info': '🌙 TUN REJIMI - Qorong\'u rang (Tungi foydalanish uchun)',
        'notify_info': '🔔 ESLATMA - Yangi kinolar qo\'shilganda xabar olish',
        'language': 'Til',
        'night_mode': 'Tun rejimi',
        'notification': 'Eslatma',
        'back': 'Orqaga',
        'turn_on': 'Yoqish',
        'turn_off': 'Ochirish',
        'on': 'YONIQ',
        'off': 'O\'CHIQ',
        'categories': 'Kategoriyalar',
        'share': 'Ulashish',
        'bad_link': '❌ Ssilka noto\'g\'ri!',
        'obuna': 'Obuna bo\'lish',
    },
    'ru': {
        'start': 'Добро пожаловать\n\nВ наш бот 《 📽 @TVKINOLARUZ_BOT 》.\n\n/top - 🏆 Топ\n/last - 🎥 Последние\n/search - 🔍 Поиск\n/favorites - ⭐ Избранное\n/profile - 👤 Профиль\n/help - ☔️ Помощь\n\n🎞 Введите код:',
        'subscribe': 'Подпишитесь на каналы.',
        'admin': '⚙️ ADMIN PANEL',
        'help': '☔️ Помощь:\n\n@bek_922',
        'profile': 'ПРОФИЛЬ',
        'lang_info': '🌍 ЯЗЫК',
        'night_info': '🌙 НОЧНОЙ РЕЖИМ - Темный цвет (для ночного использования)',
        'notify_info': '🔔 УВЕДОМЛЕНИЕ - Получать уведомления о новых фильмах',
        'language': 'Язык',
        'night_mode': 'Ночной режим',
        'notification': 'Уведомление',
        'back': 'Назад',
        'turn_on': 'Включить',
        'turn_off': 'Отключить',
        'on': 'ВКЛЮЧЕНО',
        'off': 'ОТКЛЮЧЕНО',
        'categories': 'Категории',
        'share': 'Поделиться',
        'bad_link': '❌ Ссылка неверна!',
        'obuna': 'Подписаться',
    },
    'en': {
        'start': 'Welcome\n\nTo our bot 《 📽 @TVKINOLARUZ_BOT 》.\n\n/top - 🏆 Top\n/last - 🎥 Latest\n/search - 🔍 Search\n/favorites - ⭐ Favorites\n/profile - 👤 Profile\n/help - ☔️ Help\n\n🎞 Enter code:',
        'subscribe': 'Subscribe to channels.',
        'admin': '⚙️ ADMIN PANEL',
        'help': '☔️ Help:\n\n@bek_922',
        'profile': 'PROFILE',
        'lang_info': '🌍 LANGUAGE',
        'night_info': '🌙 NIGHT MODE - Dark color (for nighttime use)',
        'notify_info': '🔔 NOTIFICATION - Get updates about new movies',
        'language': 'Language',
        'night_mode': 'Night mode',
        'notification': 'Notification',
        'back': 'Back',
        'turn_on': 'Turn on',
        'turn_off': 'Turn off',
        'on': 'ON',
        'off': 'OFF',
        'categories': 'Categories',
        'share': 'Share',
        'bad_link': '❌ Bad link!',
        'obuna': 'Subscribe',
    }
}

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL, title TEXT, desc TEXT, video_id TEXT, part INTEGER DEFAULT 1, views INTEGER DEFAULT 0, category TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, language TEXT DEFAULT "uz", night_mode INTEGER DEFAULT 0, notifications INTEGER DEFAULT 1, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, active INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER, code TEXT, PRIMARY KEY(user_id, code))')
    c.execute("INSERT OR IGNORE INTO channels (name, active) VALUES ('@andijonbozor4', 1)")
    c.execute("INSERT OR IGNORE INTO channels (name, active) VALUES ('@andijon_taziya', 1)")
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect(DATABASE)
    channels = [row[0] for row in conn.execute('SELECT name FROM channels WHERE active = 1 ORDER BY id').fetchall()]
    conn.close()
    return channels

def get_user_language(user_id):
    conn = sqlite3.connect(DATABASE)
    lang = conn.execute('SELECT language FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return lang[0] if lang else 'uz'

def normalize_channel(channel):
    channel = channel.strip()
    if channel.startswith('https://t.me/'):
        return '@' + channel.replace('https://t.me/', '')
    elif channel.startswith('http://t.me/'):
        return '@' + channel.replace('http://t.me/', '')
    elif not channel.startswith('@'):
        return '@' + channel
    return channel

async def is_subscribed(context, user_id):
    channels = get_channels()
    if not channels:
        return True
    
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            
            if member.status in ['member', 'administrator', 'creator']:
                continue
            
            if member.status == 'restricted':
                return True
            
            return False
            
        except:
            return True
    
    return True

async def get_unsubscribed_channels(context, user_id):
    channels = get_channels()
    unsubscribed = []
    
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            
            if member.status in ['member', 'administrator', 'creator']:
                continue
            
            if member.status == 'restricted':
                continue
            
            unsubscribed.append(ch)
            
        except:
            unsubscribed.append(ch)
    
    return unsubscribed

async def is_private(update):
    return update.message.chat.id == update.effective_user.id

async def start(update, context):
    if not await is_private(update):
        return
    
    user_id = update.effective_user.id
    conn = sqlite3.connect(DATABASE)
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, ?, "uz", 0, 1, CURRENT_TIMESTAMP)', (user_id, update.effective_user.username or 'user'))
    conn.commit()
    conn.close()
    
    is_sub = await is_subscribed(context, user_id)
    lang = get_user_language(user_id)
    
    if is_sub:
        await update.message.reply_text(TEXTS[lang]['start'])
    else:
        unsubscribed = await get_unsubscribed_channels(context, user_id)
        msg = TEXTS[lang]['subscribe']
        
        kb = []
        for ch in unsubscribed:
            kb.append([InlineKeyboardButton(f"➕ {TEXTS[lang]['obuna']}", url=f"https://t.me/{ch.replace('@', '')}")])
        
        kb.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def callback(update, context):
    data = update.callback_query.data
    user_id = update.callback_query.from_user.id
    lang = get_user_language(user_id)
    
    await update.callback_query.answer()
    
    if data == "check_sub":
        is_sub = await is_subscribed(context, user_id)
        
        if is_sub:
            await update.callback_query.edit_message_text(TEXTS[lang]['start'])
        else:
            unsubscribed = await get_unsubscribed_channels(context, user_id)
            
            if unsubscribed:
                msg = TEXTS[lang]['subscribe']
                
                kb = []
                for ch in unsubscribed:
                    kb.append([InlineKeyboardButton(f"➕ {TEXTS[lang]['obuna']}", url=f"https://t.me/{ch.replace('@', '')}")])
                
                kb.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
                await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            else:
                await update.callback_query.edit_message_text(TEXTS[lang]['start'])
    
    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await update.callback_query.answer("Admin emas!", show_alert=True)
            return
        
        kb = [
            [InlineKeyboardButton("➕ Kino qoshish", callback_data="add_movie")],
            [InlineKeyboardButton("✏️ Kino tahrirlash", callback_data="edit_movie")],
            [InlineKeyboardButton("🗑️ Kino ochirib tashlash", callback_data="delete_movie_menu")],
            [InlineKeyboardButton("📺 Kanallarni tahrirlash", callback_data="manage_channels")],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 Xabar yuborish", callback_data="send_message")],
        ]
        await update.callback_query.edit_message_text(TEXTS[lang]['admin'], reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "add_movie":
        if user_id != ADMIN_ID:
            return
        await update.callback_query.edit_message_text("📝 Kino kodini kiriting:")
        context.user_data['step'] = 'code'
    
    elif data == "edit_movie":
        if user_id != ADMIN_ID:
            return
        await update.callback_query.edit_message_text("✏️ Tahrirlash uchun kino kodini kiriting:")
        context.user_data['step'] = 'edit_code'
    
    elif data == "delete_movie_menu":
        if user_id != ADMIN_ID:
            return
        await update.callback_query.edit_message_text("🗑️ O'chirish uchun kino kodini kiriting:")
        context.user_data['step'] = 'delete_code'
    
    elif data == "manage_channels":
        if user_id != ADMIN_ID:
            return
        conn = sqlite3.connect(DATABASE)
        channels = conn.execute('SELECT name FROM channels ORDER BY id').fetchall()
        conn.close()
        msg = "📺 KANALLAR:\n\n"
        for ch in channels:
            msg += f"{ch[0]}\n"
        kb = [
            [InlineKeyboardButton("➕ Kanal qoshish", callback_data="add_channel")],
            [InlineKeyboardButton("🗑️ O'chirish", callback_data="delete_channel")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]
        ]
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "add_channel":
        if user_id != ADMIN_ID:
            return
        await update.callback_query.edit_message_text("Kanal nomini kiriting (@username):")
        context.user_data['step'] = 'add_channel'
    
    elif data == "delete_channel":
        if user_id != ADMIN_ID:
            return
        conn = sqlite3.connect(DATABASE)
        channels = conn.execute('SELECT name FROM channels WHERE active = 1 ORDER BY id').fetchall()
        conn.close()
        
        if not channels:
            await update.callback_query.edit_message_text("❌ Kanal yo'q!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="manage_channels")]]))
            return
        
        kb = []
        for ch in channels:
            kb.append([InlineKeyboardButton(f"🗑️ {ch[0]}", callback_data=f"del_{ch[0]}")])
        kb.append([InlineKeyboardButton("🗑️ BARCHASINI O'CHIRISH", callback_data="del_all")])
        kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="manage_channels")])
        await update.callback_query.edit_message_text("Qaysi kanalni ochirib tashlash?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "del_all":
        if user_id != ADMIN_ID:
            return
        conn = sqlite3.connect(DATABASE)
        conn.execute('DELETE FROM channels')
        conn.commit()
        conn.close()
        kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="manage_channels")]]
        await update.callback_query.edit_message_text(f"✅ BARCHA KANALLAR O'CHIRILDI!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("del_"):
        if user_id != ADMIN_ID:
            return
        ch = data.replace("del_", "")
        try:
            conn = sqlite3.connect(DATABASE)
            conn.execute('DELETE FROM channels WHERE name = ?', (ch,))
            conn.commit()
            conn.close()
            kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="manage_channels")]]
            await update.callback_query.edit_message_text(f"✅ {ch} o'chirildi!", reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            await update.callback_query.edit_message_text(f"❌ Xato: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="manage_channels")]]))
    
    elif data == "admin_stats":
        if user_id != ADMIN_ID:
            return
        conn = sqlite3.connect(DATABASE)
        movies_count = conn.execute('SELECT COUNT(DISTINCT code) FROM movies').fetchone()[0]
        users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_views = conn.execute('SELECT SUM(views) FROM movies').fetchone()[0] or 0
        
        msg = f"📊 STATISTIKA:\n\n👥 Obunachilar: {users_count}\n🎬 Kinolar: {movies_count}\n👁️ Korildi: {total_views}\n\n"
        
        for cat in CATEGORIES:
            cat_count = conn.execute('SELECT COUNT(DISTINCT code) FROM movies WHERE category = ?', (cat,)).fetchone()[0]
            cat_views = conn.execute('SELECT SUM(views) FROM movies WHERE category = ?', (cat,)).fetchone()[0] or 0
            msg += f"{cat}: {cat_count} (👁️ {cat_views})\n"
        
        conn.close()
        kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]]
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "send_message":
        if user_id != ADMIN_ID:
            return
        await update.callback_query.edit_message_text("📢 Xabar yozing:")
        context.user_data['step'] = 'admin_message'
    
    elif data.startswith("add_fav_"):
        code = data.replace("add_fav_", "")
        conn = sqlite3.connect(DATABASE)
        try:
            conn.execute('INSERT INTO favorites VALUES (?, ?)', (user_id, code))
            conn.commit()
            await update.callback_query.answer("✅ Sevimlilar'ga qo'shildi!", show_alert=True)
        except:
            await update.callback_query.answer("Allaqachon mavjud!", show_alert=True)
        finally:
            conn.close()
    
    elif data == "cat_all":
        await update.callback_query.edit_message_text("🎬 KATEGORIYALAR:\n\nTanlang:", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Filmlar", callback_data="cat_Filmlar")],
                [InlineKeyboardButton("📺 Seriallar", callback_data="cat_Seriallar")],
                [InlineKeyboardButton("🎨 Multfilmlar", callback_data="cat_Multfilmlar")],
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="profile_back")]
            ]))
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        conn = sqlite3.connect(DATABASE)
        movies = conn.execute('SELECT code, title FROM movies WHERE category = ? GROUP BY code', (category,)).fetchall()
        conn.close()
        msg = f"🎬 {category}:\n\n"
        for code, title in movies:
            msg += f"#{code}: {title}\n"
        kb = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="cat_all")]]
        await update.callback_query.edit_message_text(msg if movies else "Kino yo'q", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "set_lang":
        kb = [[InlineKeyboardButton(f"O'zbek", callback_data="lang_uz"), InlineKeyboardButton(f"Русский", callback_data="lang_ru"), InlineKeyboardButton(f"English", callback_data="lang_en")]]
        kb.append([InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")])
        await update.callback_query.edit_message_text(TEXTS[lang]['lang_info'], reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("lang_"):
        lang_new = data.replace("lang_", "")
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang_new, user_id))
        conn.commit()
        conn.close()
        lang = lang_new
        await update.callback_query.answer(f"✅ Til o'zgartirildi!", show_alert=True)
        
        conn = sqlite3.connect(DATABASE)
        user = conn.execute('SELECT language, night_mode, notifications FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        language = {'uz': 'O\'zbek', 'ru': 'Русский', 'en': 'English'}[user[0]]
        night = TEXTS[lang]['on'] if user[1] else TEXTS[lang]['off']
        notify = TEXTS[lang]['on'] if user[2] else TEXTS[lang]['off']
        
        msg = f"👤 {TEXTS[lang]['profile']}:\n\n🌍 {TEXTS[lang]['language']}: {language}\n🌙 {TEXTS[lang]['night_mode']}: {night}\n🔔 {TEXTS[lang]['notification']}: {notify}"
        
        kb = [
            [InlineKeyboardButton(f"🌍 {TEXTS[lang]['language']}", callback_data="set_lang")],
            [InlineKeyboardButton(f"🌙 {TEXTS[lang]['night_mode']}", callback_data="set_night")],
            [InlineKeyboardButton(f"🔔 {TEXTS[lang]['notification']}", callback_data="set_notify")],
            [InlineKeyboardButton(f"🎬 {TEXTS[lang]['categories']}", callback_data="cat_all")],
            [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]
        ]
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "set_night":
        conn = sqlite3.connect(DATABASE)
        status = conn.execute('SELECT night_mode FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
        conn.close()
        
        if status:
            btn_text = f"❌ {TEXTS[lang]['turn_off']}"
            btn_data = "night_off"
        else:
            btn_text = f"✅ {TEXTS[lang]['turn_on']}"
            btn_data = "night_on"
        
        kb = [[InlineKeyboardButton(btn_text, callback_data=btn_data)], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['night_info'], reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "night_on":
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET night_mode = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        kb = [[InlineKeyboardButton(f"❌ {TEXTS[lang]['turn_off']}", callback_data="night_off")], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['night_info'] + f"\n\n✅ {TEXTS[lang]['on']}!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "night_off":
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET night_mode = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        kb = [[InlineKeyboardButton(f"✅ {TEXTS[lang]['turn_on']}", callback_data="night_on")], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['night_info'] + f"\n\n❌ {TEXTS[lang]['off']}!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "set_notify":
        conn = sqlite3.connect(DATABASE)
        status = conn.execute('SELECT notifications FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
        conn.close()
        
        if status:
            btn_text = f"❌ {TEXTS[lang]['turn_off']}"
            btn_data = "notify_off"
        else:
            btn_text = f"✅ {TEXTS[lang]['turn_on']}"
            btn_data = "notify_on"
        
        kb = [[InlineKeyboardButton(btn_text, callback_data=btn_data)], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['notify_info'], reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "notify_on":
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET notifications = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        kb = [[InlineKeyboardButton(f"❌ {TEXTS[lang]['turn_off']}", callback_data="notify_off")], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['notify_info'] + f"\n\n✅ {TEXTS[lang]['on']}!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "notify_off":
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE users SET notifications = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        kb = [[InlineKeyboardButton(f"✅ {TEXTS[lang]['turn_on']}", callback_data="notify_on")], [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]]
        await update.callback_query.edit_message_text(TEXTS[lang]['notify_info'] + f"\n\n❌ {TEXTS[lang]['off']}!", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "profile_back":
        conn = sqlite3.connect(DATABASE)
        user = conn.execute('SELECT language, night_mode, notifications FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        language = {'uz': 'O\'zbek', 'ru': 'Русский', 'en': 'English'}[user[0]]
        night = TEXTS[lang]['on'] if user[1] else TEXTS[lang]['off']
        notify = TEXTS[lang]['on'] if user[2] else TEXTS[lang]['off']
        
        msg = f"👤 {TEXTS[lang]['profile']}:\n\n🌍 {TEXTS[lang]['language']}: {language}\n🌙 {TEXTS[lang]['night_mode']}: {night}\n🔔 {TEXTS[lang]['notification']}: {notify}"
        
        kb = [
            [InlineKeyboardButton(f"🌍 {TEXTS[lang]['language']}", callback_data="set_lang")],
            [InlineKeyboardButton(f"🌙 {TEXTS[lang]['night_mode']}", callback_data="set_night")],
            [InlineKeyboardButton(f"🔔 {TEXTS[lang]['notification']}", callback_data="set_notify")],
            [InlineKeyboardButton(f"🎬 {TEXTS[lang]['categories']}", callback_data="cat_all")],
            [InlineKeyboardButton(f"⬅️ {TEXTS[lang]['back']}", callback_data="profile_back")]
        ]
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def help_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    await update.message.reply_text(TEXTS[lang]['help'])

async def top_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    is_sub = await is_subscribed(context, user_id)
    if not is_sub:
        await update.message.reply_text("Kanalga azo boling")
        return
    conn = sqlite3.connect(DATABASE)
    movies = conn.execute('SELECT code, title, views FROM movies GROUP BY code ORDER BY views DESC LIMIT 10').fetchall()
    conn.close()
    msg = "🏆 TOP:\n\n"
    for code, title, views in movies:
        msg += f"#{code}: {title} (👁️ {views})\n"
    await update.message.reply_text(msg if movies else "Kino yo'q")

async def last_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    is_sub = await is_subscribed(context, user_id)
    if not is_sub:
        await update.message.reply_text("Kanalga azo boling")
        return
    conn = sqlite3.connect(DATABASE)
    movies = conn.execute('SELECT DISTINCT code, title FROM movies ORDER BY created_at DESC LIMIT 10').fetchall()
    conn.close()
    msg = "🎥 OXIRGI:\n\n"
    for code, title in movies:
        msg += f"#{code}: {title}\n"
    await update.message.reply_text(msg if movies else "Kino yo'q")

async def search_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    is_sub = await is_subscribed(context, user_id)
    if not is_sub:
        await update.message.reply_text("Kanalga azo boling")
        return
    await update.message.reply_text("🔍 Qidirish:")
    context.user_data['step'] = 'search'

async def favorites_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    is_sub = await is_subscribed(context, user_id)
    if not is_sub:
        await update.message.reply_text("Kanalga azo boling")
        return
    conn = sqlite3.connect(DATABASE)
    favs = conn.execute('SELECT DISTINCT m.code, m.title FROM movies m JOIN favorites f ON m.code = f.code WHERE f.user_id = ?', (user_id,)).fetchall()
    conn.close()
    msg = "⭐ SEVIMLILAR:\n\n"
    for code, title in favs:
        msg += f"#{code}: {title}\n"
    await update.message.reply_text(msg if favs else "Yo'q")

async def profile_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    conn = sqlite3.connect(DATABASE)
    user = conn.execute('SELECT language, night_mode, notifications FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    language = {'uz': 'O\'zbek', 'ru': 'Русский', 'en': 'English'}[user[0]]
    night = TEXTS[lang]['on'] if user[1] else TEXTS[lang]['off']
    notify = TEXTS[lang]['on'] if user[2] else TEXTS[lang]['off']
    msg = f"👤 {TEXTS[lang]['profile']}:\n\n🌍 {TEXTS[lang]['language']}: {language}\n🌙 {TEXTS[lang]['night_mode']}: {night}\n🔔 {TEXTS[lang]['notification']}: {notify}"
    kb = [
        [InlineKeyboardButton(f"🌍 {TEXTS[lang]['language']}", callback_data="set_lang")],
        [InlineKeyboardButton(f"🌙 {TEXTS[lang]['night_mode']}", callback_data="set_night")],
        [InlineKeyboardButton(f"🔔 {TEXTS[lang]['notification']}", callback_data="set_notify")],
        [InlineKeyboardButton(f"🎬 {TEXTS[lang]['categories']}", callback_data="cat_all")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def handle_text(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    text = update.message.text.strip()
    step = context.user_data.get('step')
    lang = get_user_language(user_id)
    
    if step == 'add_channel':
        channel = normalize_channel(text)
        if not channel.startswith('@'):
            await update.message.reply_text(TEXTS[lang]['bad_link'])
            return
        conn = sqlite3.connect(DATABASE)
        try:
            conn.execute('INSERT INTO channels (name, active) VALUES (?, 1)', (channel,))
            conn.commit()
            await update.message.reply_text(f"✅ {channel} qo'shildi!")
        except:
            await update.message.reply_text(f"❌ Mavjud!")
        finally:
            conn.close()
        context.user_data.clear()
    
    elif step == 'code':
        context.user_data['code'] = text
        context.user_data['step'] = 'title'
        await update.message.reply_text("Nomi:")
    elif step == 'title':
        context.user_data['title'] = text
        context.user_data['step'] = 'desc'
        await update.message.reply_text("Tavsif (skip):")
    elif step == 'desc':
        context.user_data['desc'] = text if text.lower() != 'skip' else ''
        context.user_data['step'] = 'category'
        msg = "Kategoriya:\n1. Filmlar\n2. Seriallar\n3. Multfilmlar"
        await update.message.reply_text(msg)
    elif step == 'category':
        try:
            cat_idx = int(text) - 1
            if 0 <= cat_idx < len(CATEGORIES):
                context.user_data['category'] = CATEGORIES[cat_idx]
                context.user_data['step'] = 'part'
                context.user_data['part_count'] = 0
                await update.message.reply_text("Video:")
            else:
                await update.message.reply_text("❌ Noto'g'ri!")
        except:
            await update.message.reply_text("❌ Raqam!")
    elif step == 'more_parts':
        if text.lower() in ['ha', 'yes', 'xa']:
            context.user_data['part_count'] += 1
            await update.message.reply_text(f"Video {context.user_data['part_count'] + 1}-qismini yuboring:")
            context.user_data['step'] = 'part'
        else:
            code = context.user_data.get('code')
            title = context.user_data.get('title')
            part_count = context.user_data.get('part_count', 0) + 1
            msg = f"✅ #{code}: {title}"
            if part_count > 1:
                msg += f" ({part_count}-qism)"
            msg += " qo'shildi!"
            await update.message.reply_text(msg)
            context.user_data.clear()
    elif step == 'edit_code':
        conn = sqlite3.connect(DATABASE)
        parts = conn.execute('SELECT id, part FROM movies WHERE code = ? ORDER BY part', (text,)).fetchall()
        conn.close()
        if not parts:
            await update.message.reply_text(f"❌ #{text} topilmadi")
            context.user_data.clear()
            return
        if len(parts) == 1:
            context.user_data['edit_id'] = parts[0][0]
            context.user_data['code'] = text
            context.user_data['step'] = 'edit_select'
            await update.message.reply_text("Tahrirlash:\n1. Nomi\n2. Tavsif\n3. Video\n\nRaqamni kiriting:")
        else:
            context.user_data['code'] = text
            msg = f"Qismni tanlang:\n\n"
            kb = []
            for part_id, part_num in parts:
                msg += f"{part_num}-qism\n"
                kb.append([InlineKeyboardButton(f"{part_num}-qism", callback_data=f"edit_part_{part_id}")])
            kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")])
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
    elif step == 'edit_select':
        try:
            opt = int(text)
            if opt == 1:
                context.user_data['step'] = 'edit_title'
                await update.message.reply_text("Yangi nomi:")
            elif opt == 2:
                context.user_data['step'] = 'edit_desc'
                await update.message.reply_text("Yangi tavsif:")
            elif opt == 3:
                context.user_data['step'] = 'edit_video'
                await update.message.reply_text("Yangi video:")
        except:
            await update.message.reply_text("❌ Raqam!")
    elif step == 'edit_title':
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE movies SET title = ? WHERE id = ?', (text, context.user_data['edit_id']))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Tahrirlandi!")
        context.user_data.clear()
    elif step == 'edit_desc':
        conn = sqlite3.connect(DATABASE)
        conn.execute('UPDATE movies SET desc = ? WHERE id = ?', (text, context.user_data['edit_id']))
        conn.commit()
        conn.close()
        await update.message.reply_text("✅ Tahrirlandi!")
        context.user_data.clear()
    elif step == 'edit_video':
        context.user_data['step'] = 'wait_video'
        await update.message.reply_text("Video kutilmoqda...")
    elif step == 'delete_code':
        conn = sqlite3.connect(DATABASE)
        parts = conn.execute('SELECT id, part, title FROM movies WHERE code = ? ORDER BY part', (text,)).fetchall()
        conn.close()
        if not parts:
            await update.message.reply_text(f"❌ #{text} topilmadi")
            context.user_data.clear()
            return
        context.user_data['delete_code'] = text
        if len(parts) == 1:
            context.user_data['delete_id'] = parts[0][0]
            await update.message.reply_text(f"O'chiriladi: {parts[0][2]}\n\nHaqiqatdan? (Ha/Yo'q)")
            context.user_data['step'] = 'confirm_delete'
        else:
            msg = "Qismni tanlang:\n\n"
            kb = []
            for part_id, part_num, title in parts:
                msg += f"{part_num}-qism\n"
                kb.append([InlineKeyboardButton(f"{part_num}-qism", callback_data=f"delete_part_{part_id}")])
            kb.append([InlineKeyboardButton("🗑️ Barchasini o'chirish", callback_data=f"delete_all_{text}")])
            kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")])
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
    elif step == 'confirm_delete':
        if text.lower() in ['ha', 'yes', 'xa']:
            conn = sqlite3.connect(DATABASE)
            conn.execute('DELETE FROM movies WHERE id = ?', (context.user_data['delete_id'],))
            conn.commit()
            conn.close()
            await update.message.reply_text("✅ O'chirildi!")
        else:
            await update.message.reply_text("Bekor qilindi")
        context.user_data.clear()
    elif step == 'search':
        query = text.lower()
        conn = sqlite3.connect(DATABASE)
        movies = conn.execute('SELECT code, title FROM movies WHERE LOWER(title) LIKE ? GROUP BY code', ('%' + query + '%',)).fetchall()
        conn.close()
        msg = f"🔍:\n\n"
        for code, title in movies:
            msg += f"#{code}: {title}\n"
        await update.message.reply_text(msg if movies else "❌")
        context.user_data.clear()
    elif step == 'admin_message':
        conn = sqlite3.connect(DATABASE)
        users = conn.execute('SELECT user_id, notifications FROM users').fetchall()
        conn.close()
        sent = 0
        for user_tuple in users:
            try:
                user_notify = user_tuple[1]
                if user_notify:
                    await context.bot.send_message(user_tuple[0], f"📢 YANGI KINO QO'SHILDI:\n\n{text}")
                    sent += 1
            except:
                pass
        await update.message.reply_text(f"✅ {sent} nafarga yuborildi!")
        context.user_data.clear()
    else:
        is_sub = await is_subscribed(context, user_id)
        if not is_sub:
            await update.message.reply_text("Kanalga azo boling")
            return
        code = text
        conn = sqlite3.connect(DATABASE)
        movies = conn.execute('SELECT id, title, desc, video_id, part FROM movies WHERE code = ? ORDER BY part', (code,)).fetchall()
        conn.close()
        if movies:
            for movie_id, title, desc, video_id, part in movies:
                caption = f"🎬 {title}"
                if len(movies) > 1:
                    caption += f"\n{part}-qism"
                if desc:
                    caption += f"\n\n{desc}"
                
                conn = sqlite3.connect(DATABASE)
                views = conn.execute('SELECT views FROM movies WHERE id = ?', (movie_id,)).fetchone()[0]
                conn.close()
                caption += f"\n\n👁️ {views} marta ko'rildi"
                
                kb = [[InlineKeyboardButton("⭐ Sevimlilar", callback_data=f"add_fav_{code}")],
                      [InlineKeyboardButton(f"📤 Ulashish", url=f"https://t.me/share/url?url=https://t.me/TVKINOLARUZ_BOT?start={code}&text={title}")]]
                
                conn = sqlite3.connect(DATABASE)
                conn.execute('UPDATE movies SET views = views + 1 WHERE id = ?', (movie_id,))
                conn.commit()
                conn.close()
                
                await update.message.reply_video(video_id, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await update.message.reply_text(f"❌")

async def handle_video(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    step = context.user_data.get('step')
    if step == 'part':
        code = context.user_data.get('code')
        title = context.user_data.get('title')
        desc = context.user_data.get('desc', '')
        category = context.user_data.get('category', 'Filmlar')
        part_count = context.user_data.get('part_count', 0)
        video_id = update.message.video.file_id
        conn = sqlite3.connect(DATABASE)
        try:
            conn.execute('INSERT INTO movies (code, title, desc, video_id, part, category, views) VALUES (?, ?, ?, ?, ?, ?, 0)', (code, title, desc, video_id, part_count + 1, category))
            conn.commit()
            await update.message.reply_text(f"✅ {part_count + 1}-qism\n\nYana qism? (Ha/Yo'q)")
            context.user_data['step'] = 'more_parts'
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")
        finally:
            conn.close()
    elif step == 'edit_video' or step == 'wait_video':
        edit_id = context.user_data.get('edit_id')
        video_id = update.message.video.file_id
        conn = sqlite3.connect(DATABASE)
        try:
            conn.execute('UPDATE movies SET video_id = ? WHERE id = ?', (video_id, edit_id))
            conn.commit()
            await update.message.reply_text("✅ Tahrirlandi!")
        except Exception as e:
            await update.message.reply_text(f"❌ {e}")
        finally:
            conn.close()
        context.user_data.clear()

async def admin_cmd(update, context):
    if not await is_private(update):
        return
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌")
        return
    kb = [[InlineKeyboardButton("Admin Panel", callback_data="admin_panel")]]
    await update.message.reply_text("⚙️", reply_markup=InlineKeyboardMarkup(kb))

def main():
    init_db()
    app = Application.builder().token(API_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("last", last_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("favorites", favorites_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Bot ishga tushmoqda...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
