import os
import csv

# === CONFIG ===
SEGMENT_SIZE_BYTES = 8192           # Each segment = 8192 bytes
WORD_SIZE_BITS = 8                  # Each word/byte = 8 bits
SEGMENT_BITS = SEGMENT_SIZE_BYTES * WORD_SIZE_BITS  # 65536 bits per segment
TOTAL_SEGMENTS = 32                 # Treat full file as 32 segments

# === Read all sample files ===
def get_sample_files(directory):
    return sorted([
        f for f in os.listdir(directory)
        if f.endswith(".csv") and os.path.isfile(os.path.join(directory, f))
    ])

# === Read bits positionally ===
def read_csv_bits(filepath):
    bits = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            _, byte = row
            bits.extend([int(b) for b in bin(int(byte, 16))[2:].zfill(WORD_SIZE_BITS)])
    return bits

# === Save bits as CSV ===
def write_segment_csv(bits, output_filename):
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Address', 'Word'])
        for i in range(0, len(bits), WORD_SIZE_BITS):
            address = i // WORD_SIZE_BITS
            byte_bits = bits[i:i+WORD_SIZE_BITS]
            byte_hex = hex(int(''.join(str(b) for b in byte_bits), 2))[2:].upper().zfill(2)
            writer.writerow([hex(address)[2:].upper().zfill(4), byte_hex])

# === MAIN ===
def main():
    input_dir = input("Enter folder name containing your samples: ").strip()
    if not os.path.exists(input_dir):
        print("❌ Input folder does not exist.")
        return

    OUTPUT_DIR = input_dir + "_SEGMENTS"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    files = get_sample_files(input_dir)
    print(f"✅ Found {len(files)} sample files in '{input_dir}'")

    for file in files:
        full_path = os.path.join(input_dir, file)
        full_bits = read_csv_bits(full_path)

        sample_name = os.path.splitext(file)[0]

        # === Split into 32 segments ===
        segments = []
        for i in range(TOTAL_SEGMENTS):
            seg = full_bits[i*SEGMENT_BITS : (i+1)*SEGMENT_BITS]
            if len(seg) != SEGMENT_BITS:
                print(f"⚠️ Warning: Segment {i+1} has {len(seg)} bits, expected {SEGMENT_BITS}")
            segments.append(seg)

        for idx, seg_bits in enumerate(segments, start=1):
            out_name = f"{sample_name}_Segment{idx}.csv"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            write_segment_csv(seg_bits, out_path)

    print(f"\n✅ Segments saved to '{OUTPUT_DIR}' folder.")

if __name__ == "__main__":
    main()
