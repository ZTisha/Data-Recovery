import csv

def read_csv_dual_chip(filename):
    chip1_bits = []
    chip2_bits = []

    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for row in reader:
            address, byte = row
            address = int(address)
            bin_str = bin(int(byte, 16))[2:].zfill(8)
            bits = [int(b) for b in bin_str]

            if address <= 131070:
                chip1_bits.extend(bits)
            elif address <= 262140:
                chip2_bits.extend(bits)
    return chip1_bits, chip2_bits

def read_reference_bits(filename):
    bits = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            _, byte = row
            bin_str = bin(int(byte, 16))[2:].zfill(8)
            bits.extend([int(b) for b in bin_str])
    return bits

def compare_segments(read_bits, written_bits, segment_size=65536):
    similarity_scores = []
    for i in range(16):
        start = i * segment_size
        end = start + segment_size
        segment = read_bits[start:end]
        matches = sum([1 for a, b in zip(segment, written_bits) if a == b])
        similarity = matches / segment_size
        similarity_scores.append(similarity)
    return similarity_scores

# === MAIN ===
read_file = input("Enter the filename of the READ data CSV (e.g., 6_20_25M.csv): ").strip()
chip_select = input("Select chip to evaluate (1 or 2): ").strip()

chip1, chip2 = read_csv_dual_chip(read_file)
written_bits = read_reference_bits('Aubie.csv')  # expected written pattern

selected_chip_bits = chip1 if chip_select == '1' else chip2
segment_scores = compare_segments(selected_chip_bits, written_bits)

print(f"\n📊 Segment-wise Similarity (READ vs WRITTEN) for Chip {chip_select}:")
for i, score in enumerate(segment_scores):
    print(f"  Segment {i+1:02}: {score:.4f}")
