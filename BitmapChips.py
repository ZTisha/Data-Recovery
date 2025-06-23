import os
import csv
from PIL import Image
import numpy as np
from math import isqrt, ceil

# Constants
CHIP_WIDTH = 1024
CHIP_HEIGHT = 1024
WORD_SIZE = 8
EXPECTED_BITS = 131070 * 8  # 1,048,560 bits per chip

# --- Helper Functions ---

def read_csv_bits(filepath):
    """Reads a CSV and returns a flat bit list."""
    bits = []
    with open(filepath, 'r') as f:
        lines = list(f)
        if len(lines) <= 1:
            raise ValueError(f"CSV file {filepath} is empty or has no data.")
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue
            _, byte = parts[:2]
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(WORD_SIZE)])
    return bits

def split_chip_bits(full_bits):
    """Splits full bitstream into chip 1 and chip 2 based on address logic."""
    chip1_bits = full_bits[0 : EXPECTED_BITS]
    chip2_bits = full_bits[EXPECTED_BITS : EXPECTED_BITS*2]
    return chip1_bits, chip2_bits

def pad_bits(bits, target_length):
    """Pads or trims a bit list to a specific length."""
    if len(bits) < target_length:
        bits += [0] * (target_length - len(bits))
    else:
        bits = bits[:target_length]
    return bits

def create_bitmap(bits, width, height):
    """Creates a black-and-white bitmap from bit array."""
    img = Image.new('1', (width, height), color=0)
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if idx < len(bits):
                img.putpixel((x, y), 1 - bits[idx])
    return img

def create_distribution_bitmap(bit_samples, width, height):
    """Creates a grayscale heatmap based on frequency of 1s."""
    accumulation = np.sum(bit_samples, axis=0)
    normalized = (255 - (accumulation * 255 / len(bit_samples))).astype(np.uint8)
    img = Image.fromarray(normalized.reshape((height, width)), mode='L')
    return img

# --- Main Menu ---
def main():
    print("\nSelect Bitmap Mode:")
    print("1. Distribution Bitmap of Chip 1 or Chip 2 (Flexible Samples)")
    print("2. Combined Bitmap of Both Chips (Flexible Samples)")
    print("3. General Image Bitmap from CSV (any size)")
    choice = input("Enter option (1/2/3): ").strip()

    # Make output dir
    outdir = "BITMAPS"
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if choice == "1":
        folder = input("Enter folder name (e.g., 06_01_25M): ").strip()
        chip_select = input("Select chip (1 or 2): ").strip()

        if not os.path.exists(folder):
            print("Folder not found.")
            return

        # Sample selection logic
        print("\nSample Selection:")
        print("1. All available samples")
        print("2. One specific sample")
        print("3. A range of samples")
        sample_mode = input("Choose an option (1/2/3): ").strip()

        csv_files = []

        if sample_mode == "1":
            csv_files = sorted([
                f for f in os.listdir(folder)
                if f.startswith(folder + "_") and f.endswith(".csv")
            ])
        elif sample_mode == "2":
            sample_id = input("Enter sample number (e.g., 7): ").strip()
            csv_files = [f"{folder}_{sample_id}.csv"]
        elif sample_mode == "3":
            start = int(input("Start sample number: ").strip())
            end = int(input("End sample number: ").strip())
            csv_files = [f"{folder}_{i}.csv" for i in range(start, end + 1)]
        else:
            print("Invalid sample selection.")
            return

        chip_samples = []

        for file in csv_files:
            full_path = os.path.join(folder, file)
            full_bits = read_csv_bits(full_path)
            chip1, chip2 = split_chip_bits(full_bits)
            chip_bits = chip1 if chip_select == "1" else chip2
            chip_bits = pad_bits(chip_bits, CHIP_WIDTH * CHIP_HEIGHT)
            chip_samples.append(chip_bits)

        dist_img = create_distribution_bitmap(np.array(chip_samples), CHIP_WIDTH, CHIP_HEIGHT)
        outname = f"{folder}_chip{chip_select}_distribution.png"
        dist_img.save(os.path.join(outdir, outname))
        print(f"Chip {chip_select} distribution bitmap saved to {outdir}/{outname}")

    elif choice == "2":
        folder = input("Enter folder name (e.g., 06_01_25M): ").strip()

        if not os.path.exists(folder):
            print("Folder not found.")
            return

        # Sample selection logic
        print("\nSample Selection:")
        print("1. All available samples")
        print("2. One specific sample")
        print("3. A range of samples")
        sample_mode = input("Choose an option (1/2/3): ").strip()

        csv_files = []

        if sample_mode == "1":
            csv_files = sorted([
                f for f in os.listdir(folder)
                if f.startswith(folder + "_") and f.endswith(".csv")
            ])
        elif sample_mode == "2":
            sample_id = input("Enter sample number (e.g., 7): ").strip()
            csv_files = [f"{folder}_{sample_id}.csv"]
        elif sample_mode == "3":
            start = int(input("Start sample number: ").strip())
            end = int(input("End sample number: ").strip())
            csv_files = [f"{folder}_{i}.csv" for i in range(start, end + 1)]
        else:
            print("Invalid sample selection.")
            return

        chip1_samples, chip2_samples = [], []

        for file in csv_files:
            full_path = os.path.join(folder, file)
            full_bits = read_csv_bits(full_path)
            chip1, chip2 = split_chip_bits(full_bits)
            chip1 = pad_bits(chip1, CHIP_WIDTH * CHIP_HEIGHT)
            chip2 = pad_bits(chip2, CHIP_WIDTH * CHIP_HEIGHT)
            chip1_samples.append(chip1)
            chip2_samples.append(chip2)

        chip1_map = create_distribution_bitmap(np.array(chip1_samples), CHIP_WIDTH, CHIP_HEIGHT)
        chip2_map = create_distribution_bitmap(np.array(chip2_samples), CHIP_WIDTH, CHIP_HEIGHT)

        combined = Image.blend(chip1_map.convert("RGB"), chip2_map.convert("RGB"), alpha=0.5)
        outname = f"{folder}_combined_distribution.png"
        combined.save(os.path.join(outdir, outname))
        print(f"Combined bitmap saved to {outdir}/{outname}")

    elif choice == "3":
        csv_file = input("Enter image CSV file name (Address,Word): ").strip()
        if not csv_file.endswith(".csv"):
            csv_file += ".csv"
        if not os.path.exists(csv_file):
            print("File not found.")
            return

        bits = read_csv_bits(csv_file)
        bitlen = len(bits)
        side = isqrt(bitlen)
        width = side
        height = ceil(bitlen / width)
        bits = pad_bits(bits, width * height)

        img = create_bitmap(bits, width, height)
        outname = f"{os.path.splitext(csv_file)[0]}_image_bitmap.png"
        img.save(os.path.join(outdir, outname))
        print(f"Image bitmap saved to {outdir}/{outname}")

    else:
        print("Invalid option. Exiting.")

if __name__ == "__main__":
    main()
