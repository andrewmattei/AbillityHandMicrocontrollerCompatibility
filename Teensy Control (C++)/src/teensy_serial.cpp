#include <teensy_serial.h>
#include <Arduino.h>

#define HAND_SERIAL Serial1

int autoconnect_serial(const uint32_t &baud_rate) {
    HAND_SERIAL.begin(baud_rate);
    unsigned long start_time = millis();
    while (!HAND_SERIAL) {
        if (millis() - start_time > 5000) { 
            return -1; 
        }
    }
    return 0;
}

int serial_write(uint8_t *data, uint16_t &size) {
    if (!HAND_SERIAL) {
        return -1;
    }

    size_t bytes_written = HAND_SERIAL.write((const uint8_t *)data, (size_t)size);
    return (int)bytes_written;
}

int read_serial(uint8_t *readbuf, uint16_t &bufsize) {
    if (!HAND_SERIAL) return -1;

    int bytes_available = HAND_SERIAL.available();
    if (bytes_available <= 0) return 0;

    size_t to_read = (bytes_available > bufsize) ? bufsize : bytes_available;
    return HAND_SERIAL.readBytes(readbuf, to_read);
}

void close_serial(void) {
  HAND_SERIAL.end();
}