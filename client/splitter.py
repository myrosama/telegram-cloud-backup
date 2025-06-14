# splitter.py
import os

def parse_size(size_str):
    units = {"kb": 1024, "mb": 1024**2, "gb": 1024**3}
    size_str = size_str.lower()
    for unit in units:
        if size_str.endswith(unit):
            num = float(size_str.replace(unit, ""))
            return int(num * units[unit] * 0.95)  # Use 95% of size to stay under Telegram limit
    raise ValueError("Invalid size format. Use kb, mb, or gb (e.g., 2gb)")

def split_file(file_path, chunk_size):
    file_size = os.path.getsize(file_path)
    base_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)
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
            with open(part, 'rb') as pf:
                outfile.write(pf.read())
    return output_file

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Split or join files.")
    parser.add_argument('--split', help="Path to file to split")
    parser.add_argument('--size', help="Size of each part (e.g., 2gb, 500mb)", default="4.9gb")
    parser.add_argument('--join', nargs='+', help="Parts to join")
    parser.add_argument('--output', help="Output filename for joined file")

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
        if not args.output:
            print("You must provide --output for joining.")
        else:
            print("Joining...")
            output = join_files(args.join, args.output)
            print("Joined into:", output)
    else:
        print("Use --split <file> --size <e.g. 2gb> or --join <part1 part2 ...> --output <file>")
