
# ---------------------------
# adapted from BewareVoting.py from Gaines Odom
# ---------------------------
import os
import csv
from PIL import Image

# ---------------------------
# Get all CSV sample files
# ---------------------------
def get_sample_files(directory):
    return sorted([
        f for f in os.listdir(directory)
        if f.endswith(".csv") and os.path.isfile(os.path.join(directory, f))
    ])

# ---------------------------------------
# Read CSV and split bits for both chips
# ---------------------------------------
CHIP_BITS = 131070 * 8  # 131,070 addresses * 8 bits

def read_csv_dual_chip(filename):
    bits = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for row in reader:
            _, byte = row
            byte_bits = bin(int(byte, 16))[2:].zfill(8)
            bits.extend([int(b) for b in byte_bits])
    chip1_bits = bits[0:CHIP_BITS]
    chip2_bits = bits[CHIP_BITS:CHIP_BITS * 2]
    #print(f"Total bits read: {len(bits)} | Chip1: {len(chip1_bits)} | Chip2: {len(chip2_bits)}")
    return chip1_bits, chip2_bits

# ---------------------------------
# Original sign-based voting
# ---------------------------------
def maj_fpu_voting(aged_weight, new_weight):
    votelist = [0] * len(new_weight)
    newlist = []
    for i in range(len(aged_weight)):
        diff = aged_weight[i] - new_weight[i]
        if diff <= -1:
            votelist[i] -= 1
        elif diff >= 1:
            votelist[i] += 1
    for item in votelist:
        if item < 0:
            newlist.append(1)
        elif item > 0:
            newlist.append(0)
        else:
            newlist.append(2)
    return newlist

# ---------------------------------
# Read reference file bits
# ---------------------------------
def read_reference_csv(filename):
    bits = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            _, byte = row
            byte_bits = bin(int(byte, 16))[2:].zfill(8)
            bits.extend([int(b) for b in byte_bits])
    return bits

# ---------------------------------
# Segment-wise comparison
# ---------------------------------
def compare_segments_to_reference(votes, ref_bits):
    segment_size = len(ref_bits)
    total_segments = len(votes) // segment_size
    results = []
    for i in range(total_segments):
        start = i * segment_size
        end = start + segment_size
        segment = votes[start:end]
        correct = sum(1 for a, b in zip(segment, ref_bits) if a == b)
        accuracy = correct / segment_size
        results.append(accuracy)
    return results

# ---------------------------------
# Generate recovery bitmap
# ---------------------------------
def create_recovery(votes, width, height):
    img = Image.new('RGB', (width, height), color='white')
    for i, vote in enumerate(votes):
        pixel_value = 255 if vote == 0 else 0 if vote == 1 else 128
        x, y = i % width, i // width
        if y < height:
            img.putpixel((x, y), (pixel_value, pixel_value, pixel_value))
    return img

# ---------------------------------
# MAIN PROGRAM
# ---------------------------------
def main():
    try:
        prevdir = os.getcwd()
        vote_list = []
        total_bits = 0

        while True:
            # === NEW states ===
            input_dir = input("Enter folder for NEW power-up states: ").strip()
            if not os.path.exists(input_dir):
                raise FileNotFoundError("Directory does not exist.")
            chip_id = input("Select the Chip (1 or 2): ").strip()
            sample_files = get_sample_files(input_dir)
            if len(sample_files) == 0:
                raise FileNotFoundError("No CSV files found in the NEW directory.")
            print(f"🔎 Found {len(sample_files)} samples in {input_dir}")

            new_bitlists = []
            for fname in sample_files:
                chip1, chip2 = read_csv_dual_chip(os.path.join(input_dir, fname))
                new_bitlists.append(chip2 if chip_id == '2' else chip1)

            # === AGED states ===
            target_dir = input("Enter folder for AGED power-up states: ").strip()
            if not os.path.exists(target_dir):
                raise FileNotFoundError("Directory does not exist.")
            target_files = get_sample_files(target_dir)
            if len(target_files) != len(sample_files):
                raise ValueError("Mismatch in number of samples between NEW and AGED directories.")
            aged_bitlists = []
            for fname in target_files:
                chip1, chip2 = read_csv_dual_chip(os.path.join(target_dir, fname))
                aged_bitlists.append(chip2 if chip_id == '2' else chip1)

            # === Sum bits ===
            new_weight = [sum(bits) for bits in zip(*new_bitlists)]
            aged_weight = [sum(bits) for bits in zip(*aged_bitlists)]

            # === Sign-based voting ===
            differential_votes = maj_fpu_voting(aged_weight, new_weight)
            total_bits += len(differential_votes)
            vote_list.extend(differential_votes)

            cont = input("Add another chip’s data for composite recovery? (y/n): ").strip().lower()
            if cont != 'y':
                break

        # === Load reference ===
        if not os.path.exists("AubieImage.csv"):
            raise FileNotFoundError("Reference file 'AubieImage.csv' not found.")
        ref_bits = read_reference_csv("AubieImage.csv")
        if len(ref_bits) != 65536:
            raise ValueError("AubieImage.csv must contain exactly 8192 bytes (65536 bits).")

        # === Segment-wise comparison ===
        segment_scores = compare_segments_to_reference(vote_list, ref_bits)

        print("\n📊 Segment-wise Recovery Rates:")
        for i, score in enumerate(segment_scores):
            print(f"  Segment {i+1:02}: {score:.4f}")

        # === Save bitmap ===
        if not os.path.exists("RECOVER_BMPs"):
            os.makedirs("RECOVER_BMPs")
        # Note: For huge data, use suitable dimensions. Here, 1024x1024 shown as example
        recovered_bmp = create_recovery(vote_list, 1024, 1024)
        recovered_bmp.show()
        save_name = input("Save bitmap PNG as (e.g., 'dog' for dogrecovered.png): ").strip()
        recovered_bmp.save(os.path.join("RECOVER_BMPs", f"{save_name}recovered.png"))

        print("\n✅ Composite recovery and segment-wise analysis completed.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        os.chdir(prevdir)

if __name__ == "__main__":
    main()
