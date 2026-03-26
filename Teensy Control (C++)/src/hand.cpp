#include "hand.h"

Hand::Hand(const uint8_t &h_address) : address(h_address) {}

void Hand::update_sensor_forces() {
    for (int i = 0; i < fsr.size(); ++i) {
        uint16_t D = fsr[i];
        
        if (D == 0) {
            forces[i] = C2;
        } else {
            float V = D*3.3f/4096.0f;
            float R = 33000.0f/V + 10000.0f;
            float force = C1/R + C2;
            // forces[i] = force;
            forces[i] = std::max(force, 0.0f);
        }
    }
}