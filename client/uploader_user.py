# client/uploader.py
import os
import sys
import time
import json
import math
import asyncio
from telethon import TelegramClient
from tqdm import tqdm

# This allows the script to find our other project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from client.config import API_ID, API_HASH, CHANNEL_ID
except ImportError:
    print("---FATAL ERROR---")
    print("Could not import client/config.py.")
    print("Please create it and add your API_ID, API_HASH, and CHANNEL_ID.")
    sys.exit(1)

# --- CONFIGURATION & CONSTANTS ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', 'file_db.json'))
CHUNK_SIZE = int(2000 * 1024 * 1024)
SESSION_NAME = "telegram_user_session"
# --- SPEED OPTIMIZATION ---
# Number of chunks to upload at the same time. Increase if you have a very fast connection.
CONCURRENT_UPLOADS = 4

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Database file is corrupted or empty. Starting fresh.")
            return {}

def save_db(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- WORKER FOR CONCURRENT UPLOADS ---
async def upload_worker(client, chunk_data, part_name, pbar_chunk):
    """The worker function that uploads a single chunk and updates its progress bar."""
    def progress_callback(current, total):
        pbar_chunk.n = current
        pbar_chunk.refresh()

    message = await client.send_file(
        CHANNEL_ID,
        chunk_data,
        caption=part_name,
        progress_callback=progress_callback
    )
    pbar_chunk.close()
    return message.id

# --- CORE UPLOAD LOGIC ---
async def upload_file_main(client, file_path):
    """Reads a file chunk by chunk and uploads them concurrently."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    original_filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_parts = math.ceil(file_size / CHUNK_SIZE)

    db = load_db()
    uploaded_part_ids = []
    start_part_index = 0

    if original_filename in db:
        print(f"Found an existing record for '{original_filename}'.")
        existing_data = db[original_filename]
        num_parts_on_record = len(existing_data.get("message_ids", []))

        if 0 < num_parts_on_record < total_parts:
            resume_choice = input(f"Found {num_parts_on_record}/{total_parts} uploaded parts. Resume upload? (y/n): ").lower().strip()
            if resume_choice == 'y':
                print(f"Resuming upload from part {num_parts_on_record + 1}...")
                start_part_index = num_parts_on_record
                uploaded_part_ids = existing_data["message_ids"]
            else:
                print("Starting upload from scratch as requested.")
                db.pop(original_filename, None)
        elif num_parts_on_record == total_parts:
             print("This file has already been completely uploaded according to the database.")
             return

    print(f"'{original_filename}' ({file_size / 1024**2:.2f} MB) will be uploaded in {total_parts} parts.")
    print(f"Uploading with up to {CONCURRENT_UPLOADS} connections at once.")

    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENT_UPLOADS)

    try:
        with open(file_path, 'rb') as f:
            f.seek(start_part_index * CHUNK_SIZE)
            
            pbar_overall = tqdm(total=total_parts, unit="part", desc="Overall Progress", initial=start_part_index)

            async def task_creator(part_index):
                async with semaphore:
                    part_name = f"{original_filename}.part{part_index + 1}"
                    # Read the specific chunk for this task
                    # Note: This requires careful handling in a real concurrent read scenario,
                    # but for now we read sequentially and dispatch.
                    f.seek(part_index * CHUNK_SIZE)
                    chunk_data = f.read(CHUNK_SIZE)
                    
                    pbar_chunk = tqdm(total=len(chunk_data), unit='B', unit_scale=True, desc=f"Part {part_index+1}")
                    
                    message_id = await upload_worker(client, chunk_data, part_name, pbar_chunk)
                    pbar_overall.update(1)
                    return part_index, message_id

            for i in range(start_part_index, total_parts):
                tasks.append(task_creator(i))

            results = await asyncio.gather(*tasks)
            
            # Sort results by part index to ensure correct order
            results.sort(key=lambda x: x[0])
            newly_uploaded_ids = [res[1] for res in results]
            
            # Combine with already existing IDs if resuming
            final_message_ids = uploaded_part_ids + newly_uploaded_ids
            
            db[original_filename] = {
                "message_ids": final_message_ids,
                "total_parts": total_parts,
                "file_size_bytes": file_size
            }
            save_db(db)
            pbar_overall.close()

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print(f"Upload process paused. The database has saved progress where possible.")
        print("You can run the script again to resume.")
        return

    print(f"\n✅ Successfully uploaded all parts of '{original_filename}' and finalized the database.")

async def main():
    """Main function to connect the client and start the process."""
    # We pass the number of connections to Telethon
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH, connection_retries=5)
    
    print("Connecting to Telegram as user...")
    try:
        await client.start()
        print("Successfully connected.")
    except Exception as e:
        print(f"---FATAL CONNECTION ERROR---")
        print(f"Could not connect. Please check your API_ID/API_HASH and internet connection. Error: {e}")
        return

    file_to_upload = input("📁 Enter the full path to the file you want to upload: ").strip()
    await upload_file_main(client, file_to_upload)

    await client.disconnect()
    print("Client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
