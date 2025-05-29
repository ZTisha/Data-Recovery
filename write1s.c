// Writes 0x00 to all addresses in both 23A1024 SRAM chips using segmented access

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "spi23x1024.c"  // Uses 24-bit addressing with segmentation

#define SPI_DEVICE1 "/dev/spidev0.0"
#define SPI_DEVICE2 "/dev/spidev0.1"

int main() {
    printf("Writing 0x00 to all bytes in chip 1...\n");
    spi_set_device(SPI_DEVICE1);
    spi_init();
    spi_enable_sequential_mode();  // Ensure proper addressing

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            spi_write_byte(seg, offset, 0xFF);
        }
        printf("  Segment %u written (chip 1)\n", seg);
    }
    spi_close();

    printf("Writing 0x00 to all bytes in chip 2...\n");
    spi_set_device(SPI_DEVICE2);
    spi_init();
    spi_enable_sequential_mode();

    for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
        for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
            spi_write_byte(seg, offset, 0xFF);
        }
        printf("  Segment %u written (chip 2)\n", seg);
    }
    spi_close();

    printf("Done writing 0s to both chips.\n");
    return 0;
}
