// write2chips1024.c – Writes to all 16 virtual 64Kbit segments in two 23A1024 chips

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "spi23x1024.c"  // Modified: include updated segmented SPI driver

// Modified: Define two device paths
#define SPI_DEVICE1 "/dev/spidev0.0"
#define SPI_DEVICE2 "/dev/spidev0.1"

extern void spi_set_device(const char *device);  // Add declaration for switching device

int main() {
    FILE *file = fopen("WrittenImage.csv", "r");
    if (!file) {
        perror("Failed to open CSV");
        return 1;
    }

    // Discard header line (same as before)
    char line[32];
    if (!fgets(line, sizeof(line), file)) {
        perror("Failed to read header");
        fclose(file);
        return 1;
    }

    // Modified: Buffer only for 8KB input, reused across all segments
    uint8_t data[SEGMENT_SIZE] = {0};

    // Modified: read only the first 8192 address-byte pairs
    int idx = 0;
    while (fgets(line, sizeof(line), file) && idx < SEGMENT_SIZE) {
        unsigned int address, byte;
        if (sscanf(line, "%x,%x", &address, &byte) == 2) {
            data[idx++] = (uint8_t)byte;
        }
    }
    fclose(file);

    // ---------- CHIP 1 ----------
    spi_set_device(SPI_DEVICE1);     // Modified: Select chip 1
    spi_init();

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            uint8_t value = data[offset];  // Modified: repeat same data buffer
            spi_write_byte(seg, offset, value);
        }
        printf("Chip 1 – Segment %u written successfully\n", seg);
    }

    spi_close();

    // ---------- CHIP 2 ----------
    spi_set_device(SPI_DEVICE2);     // Modified: Select chip 2
    spi_init();

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            uint8_t value = data[offset];  // Modified: repeat same data buffer
            spi_write_byte(seg, offset, value);
        }
        printf("Chip 2 – Segment %u written successfully\n", seg);
    }

    spi_close();
    printf("Done writing all segments to both chips.\n");
    return 0;
}
