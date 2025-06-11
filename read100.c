/*
 Read 100 power-up states from two 23A1024 SRAM chips using segmented addressing
 with a rock-solid 100 µs trigger via libgpiod.
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

#include "spi23x1024.c"  // Your existing SPI segmentation driver

#define FGEN_GPIO     27      // BCM pin number for trigger
#define TOTAL_SAMPLES 100

// libgpiod globals
static struct gpiod_chip *g_chip = NULL;
static struct gpiod_line *g_line = NULL;

char date[100];
char file_name[150];
volatile int s = 1;

// ----------------------------------------------------------------------------
// Initialize libgpiod once at program start
// ----------------------------------------------------------------------------
static void init_trigger_gpio(void) {
    g_chip = gpiod_chip_open_by_name("gpiochip0");
    if (!g_chip) {
        perror("gpiod_chip_open_by_name");
        exit(1);
    }
    g_line = gpiod_chip_get_line(g_chip, FGEN_GPIO);
    if (!g_line) {
        perror("gpiod_chip_get_line");
        exit(1);
    }
    if (gpiod_line_request_output(g_line, "fgen_trigger", 0) < 0) {
        perror("gpiod_line_request_output");
        exit(1);
    }
}

// ----------------------------------------------------------------------------
// Clean up libgpiod on exit
// ----------------------------------------------------------------------------
static void cleanup_trigger_gpio(void) {
    if (g_line)   gpiod_line_release(g_line);
    if (g_chip)   gpiod_chip_close(g_chip);
}

// ----------------------------------------------------------------------------
// Fire a clean 100 µs trigger pulse
// ----------------------------------------------------------------------------
static void trigger_function_generator(void) {
    gpiod_line_set_value(g_line, 1);
    usleep(100);              // 100 µs HIGH
    gpiod_line_set_value(g_line, 0);
}

// ----------------------------------------------------------------------------
// Take one “shot” at reading both SRAM chips
// ----------------------------------------------------------------------------
void chip_on(void) {
    usleep(100000);           // 100 ms settle before trigger
    trigger_function_generator();

    if (s <= TOTAL_SAMPLES) {
        printf("Starting sample %d...\n", s);
        snprintf(file_name, sizeof(file_name), "%s_%d.csv", date, s);
        FILE *file = fopen(file_name, "w");
        if (!file) { perror("File open failed"); return; }
        fprintf(file, "Chip,Segment,Address,Byte\n");

        // --- CHIP 1 ---
        usleep(200000);
        spi_set_device("/dev/spidev0.0");
        spi_init();
        spi_enable_sequential_mode();

        for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
            usleep(10000);
            int is_zero = 1;
            for (uint16_t off = 0; off < SEGMENT_SIZE; off++) {
                uint8_t val = spi_read_byte(seg, off);
                if (val) is_zero = 0;
                uint32_t abs = compute_address(seg, off);
                fprintf(file, "1,%u,%06" PRIx32 ",%02" PRIx8 "\n", seg, abs, val);
            }
            if (is_zero) printf("⚠️  All-zero segment: sample %d, chip 1, segment %d\n", s, seg);
        }
        spi_close();

        // --- CHIP 2 ---
        usleep(200000);
        spi_set_device("/dev/spidev0.1");
        spi_init();
        spi_enable_sequential_mode();

        for (uint8_t seg = 0; seg < MAX_SEGMENTS; seg++) {
            usleep(10000);
            int is_zero = 1;
            for (uint16_t off = 0; off < SEGMENT_SIZE; off++) {
                uint8_t val = spi_read_byte(seg, off);
                if (val) is_zero = 0;
                uint32_t abs = compute_address(seg, off);
                fprintf(file, "2,%u,%06" PRIx32 ",%02" PRIx8 "\n", seg, abs, val);
            }
            if (is_zero) printf("⚠️  All-zero segment: sample %d, chip 2, segment %d\n", s, seg);
        }
        spi_close();

        fclose(file);
        printf("✅ Done sample %d\n", s);
        s++;
    } else {
        printf("✅ Completed all %d samples.\n", TOTAL_SAMPLES);
    }
}

// ----------------------------------------------------------------------------
// Main: setup, loop, cleanup
// ----------------------------------------------------------------------------
int main() {
    // 1) Ask for date and prepare directory
    printf("What is today's date? (MM_DD_YY): ");
    scanf("%99s", date);
    mkdir(date, 0777);
    chdir(date);

    // 2) Initialize the GPIO trigger once
    init_trigger_gpio();

    // 3) Run each sample
    for (int i = 0; i < TOTAL_SAMPLES; i++) {
        chip_on();
        usleep(100000);
    }

    // 4) Clean up before exit
    cleanup_trigger_gpio();
    return 0;
}
