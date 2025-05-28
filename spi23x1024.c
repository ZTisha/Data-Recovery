// spi23x1024.c – Segmented access driver for Microchip 23A1024

/*
SPI API for the 23K640 SRAM chip

supports reading and writing in "Byte Operation"
does not support reading status register
does not support "Page Operation" or "Sequential Operation"
does not support writing to status register
Author: Amaar Ebrahim
Email: aae0008@auburn.edu

Modified by: Gaines Odom
Email: gaines.odom@auburn.edu

Modified by: Zakia Tamanna Tisha
Email: zakia.tisha@auburn.edu

*/

#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

// Constants and Settings

#define SPI_READ_CMD     0x03     // Read command (same as 23A640)
#define SPI_WRITE_CMD    0x02     // Write command (same as 23A640)
#define SPI_MODE_REG_R   0x05     // Read Mode Register (RDMR)
#define SPI_MODE_REG_W   0x01     // Write Mode Register (WRMR)

#define TOTAL_MEM_BYTES  0x20000  // 128 KB total memory in 23A1024
#define SEGMENT_SIZE     0x2000   // 8 KB (64 Kbit) segment size — same as 23A640
#define MAX_SEGMENTS     (TOTAL_MEM_BYTES / SEGMENT_SIZE)  // 16 segments of 8 KB each

#define SPI_DEVICE       "/dev/spidev0.0"
#define SPI_MAX_SPEED_HZ 20000000
#define SPI_BITS_PER_WORD 8


// Global Variables

static int spi_fd;
static uint32_t spi_speed = 5000000;

// Modified: Selected device path (default to SPI0.0)
static const char *selected_device_path = "/dev/spidev0.0";

// Modified: Allow selecting device before spi_init
void spi_set_device(const char *device) {
    selected_device_path = device;
}


// SPI Initialization

void spi_enable_sequential_mode() {
    uint8_t tx[2] = { SPI_MODE_REG_W, 0x40 }; // 0x40 = Sequential mode
    struct spi_ioc_transfer xfer = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = 0,
        .len = 2,
        .speed_hz = spi_speed,
        .bits_per_word = SPI_BITS_PER_WORD,
        .delay_usecs = 0
    };
    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        perror("Failed to enable sequential mode");
        exit(EXIT_FAILURE);
    }
}

void spi_init() {
    spi_fd = open(selected_device_path, O_RDWR);
    if (spi_fd < 0) {
        perror("SPI open");
        exit(EXIT_FAILURE);
    }

    uint8_t mode = SPI_MODE_0;
    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0 ||
        ioctl(spi_fd, SPI_IOC_RD_MODE, &mode) < 0) {
        perror("SPI set mode");
        close(spi_fd);
        exit(EXIT_FAILURE);
    }

    if (ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &spi_speed) < 0 ||
        ioctl(spi_fd, SPI_IOC_RD_MAX_SPEED_HZ, &spi_speed) < 0) {
        perror("SPI set speed");
        close(spi_fd);
        exit(EXIT_FAILURE);
    }

    if (ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &(uint8_t){SPI_BITS_PER_WORD}) < 0) {
        perror("SPI set bits per word");
        close(spi_fd);
        exit(EXIT_FAILURE);
    }
spi_enable_sequential_mode();  // sequential mode function called
}

void spi_close() {
    close(spi_fd);
}


// Addressing Helpers

uint32_t compute_address(uint8_t segment_id, uint16_t offset) {
    if (segment_id >= MAX_SEGMENTS || offset >= SEGMENT_SIZE) {
        fprintf(stderr, "Invalid segment or offset\n");
        exit(EXIT_FAILURE);
    }
    return (segment_id * SEGMENT_SIZE) + offset;
}

// SPI Memory Access

void spi_write_byte(uint8_t segment_id, uint16_t offset, uint8_t data) {
    uint32_t address = compute_address(segment_id, offset);

    uint8_t tx[5] = {
        SPI_WRITE_CMD,                 // Modified: use macro
        (address >> 16) & 0xFF,
        (address >> 8) & 0xFF,
        address & 0xFF,
        data
    };

    struct spi_ioc_transfer xfer = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = 0,
        .len = 5,                      // Modified: 5 bytes for 24-bit address + data
        .speed_hz = spi_speed,
        .bits_per_word = SPI_BITS_PER_WORD,
        .delay_usecs = 0
    };

    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        perror("SPI write_byte");
        exit(EXIT_FAILURE);
    }
}

// Modified: Use 24-bit addressing and named command macros
uint8_t spi_read_byte(uint8_t segment_id, uint16_t offset) {
    uint32_t address = compute_address(segment_id, offset);

    uint8_t tx[5] = {
        SPI_READ_CMD,                  // Modified: use macro
        (address >> 16) & 0xFF,
        (address >> 8) & 0xFF,
        address & 0xFF,
        0xFF                           // Dummy byte for receiving
    };
    uint8_t rx[5] = {0};

    struct spi_ioc_transfer xfer = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = (unsigned long)rx,
        .len = 5,                      // Modified: 5 bytes total
        .speed_hz = spi_speed,
        .bits_per_word = SPI_BITS_PER_WORD,
        .delay_usecs = 0
    };

    if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &xfer) < 0) {
        perror("SPI read_byte");
        exit(EXIT_FAILURE);
    }

    return rx[4];  // Data byte received
}
