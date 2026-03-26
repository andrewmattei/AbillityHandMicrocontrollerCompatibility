#include <Arduino.h>
#include <wrapper.h>
#include <array>
#include <stdio.h>

#include "wrapper.h"

// Using Serial1 for hardware UART communication
#define HAND_SERIAL Serial1
const int HAND_BAUD = 460800;
AHWrapper wrapper = AHWrapper(0x50, HAND_BAUD);
int max_dist;
int delay_fing;
int reply_mode;
std::array<float, 6> cmd;

void print_forces() {

  Serial.println("Forces: ");
  for (int i = 0; i < 5; ++i) {
    Serial.print("Finger " + String(i + 1) + ": ");
    for (int j = 0; j < 6; ++j) {
      Serial.print(wrapper.hand.forces[j + 6*i]);
      Serial.print(" ");
    }
    Serial.println();
  }
  Serial.println();
}

void print_fsr_values() {
  Serial.println("FSR Values: ");
  for (int i = 0; i < 5; ++i) {
    Serial.print("Finger " + String(i + 1) + ": ");
    for (int j = 0; j < 6; ++j) {
      Serial.print(wrapper.hand.fsr[j + 6*i]);
      Serial.print(" ");
    }
    Serial.println();
  }
  Serial.println();
}

void print_positions() {
  Serial.println("Positions: ");
  for (int i = 0; i < 6; ++i) {
    Serial.print(wrapper.hand.pos[i]);
    Serial.print(" ");
  }
  Serial.println();
}

void print_velocities() {
  // Serial.println("Velocities: ");  // Commented out for serial plotter
  for (int i = 0; i < 6; ++i) {
    Serial.print(wrapper.hand.vel[i]);
    Serial.print(" ");
  }
  Serial.println();
}

void setup() {
  Serial.begin(460800);
  HAND_SERIAL.begin(HAND_BAUD);

  for (int i = 0; i < 6; ++i) {
    cmd[i] = 0.0f;
  }

  max_dist = 10;
  delay_fing = 10;
  
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
  reply_mode = millis() % 2;
  for (int i = 0; i < 5; i++) {
    for (int j = 0; j <= 100; j += 2) {
      cmd[i] = float(j);
      wrapper.read_write_once(cmd, POSITION, 1);
      print_velocities();
      // print_forces();
      // print_fsr_values();
      // print_positions();
      delay(10);
    }

    for (int j = 100; j >= 0; j -= 2) {
      cmd[i] = float(j);
      wrapper.read_write_once(cmd, POSITION, 1);
      print_velocities();
      // print_forces();
      // print_fsr_values();
      // print_positions();
      delay(10);
    }
  }

  // wrapper.read_write_once(cmd, POSITION, reply_mode);
  // if (reply_mode == 0) {
  //   print_forces();
  // } else {
  //   print_velocities();
  // }
  // print_forces();
  // // print_positions();
  // print_velocities();
  // delay(100);

  if (millis() > 100000) {
    close_serial();
    while(1);
  }

}
