# bot/bot.py
import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN, OWNER_ID, CHANNEL_ID, DB_PATH

# Create file_db.json if it doesn't exist
def init_file_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump({}, f)

def load_file_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_file_entry(filename, num_parts, user_id):
    file_db = load_file_db()
    file_db[filename] = {
        "parts": num_parts,
        "uploaded_by": user_id
    }
    with open(DB_PATH, "w") as f:
        json.dump(file_db, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Welcome to Telegram Cloud!\n\n"
        "Use /upload to upload a file via desktop app\n"
        "Use /files to view uploaded files\n"
        "Use /download <name> to download a file"
    )

async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_db = load_file_db()
    if not file_db:
        await update.message.reply_text("📂 No files uploaded yet.")
        return

    file_list = "\n".join(f"- {fname}" for fname in file_db)
    await update.message.reply_text(f"📦 Uploaded files:\n{file_list}")

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💻 Please launch the desktop app to upload your file.\n"
        "Make sure your bot token and channel ID are set correctly."
    )

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide the filename.\nExample: /download bigfile.zip")
    else:
        filename = " ".join(context.args)
        await update.message.reply_text(f"⏬ Preparing `{filename}` for download...", parse_mode="Markdown")

if __name__ == "__main__":
    init_file_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("files", files))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("download", download))

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()
