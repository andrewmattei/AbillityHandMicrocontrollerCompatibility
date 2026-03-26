#include <Arduino.h>
#include <array>
#include <cstring>
#include <stdio.h>

#include "wrapper.h"

// Using Serial1 for hardware UART communication
#define HAND_SERIAL Serial1
const int HAND_BAUD = 460800;
AHWrapper wrapper = AHWrapper(0x50, HAND_BAUD);

namespace {
constexpr uint8_t CMD_HEADER = 0xA5;
constexpr uint8_t TELEMETRY_HEADER = 0x5A;

enum PcControlMode : uint8_t { PC_POSITION = 0, PC_VELOCITY = 1, PC_TORQUE = 2 };

struct PcCommandPacket {
  uint8_t header;
  uint8_t mode;
  float command[6];
  uint8_t checksum;
};

struct PcTelemetryPacket {
  uint8_t header;
  uint8_t mode;
  float position[6];
  float velocity[6];
  float force[30];
  uint8_t checksum;
};

constexpr size_t CMD_PACKET_SIZE = sizeof(PcCommandPacket);
constexpr size_t TELEMETRY_PACKET_SIZE = sizeof(PcTelemetryPacket);

uint8_t compute_checksum(const uint8_t *data, size_t n_bytes) {
  uint32_t sum = 0;
  for (size_t i = 0; i < n_bytes; ++i) {
    sum += data[i];
  }
  return static_cast<uint8_t>(-sum);
}

bool checksum_valid(const uint8_t *data, size_t total_size) {
  if (total_size == 0) {
    return false;
  }
  uint8_t expected = compute_checksum(data, total_size - 1);
  return expected == data[total_size - 1];
}

Command to_hand_command(uint8_t pc_mode) {
  switch (pc_mode) {
  case PC_VELOCITY:
    return VELOCITY;
  case PC_TORQUE:
    return CURRENT;
  case PC_POSITION:
  default:
    return POSITION;
  }
}

bool read_command_packet(PcCommandPacket &packet) {
  while (Serial.available() > 0) {
    if (static_cast<uint8_t>(Serial.peek()) != CMD_HEADER) {
      Serial.read();
      continue;
    }

    if (Serial.available() < static_cast<int>(CMD_PACKET_SIZE)) {
      return false;
    }

    size_t bytes_read = Serial.readBytes(reinterpret_cast<char *>(&packet), CMD_PACKET_SIZE);
    if (bytes_read != CMD_PACKET_SIZE) {
      return false;
    }

    if (!checksum_valid(reinterpret_cast<const uint8_t *>(&packet), CMD_PACKET_SIZE)) {
      Serial.println("ERROR: Bad command checksum");
      return false;
    }

    if (packet.mode > PC_TORQUE) {
      Serial.println("ERROR: Unsupported control mode");
      return false;
    }

    return true;
  }

  return false;
}

void send_telemetry_packet(uint8_t current_mode) {
  PcTelemetryPacket packet{};
  packet.header = TELEMETRY_HEADER;
  packet.mode = current_mode;

  for (int i = 0; i < 6; ++i) {
    packet.position[i] = wrapper.hand.pos[i];
    packet.velocity[i] = wrapper.hand.vel[i];
  }

  for (int i = 0; i < 30; ++i) {
    packet.force[i] = wrapper.hand.forces[i];
  }

  packet.checksum =
      compute_checksum(reinterpret_cast<const uint8_t *>(&packet), TELEMETRY_PACKET_SIZE - 1);
  Serial.write(reinterpret_cast<const uint8_t *>(&packet), TELEMETRY_PACKET_SIZE);
}
} // namespace

std::array<float, 6> cmd;
bool new_command_received = false;
unsigned long last_cmd_time = 0;
const unsigned long CMD_TIMEOUT_MS = 100;
uint8_t current_pc_mode = PC_POSITION;
Command current_hand_command = POSITION;

void setup() {
  Serial.begin(460800);
  HAND_SERIAL.begin(HAND_BAUD);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

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
}

void loop() {
  PcCommandPacket packet{};
  bool received_packet = false;
  while (read_command_packet(packet)) {
    bool valid_data = true;
    for (int i = 0; i < 6; ++i) {
      float val = packet.command[i];
      if (isnan(val) || isinf(val)) {
        Serial.println("ERROR: Invalid command value");
        digitalWrite(LED_BUILTIN, HIGH);
        valid_data = false;
        break;
      }
    }

    if (!valid_data) {
      continue;
    }

    digitalWrite(LED_BUILTIN, LOW);
    for (int i = 0; i < 6; ++i) {
      cmd[i] = packet.command[i];
    }
    current_pc_mode = packet.mode;
    current_hand_command = to_hand_command(current_pc_mode);
    new_command_received = true;
    received_packet = true;
    last_cmd_time = millis();
  }

  if (new_command_received && millis() - last_cmd_time > CMD_TIMEOUT_MS) {
    Serial.println("Command timeout, stopping hand");
    new_command_received = false;
    cmd = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
  }

  if (new_command_received || received_packet) {
    wrapper.read_write_once(cmd, current_hand_command, 1);
    send_telemetry_packet(current_pc_mode);
  }

  delayMicroseconds(100);
}

