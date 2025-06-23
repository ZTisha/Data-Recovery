import os
import csv
from PIL import Image

def read_csv_dual_chip(filename):
    chip1_bits = []
    chip2_bits = []

    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip header
        for row in csvreader:
            address, byte = row
            address = int(address)
            byte = bin(int(byte, 16))[2:].zfill(8)

            if address <= 131070:
                chip1_bits.extend([int(b) for b in byte])
            elif address <= 262140:
                chip2_bits.extend([int(b) for b in byte])
    return chip1_bits, chip2_bits

def create_recovery(votes, width, height): 
    img = Image.new('RGB', (width, height), color='white')
    for i, vote in enumerate(votes):
        pixel_value = 255 if vote == 0 else 0 if vote == 1 else 128
        x, y = i % width, i // width
        if y < height:
            img.putpixel((x, y), (pixel_value, pixel_value, pixel_value))
    return img

def maj_fpu_voting(aged_list, new_list):
    vote_result = []
    for a, n in zip(aged_list, new_list):
        diff = a - n
        if diff < 0:
            vote_result.append(1)
        elif diff > 0:
            vote_result.append(0)
        else:
            vote_result.append(2)
    return vote_result

def compare_aging(votes, aging_data):
    shared_set = []
    match_count = 0
    for v, a in zip(votes, aging_data):
        if v == a:
            shared_set.append(v)
            match_count += 1
        else:
            shared_set.append(2)
    return match_count / len(votes), shared_set

def compare_segments_to_reference(votes, ref_bits, segment_size=65536):
    segment_results = []
    for i in range(16):
        start = i * segment_size
        end = start + segment_size
        segment = votes[start:end]
        correct = sum([1 for a, b in zip(segment, ref_bits) if a == b])
        accuracy = correct / segment_size
        segment_results.append(accuracy)
    return segment_results

def read_reference_csv(filename):
    bits = []
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            _, byte = row
            byte_bits = bin(int(byte, 16))[2:].zfill(8)
            bits.extend([int(b) for b in byte_bits])
    return bits

def main():
    try:
        vote_list = []
        prevdir = os.getcwd()

        while True:
            input_dir = input("Enter the folder name for NEW power-up states (e.g., 06_20_25M): ").strip()
            if not os.path.exists(input_dir):
                raise FileNotFoundError("This directory does not exist.")

            chip_id = input("Select the Chip. (1 or 2): ").strip()

            new_bitlists = []
            for i in range(1, 26):
                file_path = f"{input_dir}_{i}.csv"
                chip1, chip2 = read_csv_dual_chip(file_path)
                new_bitlists.append(chip2 if chip_id == '2' else chip1)

            target_dir = input("Enter the folder name for AGED power-up states (e.g., 06_21_25M): ").strip()
            if not os.path.exists(target_dir):
                raise FileNotFoundError("This directory does not exist.")

            aged_bitlists = []
            for i in range(1, 26):
                file_path = f"{target_dir}_{i}.csv"
                chip1, chip2 = read_csv_dual_chip(file_path)
                aged_bitlists.append(chip2 if chip_id == '2' else chip1)

            new_weight = [sum(bits) for bits in zip(*new_bitlists)]
            aged_weight = [sum(bits) for bits in zip(*aged_bitlists)]

            vote_list.append(maj_fpu_voting(aged_weight, new_weight))

            cont = input("Would you like to add another chip’s data for composite recovery? (y/n): ").strip().lower()
            if cont != 'y':
                break

        new_votes = []
        for bits in zip(*vote_list):
            if bits.count(0) > bits.count(1):
                new_votes.append(0)
            elif bits.count(1) > bits.count(0):
                new_votes.append(1)
            else:
                new_votes.append(2)

        if not os.path.exists('RECOVER_BMPs'):
            os.makedirs('RECOVER_BMPs')

        aging_data = read_reference_csv('Aubie.csv')
        recovery, shared = compare_aging(new_votes, aging_data)

        # Segment-wise comparison
        segment_scores = compare_segments_to_reference(new_votes, aging_data)

        print("\n📊 Segment-wise Recovery Rates:")
        for i, score in enumerate(segment_scores):
            print(f"  Segment {i+1:02}: {score:.4f}")

        width, height = 1024, 1024
        recovered_bmp = create_recovery(new_votes, width, height)
        recovered_bmp.show()

        save_name = input("Save bitmap PNG as (e.g., type 'dog' for 'dogrecovered.png'): ").strip()
        recovered_bmp.save(os.path.join('RECOVER_BMPs', f"{save_name}recovered.png"))

        print(f"✅ Data recovery completed. Recovery rate: {recovery:.4f}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.chdir(os.getcwd())

if __name__ == "__main__":
    main()
