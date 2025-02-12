#include "time.h"
#include <WiFi.h>
#include <PubSubClient.h>

#define LED_RED 16
#define LED_YELLOW 17
#define LED_GREEN 5
#define SENSOR_MOTION 21
#define BUZZER 23

const char* ssid = "vifi";
const char* password = "0123456789";
const char* mqtt_server = "192.168.39.139"; 

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long previousMillis = 0;
int stepIndex = 0;
volatile bool motionDetected = false;

void resetState() 
{
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
  stepIndex = 0;
}

void detectMovement()
{
  motionDetected = (stepIndex == 0) ? true : false;
}

void setup() 
{
  Serial.begin(115200);

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(SENSOR_MOTION, INPUT_PULLUP);
  
  attachInterrupt(digitalPinToInterrupt(SENSOR_MOTION), detectMovement, RISING);

  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);

  // WiFi setup
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
  }
  Serial.println(F("Connected to WiFi"));

  if (!client.connected()) {
      reconnectMQTT();
  }
}

void loop() 
{
  if (motionDetected)
  {
    digitalWrite(BUZZER, HIGH);  // Turn on buzzer
    
    client.publish("motion/detected", "Motion detected");
    Serial.println("Published motion detected to MQTT topic");  

    motionDetected = false;  // Reset flag after sending request
  }

  // Reset buzzer when stepIndex is not 0
  if (stepIndex != 0)
  {
    digitalWrite(BUZZER, LOW);
    motionDetected = false;
  }

  unsigned long currentMillis = millis();

  switch (stepIndex)
  {
    case 0: 
      digitalWrite(LED_RED, HIGH);
      digitalWrite(LED_YELLOW, LOW);
      digitalWrite(LED_GREEN, LOW);
      if (currentMillis - previousMillis >= 7500) {
        stepIndex++;
        previousMillis = currentMillis;
      }
      break;

    case 1:
      digitalWrite(LED_YELLOW, HIGH);
      if (currentMillis - previousMillis >= 3000) {
        stepIndex++;
        previousMillis = currentMillis;
      }
      break;

    case 2:
      digitalWrite(LED_GREEN, HIGH);
      digitalWrite(LED_RED, LOW);
      digitalWrite(LED_YELLOW, LOW);

      if (currentMillis - previousMillis >= 5000) {
        stepIndex++;
        previousMillis = currentMillis;
      }
      break;

    case 3: 
      digitalWrite(LED_YELLOW, HIGH);
      if (currentMillis - previousMillis >= 3000) {
        stepIndex = 0;
        previousMillis = currentMillis;
      }
      break;
  }

  client.loop();
}

void mqttCallback(char* topic, byte* payload, unsigned int length) 
{
  // Callback function for receiving messages (if needed)
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("espClient")) { // Change "ESP32Client" if needed
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds...");
      delay(5000);
    }
  }
}

