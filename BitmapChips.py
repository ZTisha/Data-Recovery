import os
import csv
from PIL import Image
import numpy as np
from math import isqrt, ceil

# Constants
CHIP_WIDTH = 1024
CHIP_HEIGHT = 1024
WORD_SIZE = 8
SAMPLES = 25
CHIP1_END = 131070  # Chip 1: address 0 to 131069
CHIP2_START = 131071  # Chip 2: address 131071 onward
EXPECTED_BITS = 1048560  # 131070 bytes * 8

# --- Helper Functions ---

def read_csv_bits(filepath):
    """Reads a CSV and returns a flat bit list."""
    bits = []
    with open(filepath, 'r') as f:
        next(f)  # Skip header
        for line in f:
            _, byte = line.strip().split(',')
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(WORD_SIZE)])
    return bits

def split_chip_bits(full_bits):
    """Splits full bitstream into two chips (assumes 8 bits per address)."""
    chip1_bits = full_bits[:CHIP1_END * 8]
    chip2_bits = full_bits[CHIP2_START * 8:]
    return chip1_bits, chip2_bits

def pad_bits(bits, target_length):
    """Pads bit list with zeros to reach desired length."""
    if len(bits) < target_length:
        bits += [0] * (target_length - len(bits))
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
    print("1. Distribution Bitmap of Chip 1 or Chip 2 (25 Samples)")
    print("2. Combined Bitmap of Both Chips (25 Samples)")
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

        chip_samples = []

        for i in range(1, SAMPLES + 1):
            file = os.path.join(folder, f"{folder}_{i}.csv")
            if not os.path.exists(file):
                print(f"Missing: {file}")
                return
            full_bits = read_csv_bits(file)
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

        chip1_samples, chip2_samples = [], []

        for i in range(1, SAMPLES + 1):
            file = os.path.join(folder, f"{folder}_{i}.csv")
            if not os.path.exists(file):
                print(f"Missing: {file}")
                return
            full_bits = read_csv_bits(file)
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
