#include "io_functions.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD 2004A = 20 columns, 4 rows, common I2C address 0x27
LiquidCrystal_I2C lcd(0x27, 20, 4);

IOConfig ioConfig = {
	2,
	21,
	22,
	33.0f,
	32.0f
};

bool tempAlertActive = false;

void beginIOFunctions(const IOConfig &config) {
	ioConfig = config;
	tempAlertActive = false;

	pinMode(ioConfig.alertLedPin, OUTPUT);
	digitalWrite(ioConfig.alertLedPin, LOW);

	Wire.begin(ioConfig.i2cSdaPin, ioConfig.i2cSclPin);

	lcd.init();
	lcd.backlight();
	lcd.clear();
}

void showIOSplashScreen() {
	lcd.setCursor(0, 0);
	lcd.print("ESP32 + DHT11 +");
	lcd.setCursor(0, 1);
	lcd.print("Soil Sensor");
	delay(2000);
	lcd.clear();
}

void updateTempAlertLED(float temperatureC, bool dhtOk) {
	if (!dhtOk) {
		tempAlertActive = false;
	} else if (!tempAlertActive && temperatureC >= ioConfig.tempAlertOnC) {
		tempAlertActive = true;
	} else if (tempAlertActive && temperatureC <= ioConfig.tempAlertOffC) {
		tempAlertActive = false;
	}

	digitalWrite(ioConfig.alertLedPin, tempAlertActive ? HIGH : LOW);
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



