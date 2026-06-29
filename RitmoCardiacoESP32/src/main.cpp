/*
 * Monitor de Ritmo Cardíaco - ESP32 (Simulador)
 * Versión con NTP para timestamps correctos
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "config.h"

// ==================== VARIABLES GLOBALES ====================
unsigned long lastSendTime = 0;
int consecutiveErrors = 0;
bool timeInitialized = false;

// ==================== PROTOTIPOS ====================
void connectToWiFi();
void initNTP();
int generateBPM();
String generateTimestamp();
void sendReading(int bpm, const String& timestamp);
void handleError();

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println();
  Serial.println("==============================");
  Serial.println("Monitor de Ritmo Cardíaco v1.0");
  Serial.println("==============================");

  // Conectar a WiFi
  connectToWiFi();
  
  // Inicializar NTP
  initNTP();
  
  // Inicializar semilla aleatoria
  randomSeed(analogRead(0));
  
  Serial.println("[SETUP] Listo. Enviando lecturas cada 5 segundos...");
  Serial.println("==============================");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  unsigned long now = millis();

  // Verificar conexión WiFi cada cierto tiempo
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Conexión perdida. Reconectando...");
    connectToWiFi();
    return;
  }

  // Enviar lectura en el intervalo configurado
  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;

    // Verificar que la hora esté sincronizada
    if (!timeInitialized) {
      Serial.println("[NTP] Re-sincronizando hora...");
      initNTP();
    }

    int bpm = generateBPM();
    String timestamp = generateTimestamp();
    sendReading(bpm, timestamp);
  }

  delay(10);
}

// ==================== FUNCIONES ====================

/**
 * Conecta a la red WiFi
 */
void connectToWiFi() {
  Serial.print("[WIFI] Conectando a ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    if (attempts > 40) {
      Serial.println();
      Serial.println("[WIFI] Error de conexión. Reiniciando ESP32...");
      ESP.restart();
    }
  }

  Serial.println();
  Serial.print("[WIFI] Conectado. IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WIFI] RSSI: ");
  Serial.println(WiFi.RSSI());
}

/**
 * Inicializa NTP para obtener la hora actual
 */
void initNTP() {
  Serial.println("[NTP] Inicializando...");
  
  // Configurar zona horaria
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  
  // Esperar hasta obtener la hora
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 10) {
    Serial.print(".");
    delay(1000);
    attempts++;
  }

  if (attempts < 10) {
    timeInitialized = true;
    Serial.println();
    Serial.print("[NTP] Hora sincronizada: ");
    Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
  } else {
    timeInitialized = false;
    Serial.println();
    Serial.println("[NTP] Error: No se pudo obtener la hora. Usando timestamp simulado.");
  }
}

/**
 * Genera un valor simulado de BPM
 */
int generateBPM() {
  int variation = random(-BPM_VARIATION, BPM_VARIATION + 1);

  if (random(0, 100) < 10) {
    variation += random(10, 30);
  }

  int bpm = BPM_BASE + variation;
  return constrain(bpm, 40, 180);
}

/**
 * Genera timestamp en formato ISO 8601 con hora real
 */
String generateTimestamp() {
  struct tm timeinfo;
  
  // Intentar obtener hora real
  if (timeInitialized && getLocalTime(&timeinfo)) {
    char buffer[30];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    
    // Mostrar la hora para verificar
    Serial.print("[TIMESTAMP] Hora real: ");
    Serial.println(buffer);
    
    return String(buffer);
  }
  
  // Fallback: timestamp simulado (NO RECOMENDADO PARA PRODUCCIÓN)
  Serial.println("[WARN] Usando timestamp simulado");
  unsigned long uptime = millis() / 1000;
  unsigned long seconds = uptime % 60;
  unsigned long minutes = (uptime / 60) % 60;
  unsigned long hours = (uptime / 3600) % 24;
  
  char buffer[30];
  snprintf(buffer, sizeof(buffer), "2026-06-28T%02lu:%02lu:%02luZ", 
           hours, minutes, seconds);
  return String(buffer);
}

/**
 * Envía la lectura al backend
 */
void sendReading(int bpm, const String& timestamp) {
  HTTPClient http;
  http.begin(SERVER_URL);

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Api-Key", API_KEY);

  StaticJsonDocument<128> doc;
  doc["bpm"] = bpm;
  doc["timestamp"] = timestamp;

  String payload;
  serializeJson(doc, payload);

  Serial.println("------------------------------");
  Serial.print("[ENVIO] BPM: ");
  Serial.print(bpm);
  Serial.print(" | Timestamp: ");
  Serial.println(timestamp);
  Serial.print("[PAYLOAD] ");
  Serial.println(payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[RESPUESTA] HTTP ");
    Serial.println(httpCode);

    if (httpCode == 200 || httpCode == 201) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      consecutiveErrors = 0;
      Serial.println("[OK] Lectura registrada exitosamente");
    } else {
      Serial.print("[ERROR] Código inesperado. Respuesta: ");
      Serial.println(response);
      handleError();
    }
  } else {
    Serial.print("[ERROR] Falló la petición HTTP: ");
    Serial.println(http.errorToString(httpCode).c_str());
    handleError();
  }

  http.end();
}

/**
 * Maneja errores
 */
void handleError() {
  consecutiveErrors++;
  Serial.print("[ERROR] Fallos consecutivos: ");
  Serial.println(consecutiveErrors);

  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  if (consecutiveErrors >= 5) {
    Serial.println("[ERROR] Demasiados fallos. Reiniciando...");
    delay(2000);
    ESP.restart();
  }
}