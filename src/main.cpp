#include <Arduino.h>

#define SOIL_PIN 34

void setup() {
    Serial.begin(115200);
    delay(1000);  
}

void loop() {
    int value = analogRead(SOIL_PIN);
    Serial.print("Soil sensor value: ");
    Serial.println(value);
    delay(1000);
}