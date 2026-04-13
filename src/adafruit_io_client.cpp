#include "adafruit_io_client.h"
#include "adafruit_secrets.h"
#include <AdafruitIO_WiFi.h>

// Create Adafruit IO connection
AdafruitIO_WiFi io(IO_USERNAME, IO_KEY, WIFI_SSID, WIFI_PASS);
// Create/feed names in Adafruit IO
AdafruitIO_Feed *temperatureFeed = io.feed("temperature");
AdafruitIO_Feed *humidityFeed    = io.feed("humidity");
AdafruitIO_Feed *soilRawFeed     = io.feed("soil-raw");
AdafruitIO_Feed *soilMoistFeed   = io.feed("soil-moisture");

void beginAdafruitIO() {
    Serial.println("Connecting to Adafruit IO...");
    io.connect();

    unsigned long start = millis();
    while (io.status() < AIO_CONNECTED && millis() - start < 30000) { // wait for 30 seconds max
        io.run();
        Serial.print(".");
        delay(500);
    }
    Serial.println();

    if (io.status() == AIO_CONNECTED) {
        Serial.println("Adafruit IO connected!");
        Serial.println(io.statusText());
    } else {
        Serial.println("Adafruit IO connection timeout.");
        Serial.println(io.statusText());
    }
}

void updateAdafruitIO() {
    io.run();

    static aio_status_t lastStatus = AIO_IDLE;
    aio_status_t currentStatus = io.status();

    if (currentStatus != lastStatus) {
        Serial.print("Adafruit IO status: ");
        Serial.println(io.statusText());
        lastStatus = currentStatus;
    }
}

bool adafruitIOConnected() {
    return io.status() == AIO_CONNECTED;
}

bool sendToAdafruitIO(float temperatureC,
                      float humidity,
                      int soilRaw,
                      int soilPercent,
                      bool dhtOk) {
    updateAdafruitIO();

    if (!adafruitIOConnected()) {
        Serial.println("Adafruit IO not connected, skip upload.");
        return false;
    }

    if (dhtOk) {
        temperatureFeed->save(temperatureC);
        humidityFeed->save(humidity);
    }

    soilRawFeed->save(soilRaw);
    soilMoistFeed->save(soilPercent);

    Serial.println("Data sent to Adafruit IO.");
    return true;
}