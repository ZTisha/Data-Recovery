## adapted from BewareVoting.py by Gaines Odom ##

import os
import csv
from PIL import Image

# === CONFIG ===
WORD_SIZE_BITS = 8
SEGMENT_BITS = 8192 * 8  # 8192 bytes = 65536 bits per segment

# === Read CSV bits ===
def read_csv_bits(filepath):
    bits = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            _, byte = row
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(WORD_SIZE_BITS)])
    return bits

# === Read reference bits ===
def read_reference_csv(filename):
    bits = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            _, byte = row
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(8)])
    return bits

# === Sign-based voting for one segment ===
def sign_based_voting(new_bitlists, aged_bitlists):
    new_weight = [sum(bits) for bits in zip(*new_bitlists)]
    aged_weight = [sum(bits) for bits in zip(*aged_bitlists)]
    weights = [aged - new for aged, new in zip(aged_weight, new_weight)]

    prd = []
    for w in weights:
        if w > 0:
            prd.append(0)
        elif w < 0:
            prd.append(1)
        else:
            prd.append(2)
    return prd

# === Cross-PRD majority voting ===
def cross_prd_voting(prds):
    final_votes = []
    for bits in zip(*prds):
        zeros = bits.count(0)
        ones = bits.count(1)
        if zeros > ones:
            final_votes.append(0)
        elif ones > zeros:
            final_votes.append(1)
        else:
            final_votes.append(2)
    return final_votes

# === Bitmap Generation ===
def create_recovery_bitmap(bits, width=256, height=256):
    img = Image.new('RGB', (width, height), 'white')
    for i, bit in enumerate(bits):
        pixel_value = 0 if bit == 1 else 255 if bit == 0 else 128
        x, y = i % width, i // width
        if y < height:
            img.putpixel((x, y), (pixel_value, pixel_value, pixel_value))
    return img

# === MAIN ===
def main():
    # ✅ User just types the base names; _SEGMENTS is added automatically
    ipu_base = input("Enter BASE folder name for Initial Power-Up States: ").strip()
    ipu_dir = ipu_base + "_SEGMENTS"
    if not os.path.exists(ipu_dir):
        print(f"❌ Folder '{ipu_dir}' does not exist.")
        return

    apu_base = input("Enter BASE folder name for Aged Power-Up States: ").strip()
    apu_dir = apu_base + "_SEGMENTS"
    if not os.path.exists(apu_dir):
        print(f"❌ Folder '{apu_dir}' does not exist.")
        return

    ipu_files = os.listdir(ipu_dir)
    apu_files = os.listdir(apu_dir)

    seg_input = input("Enter segments to use (e.g., 2,4,7) or ALL: ").strip()
    if seg_input.lower() == "all":
        selected_segments = list(range(1, 33))   # ✅ NOW 32 SEGMENTS!
    else:
        selected_segments = [int(s.strip()) for s in seg_input.split(",")]

    print(f"\nSelected segments: {selected_segments}\n")

    prds = []

    for seg_num in selected_segments:
        ipu_seg_files = [f for f in ipu_files if f"_Segment{seg_num}.csv" in f]
        apu_seg_files = [f for f in apu_files if f"_Segment{seg_num}.csv" in f]

        if len(ipu_seg_files) == 0 or len(apu_seg_files) == 0:
            print(f"⚠️ Segment {seg_num}: Missing files in IPU or APU folder.")
            continue

        #print(f"Segment {seg_num}: {len(ipu_seg_files)} IPU files, {len(apu_seg_files)} APU files")

        new_bitlists = []
        aged_bitlists = []

        for f in ipu_seg_files:
            bits = read_csv_bits(os.path.join(ipu_dir, f))
            if len(bits) != SEGMENT_BITS:
                print(f"⚠️ IPU file {f} has {len(bits)} bits, expected {SEGMENT_BITS}")
            new_bitlists.append(bits)

        for f in apu_seg_files:
            bits = read_csv_bits(os.path.join(apu_dir, f))
            if len(bits) != SEGMENT_BITS:
                print(f"⚠️ APU file {f} has {len(bits)} bits, expected {SEGMENT_BITS}")
            aged_bitlists.append(bits)

        prd = sign_based_voting(new_bitlists, aged_bitlists)
        prds.append(prd)

    if len(prds) == 0:
        print("\n❌ No PRDs generated. Exiting.")
        return

    print(f"\nCombining {len(prds)} PRDs using cross-segment majority voting...")
    final_votes = cross_prd_voting(prds)

    # === Load reference ===
    if not os.path.exists("AubieImage.csv"):
        print("\n❌ Reference file 'AubieImage.csv' not found.")
        return

    ref_bits = read_reference_csv("AubieImage.csv")
    if len(ref_bits) != SEGMENT_BITS:
        print(f"⚠️ Reference image should be 8192 bytes (65536 bits). Found {len(ref_bits)} bits.")

    correct = sum(1 for a, b in zip(final_votes, ref_bits) if a == b)
    accuracy = correct / SEGMENT_BITS

    print(f"\n✅ Final Recovery Accuracy: {accuracy:.4f}")
    recovered_img = create_recovery_bitmap(final_votes)
    recovered_img.show()
    if not os.path.exists("RECOVER_BMPs"):
        os.makedirs("RECOVER_BMPs")
    save_name = input("Save bitmap as (e.g., recovered.png): ").strip()
    if not save_name.lower().endswith('.png'):
        save_name += '.png'
    save_path = os.path.join("RECOVER_BMPs", save_name)
    recovered_img.save(save_path)

    print(f"✅ Bitmap saved to: {save_path}")


if __name__ == "__main__":
    main()
