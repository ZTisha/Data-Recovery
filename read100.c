/*
Read 100 power-up states from two 23A1024 SRAM chips using segmented addressing
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
#include <gpiod.h>

#include "spi23x1024.c"  // Uses 24-bit addressing with segmentation

#define FGEN_GPIO 27  // BCM GPIO27 = physical pin 13
char date[100];
char file_name[150];
volatile int s = 1;

void trigger_function_generator() {
    struct gpiod_chip *chip = gpiod_chip_open_by_name("gpiochip0");
    if (!chip) {
        perror("Failed to open gpiochip0");
        return;
    }

    struct gpiod_line *line = gpiod_chip_get_line(chip, FGEN_GPIO);
    if (!line) {
        perror("Failed to get GPIO line 27");
        gpiod_chip_close(chip);
        return;
    }

    if (gpiod_line_request_output(line, "trigger", 0) < 0) {
        perror("Failed to set GPIO27 as output");
        gpiod_chip_close(chip);
        return;
    }

    gpiod_line_set_value(line, 1);  // HIGH
    usleep(100);                   // 100 µs pulse
    gpiod_line_set_value(line, 0);  // LOW

    gpiod_chip_close(chip);
}

void chip_on(void) {
    usleep(100000);  // 100 ms delay before triggering
    trigger_function_generator();

    if (s <= 100) {
        printf("Starting sample %d...\n", s);

        snprintf(file_name, sizeof(file_name), "%s_%d.csv", date, s);
        FILE *file = fopen(file_name, "w");
        if (!file) {
            perror("File open failed");
            return;
        }

        fprintf(file, "Chip,Segment,Address,Byte\n");

        // -------- CHIP 1 --------
        usleep(200000);  // Allow Vcc to stabilize before SPI
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
        usleep(200000);  // Allow Vcc to stabilize before SPI
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
        printf("✅ Done sample %d\n", s);
        s++;
    } else {
        printf("✅ Completed all 100 samples.\n");
    }
}

int main() {
    printf("What is today's date? (Use format MM_DD_YY): ");
    scanf("%99s", date);
    mkdir(date, 0777);
    chdir(date);

    for (int i = 0; i < 100; i++) {
        chip_on();
        usleep(100000);  // 100 ms between samples
    }

    return 0;
}
