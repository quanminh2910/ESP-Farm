#include <Arduino.h>
#include <Wire.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include "adafruit_io_client.h"

#define SOIL_PIN 34
#define DHTPIN 4
#define DHTTYPE DHT11
#define ALERT_LED_PIN 2

// I2C pins for generic ESP32
#define I2C_SDA 21
#define I2C_SCL 22

DHT dht(DHTPIN, DHTTYPE);

// LCD 2004A = 20 columns, 4 rows
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Adjust after calibration
const int dryValue = 3200;
const int wetValue = 1400;

// Temperature alert threshold (C)
const float tempAlertOnC = 33.0f;
const float tempAlertOffC = 32.0f; // hysteresis to reduce LED flicker near threshold

bool tempAlertActive = false;

// Upload every 10 seconds
const unsigned long uploadIntervalMs = 10000;
unsigned long lastUploadMs = 0;

void updateTempAlertLED(float temperatureC, bool dhtOk) {
    if (!dhtOk) {
        tempAlertActive = false;
    } else if (!tempAlertActive && temperatureC >= tempAlertOnC) {
        tempAlertActive = true;
    } else if (tempAlertActive && temperatureC <= tempAlertOffC) {
        tempAlertActive = false;
    }

    digitalWrite(ALERT_LED_PIN, tempAlertActive ? HIGH : LOW);
}

void printLCD(float temperatureC, float humidity, int soilRaw, int soilPercent, bool dhtOk) {
    char line[21];

    lcd.setCursor(0, 0);
    snprintf(line, sizeof(line), "ESP32 FARM MONITOR  ");
    lcd.print(line);

    lcd.setCursor(0, 1);
    if (dhtOk) {
        snprintf(line, sizeof(line), "T:%4.1f%cC H:%4.0f%%   ",
                 temperatureC, 223, humidity);
    } else {
        snprintf(line, sizeof(line), "DHT11 read error    ");
    }
    lcd.print(line);

    lcd.setCursor(0, 2);
    snprintf(line, sizeof(line), "Soil Raw: %-6d     ", soilRaw);
    lcd.print(line);

    lcd.setCursor(0, 3);
    snprintf(line, sizeof(line), "Soil Moist: %3d%%   ", soilPercent);
    lcd.print(line);
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(ALERT_LED_PIN, OUTPUT);
    digitalWrite(ALERT_LED_PIN, LOW);

    analogReadResolution(12);
    dht.begin();

    Wire.begin(I2C_SDA, I2C_SCL);

    lcd.init();
    lcd.backlight();
    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("ESP32 + DHT11 +");
    lcd.setCursor(0, 1);
    lcd.print("Soil Sensor");
    delay(2000);
    lcd.clear();

    Serial.println("ESP32 + DHT11 + Soil Moisture Sensor");
    Serial.print("Temperature alert LED pin: ");
    Serial.println(ALERT_LED_PIN);
    Serial.print("Alert turns ON at ");
    Serial.print(tempAlertOnC);
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
    }

    delay(2000);
}