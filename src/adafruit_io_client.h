#pragma once
#include <Arduino.h>

void beginAdafruitIO();
void updateAdafruitIO();
bool adafruitIOConnected();

bool sendToAdafruitIO(float temperatureC,
                      float humidity,
                      int soilRaw,
                      int soilPercent,
                      bool dhtOk);