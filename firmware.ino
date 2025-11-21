#include <LedControl.h>

// Pins: DIN, CLK, CS, number of devices
const int DIN_PIN = 12;
const int CLK_PIN = 11;
const int CS_PIN  = 10;

LedControl lc = LedControl(DIN_PIN, CLK_PIN, CS_PIN, 1);

const byte FRAME_HEADER = 0xAA;  // Start-of-frame marker
byte rowBuffer[8];
int rowIndex = 0;
bool inFrame = false;

void setup() {
  // Init MAX7219
  lc.shutdown(0, false);
  lc.setIntensity(0, 8);   // 0–15 brightness
  lc.clearDisplay(0);

  // Serial (must match Python)
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) {
    byte b = Serial.read();

    if (!inFrame) {
      // Wait for header byte
      if (b == FRAME_HEADER) {
        inFrame = true;
        rowIndex = 0;
      }
    } else {
      // Collect 8 row bytes
      rowBuffer[rowIndex++] = b;

      if (rowIndex >= 8) {
        // We have a full frame: update display
        for (int r = 0; r < 8; r++) {
          // Each byte rowBuffer[r] controls row r
          lc.setRow(0, r, rowBuffer[r]);
        }
        inFrame = false;  // Next frame
      }
    }
  }
}
