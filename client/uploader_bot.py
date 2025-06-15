# client/uploader_bot.py
import os
import sys
import time
import json
import math
import telebot
from tqdm import tqdm

# This allows the script to find our other project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from bot.config import BOT_TOKEN, CHANNEL_ID
except ImportError as e:
    print("---FATAL ERROR---")
    print("Could not import bot/config.py.")
    print(f"Details: {e}")
    sys.exit(1)

# --- CONFIGURATION & CONSTANTS ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', 'file_db.json'))
CHUNK_SIZE = int(19 * 1024 * 1024)
UPLOAD_RETRIES = 10 # Increased retries for more robustness

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_db(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- CORE UPLOAD LOGIC ---
def upload_file_bot(file_path, bot_instance):
    """Splits a file into 19MB chunks and uploads them via the Bot API."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    original_filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_parts = math.ceil(file_size / CHUNK_SIZE)

    db = load_db()
    uploaded_message_info = []
    start_part_index = 0

    # --- NEW: Automatic Resume Logic ---
    if original_filename in db:
        existing_data = db[original_filename]
        num_parts_on_record = len(existing_data.get("messages", []))
        
        # If the upload is incomplete, automatically resume
        if 0 < num_parts_on_record < total_parts:
            print(f"Found incomplete upload for '{original_filename}'. Automatically resuming from part {num_parts_on_record + 1}.")
            start_part_index = num_parts_on_record
            uploaded_message_info = existing_data["messages"]
        
        # If the upload is complete, ask to overwrite
        elif num_parts_on_record >= total_parts:
            print(f"A complete record for '{original_filename}' already exists in the database.")
            overwrite_choice = input("Do you want to overwrite it and re-upload from scratch? (y/n): ").lower().strip()
            if overwrite_choice != 'y':
                print("Upload cancelled.")
                return # Exit the function
            else:
                # User chose to overwrite, so reset everything
                start_part_index = 0
                uploaded_message_info = []
                # Remove the old entry from the database before starting the new upload
                db.pop(original_filename, None)
                save_db(db)


    print(f"'{original_filename}' ({file_size / 1024**2:.2f} MB) will be uploaded in {total_parts} parts.")

    try:
        with open(file_path, 'rb') as f:
            f.seek(start_part_index * CHUNK_SIZE)
            with tqdm(total=total_parts, unit="part", desc="Overall Progress", initial=start_part_index) as pbar:
                for i in range(start_part_index, total_parts):
                    part_name = f"{original_filename}.part{i + 1}"
                    chunk_data = f.read(CHUNK_SIZE)
                    if not chunk_data: break

                    for attempt in range(UPLOAD_RETRIES):
                        try:
                            message = bot_instance.send_document(
                                chat_id=CHANNEL_ID,
                                document=chunk_data,
                                visible_file_name=part_name,
                                caption=part_name,
                                timeout=90 # Increased timeout
                            )
                            uploaded_message_info.append({
                                'message_id': message.id,
                                'file_id': message.document.file_id
                            })
                            db[original_filename] = {
                                "messages": uploaded_message_info,
                                "total_parts": total_parts,
                                "file_size_bytes": file_size,
                                "upload_method": "bot"
                            }
                            save_db(db)
                            break # Success, exit retry loop
                        
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                error_json = json.loads(e.result.text)
                                retry_after = error_json['parameters']['retry_after']
                                print(f"\nRate limit hit. Waiting for {retry_after} seconds as requested by Telegram...")
                                time.sleep(retry_after)
                                continue 
                            else:
                                print(f"\nTelegram API Error: {e}")
                                time.sleep(5)
                        except Exception as e:
                            print(f"\nFailed to upload {part_name} on attempt {attempt + 1}. Error: {e}")
                            if attempt < UPLOAD_RETRIES - 1:
                                time.sleep(10) # General network error, wait longer
                            else:
                                raise e # All retries failed, stop the upload
                    
                    pbar.update(1)
                    # --- NEW: Proactive delay to prevent rate limiting ---
                    time.sleep(1)

    except Exception as e:
        print(f"\nUpload process failed. Last progress was saved. Error: {e}")
        return

    print(f"\n✅ Successfully uploaded all parts of '{original_filename}'.")

def main():
    """Main function for the bot uploader."""
    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        bot.get_me()
        print("Bot connection successful.")
    except Exception as e:
        print("Could not connect to bot. Check BOT_TOKEN in bot/config.py.")
        return

    file_to_upload = input("📁 Enter the full path to the file you want to upload: ").strip()
    upload_file_bot(file_to_upload, bot)

if __name__ == "__main__":
    main()
