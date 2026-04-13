#include <Arduino.h>
#include <DHT.h>
#include "adafruit_io_client.h"
#include "io_functions.h"

#define SOIL_PIN 34
#define DHTPIN 4
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

// Adjust after calibration
const int dryValue = 3200;
const int wetValue = 1400;

const IOConfig ioConfig = {
    2,
    21,
    22,
    33.0f,
    32.0f
};

// Upload to Adafruit IO every 10 seconds
const unsigned long uploadIntervalMs = 10000;
unsigned long lastUploadMs = 0;  

void setup() {
    Serial.begin(115200);
    delay(1000);

    analogReadResolution(12);
    dht.begin();

    beginIOFunctions(ioConfig);
    showIOSplashScreen();

    Serial.println("ESP32 + DHT11 + Soil Moisture Sensor");
    Serial.print("Temperature alert LED pin: ");
    Serial.println(ioConfig.alertLedPin);
    Serial.print("Alert turns ON at ");
    Serial.print(ioConfig.tempAlertOnC);
    Serial.println(" C");

    beginAdafruitIO();
}

void loop() {
    updateAdafruitIO();

    float humidity = dht.readHumidity();
    float temperatureC = dht.readTemperature();

    int soilRaw = analogRead(SOIL_PIN);
    int soilPercent = map(soilRaw, dryValue, wetValue, 0, 100);
    soilPercent = constrain(soilPercent, 0, 100);

    bool dhtOk = !(isnan(humidity) || isnan(temperatureC));
    updateTempAlertLED(temperatureC, dhtOk);

    if (!dhtOk) {
        Serial.println("Failed to read from DHT11");
    } else {
        Serial.print("Temperature: ");
        Serial.print(temperatureC);
        Serial.println(" C");

        Serial.print("Humidity: ");
        Serial.print(humidity);
        Serial.println(" %");
    }

    Serial.print("Soil Raw: ");
    Serial.print(soilRaw);
    Serial.print(" | Soil Moisture: ");
    Serial.print(soilPercent);
    Serial.println(" %");

    Serial.println("------------------------");

    printLCD(temperatureC, humidity, soilRaw, soilPercent, dhtOk);

    if (millis() - lastUploadMs >= uploadIntervalMs) {
        lastUploadMs = millis();
        sendToAdafruitIO(temperatureC, humidity, soilRaw, soilPercent, dhtOk);
    } else {
        // Still need to call io.run() regularly to maintain connection
        updateAdafruitIO();
    }

    delay(2000);
}