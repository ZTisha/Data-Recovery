
import os
import csv
from PIL import Image
import numpy as np
from math import isqrt, ceil

# Constants
CHIP_WIDTH = 1024
CHIP_HEIGHT = 1024
WORD_SIZE = 8
SEGMENT_BITS = 8192 * 8
SEGMENT_WIDTH = 256
SEGMENT_HEIGHT = 256
GRID_ROWS = 4
GRID_COLS = 4
CHIP_BITS = SEGMENT_BITS * 16

def read_csv_bits(filepath):
    bits = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            _, byte = row[:2]
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(WORD_SIZE)])
    return bits

def split_chip_bits(full_bits):
    chip1_bits = full_bits[0:CHIP_BITS]
    chip2_bits = full_bits[CHIP_BITS:CHIP_BITS*2]
    return chip1_bits, chip2_bits

def extract_segments(bits):
    return [bits[i*SEGMENT_BITS:(i+1)*SEGMENT_BITS] for i in range(16)]

def create_segment_bitmap(bits):
    img = Image.new('1', (SEGMENT_WIDTH, SEGMENT_HEIGHT), color=0)
    for y in range(SEGMENT_HEIGHT):
        for x in range(SEGMENT_WIDTH):
            idx = y * SEGMENT_WIDTH + x
            img.putpixel((x, y), 1 - bits[idx])
    return img

def create_segment_grayscale(avg_bits):
    img = Image.new('L', (SEGMENT_WIDTH, SEGMENT_HEIGHT), color=255)
    for y in range(SEGMENT_HEIGHT):
        for x in range(SEGMENT_WIDTH):
            idx = y * SEGMENT_WIDTH + x
            img.putpixel((x, y), int(avg_bits[idx]))
    return img

def create_tiled_bitmap(segments, mode='1'):
    img_mode = '1' if mode == '1' else 'RGB'
    full_img = Image.new(img_mode, (1024, 1024), color=0)
    for i, seg in enumerate(segments):
        x = (i % GRID_COLS) * SEGMENT_WIDTH
        y = (i // GRID_COLS) * SEGMENT_HEIGHT
        img = seg if isinstance(seg, Image.Image) else create_segment_bitmap(seg)
        full_img.paste(img, (x, y))
    return full_img

def average_segments(segment_samples):
    arrays = [np.array(seg) for seg in segment_samples]
    accumulation = np.sum(arrays, axis=0)
    avg = (255 - (accumulation * 255 / len(segment_samples))).astype(np.uint8)
    return avg

def main():
    print("\nSelect Bitmap Mode:")
    print("1. Bitmap of Chip 1 or Chip 2")
    print("2. Overlay Bitmap of Both Chips")
    print("3. General Image Bitmap from CSV (any size)")
    choice = input("Enter option (1/2/3): ").strip()

    outdir = "BITMAPS"
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if choice == "1":
        folder = input("Enter folder name: ").strip()
        chip_select = input("Select chip (1 or 2): ").strip()

        print("\nSample Selection:")
        print("1. All available samples")
        print("2. One specific sample")
        print("3. A range of samples")
        sample_mode = input("Choose an option (1/2/3): ").strip()

        if not os.path.exists(folder):
            print("Folder not found.")
            return

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

        all_chip_segments = [[] for _ in range(16)]

        for file in csv_files:
            full_path = os.path.join(folder, file)
            full_bits = read_csv_bits(full_path)
            chip1, chip2 = split_chip_bits(full_bits)
            chip_bits = chip1 if chip_select == "1" else chip2
            segments = extract_segments(chip_bits)
            for i in range(16):
                all_chip_segments[i].append(segments[i])

        if len(csv_files) == 1:
            # Single sample: tile directly
            tiled = create_tiled_bitmap([s[0] for s in all_chip_segments], mode='1')
        else:
            # Average multiple
            segment_imgs = [create_segment_grayscale(average_segments(s)) for s in all_chip_segments]
            tiled = create_tiled_bitmap(segment_imgs, mode='2')

        outname = f"{folder}_chip{chip_select}_bitmap.png"
        tiled.save(os.path.join(outdir, outname))
        print(f"Bitmap saved to {outdir}/{outname}")

    elif choice == "2":
        folder = input("Enter folder name: ").strip()

        print("\nSample Selection:")
        print("1. All available samples")
        print("2. One specific sample")
        print("3. A range of samples")
        sample_mode = input("Choose an option (1/2/3): ").strip()

        if not os.path.exists(folder):
            print("Folder not found.")
            return

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

        chip1_segs = [[] for _ in range(16)]
        chip2_segs = [[] for _ in range(16)]

        for fname in csv_files:
            full_path = os.path.join(folder, fname)
            bits = read_csv_bits(full_path)
            c1, c2 = split_chip_bits(bits)
            c1_segments = extract_segments(c1)
            c2_segments = extract_segments(c2)
            for i in range(16):
                chip1_segs[i].append(c1_segments[i])
                chip2_segs[i].append(c2_segments[i])

        blended_segments = []
        for i in range(16):
            if len(csv_files) == 1:
                img1 = create_segment_bitmap(chip1_segs[i][0])
                img2 = create_segment_bitmap(chip2_segs[i][0])
            else:
                img1 = create_segment_grayscale(average_segments(chip1_segs[i]))
                img2 = create_segment_grayscale(average_segments(chip2_segs[i]))
            blended = Image.blend(img1.convert("RGB"), img2.convert("RGB"), alpha=0.5)
            blended_segments.append(blended)

        tiled = create_tiled_bitmap(blended_segments, mode='2')
        outname = f"{folder}_overlay_bitmap.png"
        tiled.save(os.path.join(outdir, outname))
        print(f"Overlay bitmap saved to {outdir}/{outname}")

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
        if len(bits) < width * height:
            bits += [0] * (width * height - len(bits))

        img = Image.new('1', (width, height), color=0)
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                img.putpixel((x, y), 1 - bits[idx])
        outname = f"{os.path.splitext(csv_file)[0]}_image_bitmap.png"
        img.save(os.path.join(outdir, outname))
        print(f"Image bitmap saved to {outdir}/{outname}")

    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()
