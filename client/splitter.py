# splitter.py
import os
import argparse

def parse_size(size_str):
    units = {"kb": 1024, "mb": 1024**2, "gb": 1024**3}
    size_str = size_str.lower()
    for unit in units:
        if size_str.endswith(unit):
            num = float(size_str.replace(unit, ""))
            return int(num * units[unit] * 0.95)  # Use 95% of size to stay under Telegram limit
    # Added 'b' for bytes to allow for small test files
    if size_str.endswith('b'):
        return int(size_str[:-1])
    raise ValueError("Invalid size format. Use b, kb, mb, or gb (e.g., 2gb)")

def split_file(file_path, chunk_size):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File to split not found: {file_path}")

    file_size = os.path.getsize(file_path)
    base_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path) or '.' # Use current directory if empty
    part_num = 1
    parts = []

    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(int(chunk_size))
            if not chunk:
                break
            part_name = f"{base_name}.part{part_num}"
            part_path = os.path.join(file_dir, part_name)
            with open(part_path, 'wb') as pf:
                pf.write(chunk)
            parts.append(part_path)
            part_num += 1

    return parts

def join_files(parts_list, output_file):
    with open(output_file, 'wb') as outfile:
        for part in parts_list:
            if not os.path.exists(part):
                print(f"Warning: Part file not found, skipping: {part}")
                continue
            with open(part, 'rb') as pf:
                outfile.write(pf.read())
    return output_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Split or join files.")
    parser.add_argument('--split', help="Path to file to split")
    parser.add_argument('--size', help="Size of each part (e.g., 2gb, 500mb)", default="1.9gb")
    # Changed nargs to '*' to allow for zero or more arguments for --join
    parser.add_argument('--join', help="Path to the FIRST part to join. The rest are found automatically.")
    parser.add_argument('--output', help="Output filename for joined file. Optional for joining.")

    args = parser.parse_args()

    if args.split:
        try:
            chunk_size = parse_size(args.size)
            print(f"Splitting into chunks of ~{args.size} (using {chunk_size} bytes)...")
            result = split_file(args.split, chunk_size)
            print("Split into:", result)
        except Exception as e:
            print("Error:", e)
    
    elif args.join:
        # --- THIS IS THE NEW LOGIC ---
        first_part = args.join
        
        # 1. Get the base name (e.g., 'myvideo.mp4' from 'myvideo.mp4.part1')
        try:
            base_name = os.path.basename(first_part).rsplit('.part', 1)[0]
        except ValueError:
            print(f"Error: Invalid part file name '{first_part}'. Expected format 'filename.partX'.")
            exit()

        # 2. Automatically determine the output filename if not provided
        output_filename = args.output if args.output else base_name
        
        # 3. Find all parts in the same directory
        directory = os.path.dirname(first_part) or '.'
        all_files_in_dir = os.listdir(directory)
        
        # Filter for only the parts of our file
        detected_parts = [f for f in all_files_in_dir if f.startswith(base_name + '.part')]
        
        if not detected_parts:
            print(f"Error: No parts found for '{base_name}' in this directory.")
            exit()
            
        # 4. Sort the parts numerically, not alphabetically (so part10 comes after part9)
        detected_parts.sort(key=lambda name: int(name.rsplit('.part', 1)[1]))
        
        # Create full paths for each part
        full_part_paths = [os.path.join(directory, p) for p in detected_parts]
        
        print(f"Auto-detected {len(full_part_paths)} parts. Joining into '{output_filename}'...")
        output = join_files(full_part_paths, output_filename)
        print("Joined successfully into:", output)
        
    else:
        print("No action specified. Use --split <file> or --join <first_part>.")
