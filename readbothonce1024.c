// readbothonce1024.c – Reads both 23A1024 chips with segment-based addressing into test.csv

#include <stdio.h>
#include <errno.h>
#include <stdint.h>
#include <linux/spi/spidev.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <string.h>
#include <inttypes.h>

#include "spi23x1024.c"  // Modified: use updated segmented SPI driver

#define FILE_NAME "test"
#define SPI_DEVICE1 "/dev/spidev0.0"
#define SPI_DEVICE2 "/dev/spidev0.1"

extern void spi_set_device(const char *device);  // Needed to switch active chip

int main() {
    FILE *file = fopen(FILE_NAME ".csv", "w");
    if (!file) {
        perror("Failed to create output file");
        return 1;
    }

    fprintf(file, "Address,Word\n");

    // ---------- CHIP 1 ----------
    spi_set_device(SPI_DEVICE1);
    spi_init();

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            uint32_t absolute = compute_address(seg, offset);
            uint8_t val = spi_read_byte(seg, offset);
            fprintf(file, "%05" PRIx32 ",%02" PRIx8 "\n", absolute, val);  // Modified: 24-bit address output
        }
    }

    spi_close();

    // ---------- CHIP 2 ----------
    spi_set_device(SPI_DEVICE2);
    spi_init();

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            uint32_t absolute = compute_address(seg, offset);
            uint8_t val = spi_read_byte(seg, offset);
            fprintf(file, "%05" PRIx32 ",%02" PRIx8 "\n", absolute, val);
        }
    }

    spi_close();
    fclose(file);

    printf("Done reading both chips. Output file is %s.csv\n", FILE_NAME);
    return 0;
}
