# client/uploader.py
import os
import sys
import time
import json
import telebot
from tqdm import tqdm

# This allows the script to find our other project modules
# when run from the root directory (e.g., `python client/uploader.py`)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from bot.config import BOT_TOKEN, CHANNEL_ID
    from client.splitter import split_file 
except ImportError as e:
    print("---FATAL ERROR---")
    print("Could not import necessary modules.")
    print("Please ensure that 'bot/config.py' and 'client/splitter.py' exist and are correct.")
    print(f"Import Error Details: {e}")
    sys.exit(1)

# --- CONFIGURATION & CONSTANTS ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', 'file_db.json'))
CHUNK_SIZE = int((50 * 1024 * 1024) * 0.95) # 95% of 50MB

# --- DATABASE FUNCTIONS ---
def load_db():
    """Loads the JSON database that tracks uploaded files."""
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Database file is corrupted or empty. Starting fresh.")
            return {}

def save_db(data):
    """Saves the given data to the JSON database."""
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- CORE UPLOAD LOGIC ---
def upload_file_main(file_path, bot_instance):
    """Splits a file and uploads its parts to the Telegram channel."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    original_filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    db = load_db()
    if original_filename in db:
        print(f"Warning: A file named '{original_filename}' already exists in the database.")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("Upload cancelled by user.")
            return

    parts = split_file(file_path, CHUNK_SIZE)

    if not parts:
        print("File splitting resulted in no parts. Is the file empty?")
        return

    print(f"'{original_filename}' ({file_size / 1024**2:.2f} MB) was split into {len(parts)} parts.")
    print("Starting upload process...")

    uploaded_part_ids = []
    try:
        with tqdm(total=len(parts), unit="part", desc=f"Uploading {original_filename}") as pbar:
            for part_path in parts:
                part_name = os.path.basename(part_path)
                with open(part_path, 'rb') as part_file:
                    message = bot_instance.send_document(
                        chat_id=CHANNEL_ID,
                        document=part_file,
                        caption=part_name,
                        disable_notification=True
                    )
                    uploaded_part_ids.append(message.document.file_id)
                
                os.remove(part_path)
                pbar.update(1)
                time.sleep(1) 
    except Exception as e:
        print(f"\n---FATAL UPLOAD ERROR---")
        print(f"An error occurred: {e}")
        print("Cleaning up any remaining local file parts.")
        for part_path in parts:
            if os.path.exists(part_path):
                os.remove(part_path)
        return

    db = load_db()
    db[original_filename] = {
        "file_ids": uploaded_part_ids,
        "total_parts": len(parts),
        "file_size_bytes": file_size
    }
    save_db(db)
    print(f"\n✅ Successfully uploaded all parts of '{original_filename}' and updated the database.")

# --- SCRIPT EXECUTION ---
if __name__ == "__main__":
    try:
        print("Connecting to Telegram...")
        bot = telebot.TeleBot(BOT_TOKEN)
        bot_info = bot.get_me()
        print(f"Successfully connected as bot: {bot_info.first_name} (@{bot_info.username})")
    except Exception as e:
        print("---FATAL CONNECTION ERROR---")
        print("Could not connect to Telegram. Please check your BOT_TOKEN in bot/config.py.")
        print(f"Details: {e}")
        sys.exit(1)

    file_to_upload = input("📁 Enter the full path to the file you want to upload: ").strip()
    upload_file_main(file_to_upload, bot)