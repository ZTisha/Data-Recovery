/*
Read 200 power-up states from two 23A1024 SRAM chips using segmented addressing
*/

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
#include <sys/stat.h>

#include "spi23x1024.c"  // Uses 24-bit addressing with segmentation

#define FGEN_PIN 0
char date[100];
char file_name[150];
volatile int s = 1;

void chip_on(void) {
    usleep(100000);  // 100 ms delay before beginning sample

    // GPIO trigger pulse to function generator
    system("gpio -g mode 27 out");
    system("gpio -g write 27 1");
    usleep(100);  // 100 µs pulse
    system("gpio -g write 27 0");

    if (s <= 200) {
        printf("Starting %d...\n", s);

        snprintf(file_name, sizeof(file_name), "%s_%d.csv", date, s);
        FILE *file = fopen(file_name, "w");

        if (!file) {
            perror("File open failed");
            return;
        }

        fprintf(file, "Chip,Segment,Address,Byte\n");

        // -------- CHIP 1 --------
        usleep(200000);  // Allow Vcc to stabilize before SPI communication
        spi_set_device("/dev/spidev0.0");
        spi_init();
        spi_enable_sequential_mode();

        for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
            usleep(10000);  // 10 ms delay between segments
            int is_zero = 1;

            for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
                uint8_t val = spi_read_byte(seg, offset);
                if (val != 0x00) is_zero = 0;

                uint32_t abs_addr = compute_address(seg, offset);
                fprintf(file, "1,%u,%06" PRIx32 ",%02" PRIx8 "\n", seg, abs_addr, val);
            }

            if (is_zero) {
                printf("⚠️  All-zero segment: sample %d, chip 1, segment %d\n", s, seg);
            }
        }
        spi_close();

        // -------- CHIP 2 --------
        usleep(200000);  // Allow Vcc to stabilize before SPI communication
        spi_set_device("/dev/spidev0.1");
        spi_init();
        spi_enable_sequential_mode();

        for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
            usleep(10000);  // 10 ms delay between segments
            int is_zero = 1;

            for (uint16_t offset = 0; offset < SEGMENT_SIZE; offset++) {
                uint8_t val = spi_read_byte(seg, offset);
                if (val != 0x00) is_zero = 0;

                uint32_t abs_addr = compute_address(seg, offset);
                fprintf(file, "2,%u,%06" PRIx32 ",%02" PRIx8 "\n", seg, abs_addr, val);
            }

            if (is_zero) {
                printf("⚠️  All-zero segment: sample %d, chip 2, segment %d\n", s, seg);
            }
        }
        spi_close();

        fclose(file);
        printf("Done sample %d!\n", s);
        s++;
    } else {
        printf("Completed all 200 samples.\n");
    }
}

int main() {
    printf("What is today's date? (Use format MM_DD_YY): ");
    scanf("%99s", date);
    mkdir(date, 0777);
    chdir(date);

    for (int i = 0; i < 200; i++) {
        chip_on();  // Trigger manually instead of relying on ISR
        usleep(100000);  // 100 ms delay between samples
    }

    return 0;
}
