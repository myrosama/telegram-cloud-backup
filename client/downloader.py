# client/downloader.py
import os
import sys
import json
import time
import asyncio
from telethon import TelegramClient
from tqdm import tqdm

# This allows the script to find our other project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from client.config import API_ID, API_HASH, CHANNEL_ID
except ImportError:
    print("---FATAL ERROR---")
    print("Could not import client/config.py. Please create it and add your API credentials.")
    sys.exit(1)

# --- CONFIGURATION & CONSTANTS ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', 'file_db.json'))
SESSION_NAME = "telegram_user_session"
DOWNLOAD_FOLDER = "downloads"
# --- SPEED OPTIMIZATION ---
# Number of chunks to download at the same time.
CONCURRENT_DOWNLOADS = 4

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_PATH):
        return None
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Database file is corrupted or empty.")
            return None

# --- Self-Contained Join Function ---
def join_files_here(parts_list, output_file):
    """
    Joins a list of file parts into a single output file.
    """
    print("\nJoining parts...")
    with open(output_file, 'wb') as outfile:
        for part_path in tqdm(parts_list, desc="Joining"):
            with open(part_path, 'rb') as part_file:
                outfile.write(part_file.read())
    return output_file

# --- CORE DOWNLOAD LOGIC ---
async def download_worker(client, msg_id, part_path, pbar_chunk):
    """A worker that downloads a single file part."""
    message = await client.get_messages(CHANNEL_ID, ids=msg_id)
    if not message or not message.document:
        print(f"\nWarning: Could not find document for message ID {msg_id}. Skipping.")
        return None

    def progress_callback(current, total):
        pbar_chunk.update(current - pbar_chunk.n)

    await client.download_media(
        message,
        file=part_path,
        progress_callback=progress_callback
    )
    pbar_chunk.close()
    return part_path

async def download_file_main(client, file_to_download, db):
    """Downloads all parts of a file concurrently and joins them."""
    file_info = db[file_to_download]
    message_ids = file_info["message_ids"]
    total_parts = file_info["total_parts"]
    
    print(f"Starting download for '{file_to_download}' which has {total_parts} parts.")
    print(f"Downloading with up to {CONCURRENT_DOWNLOADS} connections at once.")

    temp_download_dir = os.path.join(DOWNLOAD_FOLDER, f"{file_to_download}_parts")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
    tasks = []

    async def task_creator(msg_id, part_index):
        async with semaphore:
            part_path = os.path.join(temp_download_dir, str(part_index))
            pbar_chunk = tqdm(total=0, unit='B', unit_scale=True, desc=f"Part {part_index+1}")
            # We don't know the size yet, so we'll update it later
            
            return await download_worker(client, msg_id, part_path, pbar_chunk)

    try:
        for i, msg_id in enumerate(message_ids):
            tasks.append(task_creator(msg_id, i))

        downloaded_parts_paths = await asyncio.gather(*tasks)
        # Filter out any None results from skipped parts
        downloaded_parts_paths = [path for path in downloaded_parts_paths if path is not None]

        if len(downloaded_parts_paths) != total_parts:
            print(f"\nError: Download failed. Expected {total_parts} parts, but only got {len(downloaded_parts_paths)}. Aborting.")
            return

        print("\nAll parts downloaded successfully. Now joining them...")
        
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        final_output_path = os.path.join(DOWNLOAD_FOLDER, file_to_download)
        
        downloaded_parts_paths.sort(key=lambda x: int(os.path.basename(x)))

        join_files_here(downloaded_parts_paths, final_output_path)

        print(f"\n✅ Success! File '{file_to_download}' has been reassembled in the '{DOWNLOAD_FOLDER}' directory.")

    except Exception as e:
        print(f"\n---FATAL DOWNLOAD ERROR---")
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up temporary part files...")
        # Code to clean up downloaded_parts_paths and temp_download_dir
        for path in downloaded_parts_paths:
            if path and os.path.exists(path):
                os.remove(path)
        if os.path.exists(temp_download_dir):
            try:
                if not os.listdir(temp_download_dir):
                    os.rmdir(temp_download_dir)
            except OSError as e:
                print(f"Error during cleanup: {e}")
        print("Cleanup complete.")

async def main():
    """Main function to connect the client and start the download process."""
    db = load_db()
    if not db:
        print("Database not found or is empty. Please upload a file first.")
        return

    print("Available files to download:")
    file_list = list(db.keys())
    for i, filename in enumerate(file_list):
        size_mb = db[filename]['file_size_bytes'] / (1024 * 1024)
        print(f"  {i + 1}: {filename} ({size_mb:.2f} MB)")
    
    try:
        choice = int(input("Enter the number of the file you want to download: ")) - 1
        if not 0 <= choice < len(file_list):
            print("Invalid number.")
            return
        file_to_download = file_list[choice]
    except (ValueError, IndexError):
        print("Invalid input.")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    print("Connecting to Telegram as user...")
    await client.start()
    print("Successfully connected.")

    await download_file_main(client, file_to_download, db)

    await client.disconnect()
    print("Client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
