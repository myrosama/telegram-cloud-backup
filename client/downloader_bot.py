# client/downloader_bot.py
import os
import sys
import json
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# This allows the script to find our other project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from bot.config import BOT_TOKEN
except ImportError:
    print("---FATAL ERROR---")
    print("Could not import bot/config.py. Please create it and add your BOT_TOKEN.")
    sys.exit(1)

# --- CONFIGURATION & CONSTANTS ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', 'file_db.json'))
DOWNLOAD_FOLDER = "downloads"
# --- SPEED/STABILITY OPTIMIZATION ---
# A high number of connections can cause instability. 20-25 is a good balance.
CONCURRENT_DOWNLOADS = 25
# Number of times to retry a failed part download
DOWNLOAD_RETRIES = 5

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
    print("\nJoining parts...")
    with open(output_file, 'wb') as outfile:
        for part_path in tqdm(parts_list, desc="Joining"):
            with open(part_path, 'rb') as part_file:
                outfile.write(part_file.read())
    return output_file

# --- NEW: Worker function with robust exponential backoff retry logic ---
def download_part_worker(bot_token, file_id, part_path):
    """This function runs in a separate thread to download one part, with smart retries."""
    delay = 3  # Initial delay in seconds for retries
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            # Get file path from Telegram with a longer timeout
            file_info_from_api = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}", timeout=30).json()
            
            if not file_info_from_api.get('ok'):
                description = file_info_from_api.get('description', 'Unknown API Error')
                # If error is "wrong file_id", no point in retrying
                if "wrong file_id" in description:
                    print(f"\n[FATAL] Error for file_id {file_id}: {description}")
                    return None
                # For other API errors, we can retry
                raise requests.exceptions.RequestException(f"API Error: {description}")
            
            file_path_on_server = file_info_from_api['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path_on_server}"
            
            # Stream the download with a generous timeout
            response = requests.get(file_url, stream=True, timeout=120)
            response.raise_for_status() # Raise an exception for bad status codes (like 404, 500)
            
            with open(part_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # If we reach here, download was successful
            return part_path
        
        except requests.exceptions.RequestException as e:
            print(f"\nWarning: Attempt {attempt + 1}/{DOWNLOAD_RETRIES} failed for a part. Error: {e}")
            if attempt < DOWNLOAD_RETRIES - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff: 3s, 6s, 12s...
            else:
                print(f"\n[FATAL] Failed to download part with file_id {file_id} after {DOWNLOAD_RETRIES} attempts.")
                return None # Return None after all retries fail
    return None

# --- CORE DOWNLOAD LOGIC ---
def download_file_main(file_to_download, db):
    """Downloads all parts of a file concurrently using threads and joins them."""
    file_info = db[file_to_download]
    messages = file_info.get("messages", [])
    if not messages:
        print(f"Error: No message data found for '{file_to_download}'. Cannot download.")
        return

    total_parts = file_info["total_parts"]
    
    print(f"Starting download for '{file_to_download}' which has {total_parts} parts.")
    print(f"Using up to {CONCURRENT_DOWNLOADS} concurrent connections.")

    temp_download_dir = os.path.join(DOWNLOAD_FOLDER, f"{file_to_download}_parts")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    downloaded_parts_paths = []

    try:
        with ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOADS) as executor:
            future_to_part_path = {}
            for i, msg_info in enumerate(messages):
                file_id = msg_info.get('file_id')
                if not file_id:
                    print(f"Warning: Missing file_id for part {i+1}. Skipping.")
                    continue
                
                part_path = os.path.join(temp_download_dir, f"part_{i}")
                future = executor.submit(download_part_worker, BOT_TOKEN, file_id, part_path)
                future_to_part_path[future] = part_path

            with tqdm(total=total_parts, unit="part", desc=f"Downloading {file_to_download}") as pbar:
                for future in as_completed(future_to_part_path):
                    result_path = future.result()
                    if result_path:
                        downloaded_parts_paths.append(result_path)
                    pbar.update(1)

        if len(downloaded_parts_paths) != total_parts:
            print(f"\nError: Download failed. Expected {total_parts} parts, but only got {len(downloaded_parts_paths)}.")
            return

        print("\nAll parts downloaded successfully. Now joining them...")
        
        final_output_path = os.path.join(DOWNLOAD_FOLDER, file_to_download)
        downloaded_parts_paths.sort(key=lambda x: int(os.path.basename(x).split('_')[1]))
        join_files_here(downloaded_parts_paths, final_output_path)

        print(f"\n✅ Success! File '{file_to_download}' has been reassembled in the '{DOWNLOAD_FOLDER}' directory.")

    except Exception as e:
        print(f"\n---FATAL DOWNLOAD ERROR---")
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up temporary part files...")
        for path in downloaded_parts_paths:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(temp_download_dir) and len(os.listdir(temp_download_dir)) == 0:
            os.rmdir(temp_download_dir)
        print("Cleanup complete.")

def main():
    db = load_db()
    if not db:
        print("Database not found or is empty. Please upload a file first.")
        return

    print("Available files to download (Bot Method only):")
    
    bot_files = {name: info for name, info in db.items() if info.get("upload_method") == "bot"}
    
    if not bot_files:
        print("No files uploaded with the bot method were found.")
        return

    file_list = list(bot_files.keys())
    for i, filename in enumerate(file_list):
        size_mb = bot_files[filename]['file_size_bytes'] / (1024 * 1024)
        print(f"  {i + 1}: {filename} ({size_mb:.2f} MB)")
    
    try:
        choice = int(input("Enter the number of the file you want to download: ")) - 1
        file_to_download = file_list[choice]
    except (ValueError, IndexError):
        print("Invalid input.")
        return

    download_file_main(file_to_download, db)

if __name__ == "__main__":
    main()
