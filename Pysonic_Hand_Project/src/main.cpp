#include <Arduino.h>
#include <wrapper.h>
#include <array>
#include <stdio.h>

#include "wrapper.h"

// Using Serial1 for hardware UART communication
#define HAND_SERIAL Serial1
const int HAND_BAUD = 460800;
AHWrapper wrapper = AHWrapper(0x50, HAND_BAUD);

// Build a union to hold the by structure and the float structure
union FloatArrayUnion {
  std::array<float, 6> floats;
  char buffer[24];
};


// Setup for python communication
FloatArrayUnion data_packet;
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
    int connect = wrapper.connect("");
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
  
  if (Serial.available() >= 24) {
    Serial.readBytes(data_packet.buffer, 24);

    for (int i = 0; i < 6; ++i) {
      cmd[i] = data_packet.floats[i];
    }
    Serial.print("Received command: ");
    for (int i = 0; i < 6; ++i) {
      Serial.print(cmd[i]);
      Serial.print(" ");
    }

    wrapper.read_write_once(cmd, POSITION, 0);
    Serial.println();
  }







  // if (Serial.available() > 0) {
  //   // Read the entire line of text, until you press 'Enter'
  //   String input = Serial.readStringUntil('\n');
    
  //   // Trim any extra whitespace
  //   input.trim();

  //   // --- Convert String to Number ---
  //   // .toInt() converts the string to an integer.
  //   // If you type "abc", it will result in 0.
  //   // If you need decimal places, use .toFloat()
  //   float number = float(input.toInt());

  //   // Echo the received string and the converted number
  //   Serial.print("Teensy received string: '");
  //   Serial.print(input);
  //   Serial.println("'");
    
  //   Serial.print("Converted to number: ");
  //   Serial.println(number);

  //   // --- Do something with the number ---
  //   long result = number * 2;
  //   Serial.print("Number * 2 = ");
  //   Serial.println(result);
  //   Serial.println("---");
  //   cmd[0] = number;
  //   wrapper.read_write_once(cmd, POSITION, 0);
  // }


  

  // for (int i = 0; i < 5; ++i) {
  //   for (int j = 0; j < 100; j += 10) {
  //     cmd[i] = float(j);
  //     wrapper.read_write_once(cmd, POSITION, 0);
  //     delay(10);
  //   }
  //   for (int j = 100; j > 0; j-=10) {
  //     cmd[i] = float(j);
  //     wrapper.read_write_once(cmd, POSITION, 0);
  //     delay(10);
  //   }
  //   // cmd[5] = -cmd[5];
  //   Serial.print("cmd: ");
  //   for (int i = 0; i < 6; ++i) {
  //     Serial.print(cmd[i]);
  //     Serial.print(" ");
  //   }
  //   Serial.println();
  // }

  // DEBUG: Check if this serial connection is still alive 
  // long time = millis();
  // while (!Serial) {
  //   if (millis() - time > 1000) {
  //     close_serial();
  //     Serial.println("Serial connection lost. Exiting...");
  //     while (1);
  //   }
  // }

  // if (millis() > 100000) {
  //   close_serial();
  //   while(1);
  // }

}

