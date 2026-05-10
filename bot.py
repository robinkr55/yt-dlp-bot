import telebot
import yt_dlp
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# URL temporarily store karne ke liye
user_url_store = {}

QUALITY_OPTIONS = {
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",   # 4K
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",   # 2K
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",   # Full HD
    "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",     # HD
    "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",     # SD
    "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",     # Low
    "audio": "bestaudio/best",                                          # Sirf Audio MP3
}

QUALITY_LABELS = {
    "2160p": "4K Ultra HD 🔵",
    "1440p": "2K QHD 🟣",
    "1080p": "1080p Full HD 🟢",
    "720p":  "720p HD 🟡",
    "480p":  "480p SD 🟠",
    "360p":  "360p Low 🔴",
    "audio": "🎵 Sirf Audio (MP3)",
}


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "👋 *Namaste! Main Video Downloader Bot hoon!*\n\n"
        "🌐 *Supported Platforms:*\n"
        "▶️ YouTube • 📸 Instagram • 🐦 Twitter/X\n"
        "🎵 TikTok • 📘 Facebook • 🎬 Vimeo\n"
        "🎙️ SoundCloud • 🔗 1000+ aur bhi!\n\n"
        "📤 *Kaise use karo:*\n"
        "Bas koi bhi video link bhejo!\n"
        "Main quality choose karne ka option dunga 🎯",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(
        message,
        "ℹ️ *Help Guide:*\n\n"
        "1️⃣ Koi bhi video URL bhejo\n"
        "2️⃣ Quality select karo\n"
        "3️⃣ Video/Audio download ho jayega!\n\n"
        "⚠️ *Limits:*\n"
        "• Max file size: 50MB (Telegram limit)\n"
        "• Badi files ke liye lower quality choose karo\n\n"
        "🌐 *Platforms:* YouTube, Instagram, TikTok, Twitter, Facebook, Vimeo, SoundCloud aur bahut saare!",
        parse_mode="Markdown"
    )


def quality_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, label in QUALITY_LABELS.items():
        buttons.append(InlineKeyboardButton(label, callback_data=f"quality_{key}"))
    markup.add(*buttons)
    return markup


@bot.message_handler(func=lambda message: True)
def handle_url(message):
    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "⚠️ Valid URL bhejo (http se shuru hona chahiye).\n\nExample: https://youtube.com/watch?v=...")
        return

    # URL store karo
    user_url_store[message.chat.id] = url

    # Platform detect karne ki koshish
    platform = detect_platform(url)

    bot.reply_to(
        message,
        f"🔗 *Link mila!*\n"
        f"🌐 Platform: *{platform}*\n\n"
        f"📊 *Kaun si quality mein download karein?*",
        reply_markup=quality_keyboard(),
        parse_mode="Markdown"
    )


def detect_platform(url):
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube ▶️"
    elif "instagram.com" in url_lower:
        return "Instagram 📸"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X 🐦"
    elif "tiktok.com" in url_lower:
        return "TikTok 🎵"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "Facebook 📘"
    elif "vimeo.com" in url_lower:
        return "Vimeo 🎬"
    elif "soundcloud.com" in url_lower:
        return "SoundCloud 🎙️"
    elif "dailymotion.com" in url_lower:
        return "Dailymotion 📹"
    else:
        return "Unknown Platform 🌐"


@bot.callback_query_handler(func=lambda call: call.data.startswith("quality_"))
def handle_quality(call):
    quality_key = call.data.replace("quality_", "")
    chat_id = call.message.chat.id
    url = user_url_store.get(chat_id)

    if not url:
        bot.answer_callback_query(call.id, "❌ URL nahi mila! Dobara link bhejo.")
        return

    bot.answer_callback_query(call.id, f"✅ {QUALITY_LABELS[quality_key]} select kiya!")
    bot.edit_message_text(
        f"⏳ *Download ho raha hai...*\n"
        f"📊 Quality: *{QUALITY_LABELS[quality_key]}*\n"
        f"🔗 URL: `{url[:50]}...`\n\n"
        f"Please wait karo... 🙏",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown"
    )

    format_str = QUALITY_OPTIONS[quality_key]
    is_audio = quality_key == "audio"

    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(title).50s.%(ext)s",
        "format": format_str,
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4" if not is_audio else None,
    }

    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if is_audio:
                filename = os.path.splitext(filename)[0] + ".mp3"

        title = info.get("title", "Video")[:50]
        duration = info.get("duration", 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"

        file_size = os.path.getsize(filename)
        file_size_mb = file_size / (1024 * 1024)

        if file_size_mb > 50:
            bot.send_message(
                chat_id,
                f"❌ *File bahut badi hai!* ({file_size_mb:.1f}MB)\n\n"
                f"Telegram ka limit 50MB hai.\n"
                f"Please lower quality choose karo! 👇",
                reply_markup=quality_keyboard(),
                parse_mode="Markdown"
            )
            os.remove(filename)
            user_url_store[chat_id] = url
            return

        caption = (
            f"✅ *Download Complete!*\n"
            f"🎬 *{title}*\n"
            f"⏱️ Duration: {duration_str}\n"
            f"📊 Quality: {QUALITY_LABELS[quality_key]}\n"
            f"📦 Size: {file_size_mb:.1f}MB"
        )

        with open(filename, "rb") as f:
            if is_audio:
                bot.send_audio(chat_id, f, caption=caption, parse_mode="Markdown")
            else:
                bot.send_video(chat_id, f, caption=caption, parse_mode="Markdown", supports_streaming=True)

        os.remove(filename)
        user_url_store.pop(chat_id, None)

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)[:300]
        bot.send_message(
            chat_id,
            f"❌ *Download fail hua!*\n\n"
            f"Reason: `{error_msg}`\n\n"
            f"💡 Try karo:\n"
            f"• Lower quality choose karo\n"
            f"• Check karo URL valid hai\n"
            f"• Private video nahi honi chahiye",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ *Kuch gadbad hui!*\n`{str(e)[:200]}`",
            parse_mode="Markdown"
        )


print("🤖 Bot chal raha hai... 24/7 Ready!")
bot.infinity_polling()
