#include <Arduino.h>
#include <wrapper.h>
#include <array>
#include <stdio.h>

#include "wrapper.h"

// Using Serial1 for hardware UART communication
#define HAND_SERIAL Serial1
const int HAND_BAUD = 460800;
AHWrapper wrapper = AHWrapper(0x50, HAND_BAUD);

std::array<float, 6> cmd;

void setup() {
  Serial.begin(460800);
  HAND_SERIAL.begin(HAND_BAUD);

  for (int i = 0; i < 6; ++i) {
    cmd[i] = 0.0f;
  }
  
  // Wait for hand connection
  bool connecting = true;
  while (connecting && (millis() < 5000)) {
    int connect = wrapper.connect();
    if (connect != 0) {
      Serial.println("Looking for hand...");
      delay(100);
    } else {
      connecting = false;
      Serial.println("Successfully connected to hand!\n");
    }
  }

  if (connecting) {
    Serial.println("Failed to connect to hand. Exiting...");
    while(1);
  }
  digitalWrite(LED_BUILTIN, HIGH);
}

void loop() {    

  // for each finger
  for (int i = 0; i < 5; ++i) {
    // close specified finger
    for (int j = 0; j < 100; j += 10) {
      cmd[i] = float(j);
      wrapper.read_write_once(cmd, POSITION, 0);
      delay(10);
    }
    // open specified finger
    for (int j = 100; j > 0; j-=10) {
      cmd[i] = float(j);
      wrapper.read_write_once(cmd, POSITION, 0);
      delay(10);
    }
  }

  if (millis() > 100000) {
    close_serial();
    while(1);
  }

}

