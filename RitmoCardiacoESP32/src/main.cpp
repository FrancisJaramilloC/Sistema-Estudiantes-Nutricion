/*
 * Monitor de Ritmo Cardíaco - ESP32
 * Versión con WiFiManager (Portal Cautivo) + Autenticación por MAC
 *
 * FLUJO DEL USUARIO:
 * 1. Encender el ESP32 → Si no tiene WiFi guardado, crea una red "Sensor-Ritmo-XXXX"
 * 2. Conectarse a esa red desde el celular → Se abre un portal web automáticamente
 * 3. Seleccionar la red WiFi, ingresar contraseña e ID del Estudiante
 * 4. El ESP32 se conecta, se auto-registra en el backend y empieza a enviar datos
 *
 * RESET DE FÁBRICA:
 * Mantener presionado el botón BOOT (GPIO 0) durante 3 segundos al encender
 * para borrar la configuración WiFi y volver al modo Portal Cautivo.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <time.h>
#include "config.h"

// ==================== VARIABLES GLOBALES ====================
WiFiManager wm;
Preferences preferences;

unsigned long lastSendTime = 0;
int consecutiveErrors = 0;
bool timeInitialized = false;
bool shouldSaveConfig = false;

String deviceMac = "";
String studentId = "";

// ==================== PROTOTIPOS ====================
void checkFactoryReset();
void setupWiFiManager();
void saveConfigCallback();
void loadStudentId();
void saveStudentId(const String& id);
void initNTP();
void autoRegisterDevice();
int generateBPM();
String generateTimestamp();
void sendReading(int bpm, const String& timestamp);
void handleError();
void blinkLed(int times, int delayMs);

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(RESET_PIN, INPUT_PULLUP);

  Serial.println();
  Serial.println("==========================================");
  Serial.println("  Monitor de Ritmo Cardíaco v2.0");
  Serial.println("  WiFiManager + Autenticación por MAC");
  Serial.println("==========================================");

  // Obtener dirección MAC del dispositivo
  deviceMac = WiFi.macAddress();
  Serial.print("[MAC] Dirección MAC del dispositivo: ");
  Serial.println(deviceMac);

  // Verificar si se solicita reset de fábrica
  checkFactoryReset();

  // Cargar student_id guardado en NVS
  loadStudentId();

  // Configurar e iniciar WiFiManager
  setupWiFiManager();

  // Inicializar NTP
  initNTP();

  // Inicializar semilla aleatoria
  randomSeed(analogRead(0));

  // Auto-registrar dispositivo en el backend
  autoRegisterDevice();

  Serial.println("[SETUP] Listo. Enviando lecturas cada 5 segundos...");
  Serial.println("==========================================");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  unsigned long now = millis();

  // Verificar conexión WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Conexión perdida. Reconectando...");
    // Intentar reconexión rápida
    WiFi.reconnect();
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println();
      Serial.println("[WIFI] No se pudo reconectar. Reiniciando...");
      ESP.restart();
    }
    Serial.println();
    Serial.println("[WIFI] Reconectado exitosamente.");
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
 * Verifica si el usuario mantiene presionado el botón BOOT
 * durante 3 segundos para hacer un factory reset.
 */
void checkFactoryReset() {
  Serial.println("[RESET] Verificando botón de reset...");
  Serial.println("[RESET] Mantén presionado BOOT (GPIO 0) por 3 segundos para resetear.");

  // Dar una ventana de 3 segundos para detectar el botón
  unsigned long startCheck = millis();
  bool buttonHeld = true;

  while (millis() - startCheck < 3000) {
    if (digitalRead(RESET_PIN) == HIGH) {
      // Botón no presionado, salir
      buttonHeld = false;
      break;
    }
    // Parpadeo rápido del LED mientras se detecta el botón
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
  digitalWrite(LED_PIN, LOW);

  if (buttonHeld) {
    Serial.println("==========================================");
    Serial.println("[RESET] ¡FACTORY RESET ACTIVADO!");
    Serial.println("[RESET] Borrando configuración WiFi...");
    Serial.println("[RESET] Borrando ID del estudiante...");
    Serial.println("==========================================");

    // Borrar configuración WiFi
    wm.resetSettings();

    // Borrar student_id de NVS
    preferences.begin("sensor", false);
    preferences.clear();
    preferences.end();

    Serial.println("[RESET] Todo borrado. Reiniciando en modo Portal Cautivo...");
    delay(1000);
    ESP.restart();
  }

  Serial.println("[RESET] No se solicitó reset. Continuando arranque normal.");
}

/**
 * Callback que se ejecuta cuando WiFiManager guarda la configuración
 */
void saveConfigCallback() {
  Serial.println("[WIFI] Configuración guardada por WiFiManager.");
  shouldSaveConfig = true;
}

/**
 * Carga el student_id desde la memoria NVS (Preferences)
 */
void loadStudentId() {
  preferences.begin("sensor", true); // read-only
  studentId = preferences.getString("student_id", "");
  preferences.end();

  if (studentId.length() > 0) {
    Serial.print("[NVS] ID del Estudiante cargado: ");
    Serial.println(studentId);
  } else {
    Serial.println("[NVS] No hay ID del Estudiante guardado. Se pedirá en el Portal Cautivo.");
  }
}

/**
 * Guarda el student_id en la memoria NVS (Preferences)
 */
void saveStudentId(const String& id) {
  preferences.begin("sensor", false); // read-write
  preferences.putString("student_id", id);
  preferences.end();
  Serial.print("[NVS] ID del Estudiante guardado: ");
  Serial.println(id);
}

/**
 * Configura WiFiManager con el portal cautivo y parámetros personalizados
 */
void setupWiFiManager() {
  Serial.println("[WIFI] Iniciando WiFiManager...");

  // Crear parámetro personalizado para el ID del Estudiante
  WiFiManagerParameter custom_student_id(
    "student_id",              // ID del campo
    "ID del Estudiante",       // Label que ve el usuario
    studentId.c_str(),         // Valor por defecto (si ya había uno guardado)
    50                         // Longitud máxima
  );

  // Configurar WiFiManager
  wm.setSaveConfigCallback(saveConfigCallback);
  wm.addParameter(&custom_student_id);
  wm.setConfigPortalTimeout(CONFIG_PORTAL_TIMEOUT);
  wm.setConnectTimeout(20);

  // Personalizar el portal
  wm.setTitle("Sensor de Ritmo Cardíaco");

  // Generar nombre del AP con los últimos 4 caracteres del MAC
  String macClean = deviceMac;
  macClean.replace(":", "");
  String apName = String(AP_NAME_PREFIX) + macClean.substring(macClean.length() - 4);

  Serial.print("[WIFI] Nombre del AP: ");
  Serial.println(apName);
  Serial.println("[WIFI] Conéctate a esta red WiFi desde tu celular para configurar.");

  // LED parpadeando indica modo configuración
  // autoConnect bloquea hasta que se conecte
  bool connected = wm.autoConnect(apName.c_str(), AP_PASSWORD);

  if (!connected) {
    Serial.println("[WIFI] No se pudo conectar. Reiniciando...");
    delay(2000);
    ESP.restart();
  }

  Serial.println("[WIFI] ¡Conectado exitosamente!");
  Serial.print("[WIFI] IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WIFI] RSSI: ");
  Serial.println(WiFi.RSSI());

  // Guardar el student_id si se ingresó en el portal
  if (shouldSaveConfig) {
    String newStudentId = String(custom_student_id.getValue());
    newStudentId.trim();

    if (newStudentId.length() > 0) {
      studentId = newStudentId;
      saveStudentId(studentId);
    }
  }

  // Verificar que tenemos un student_id configurado
  if (studentId.length() == 0) {
    Serial.println("[WARN] ¡No se ha configurado un ID del Estudiante!");
    Serial.println("[WARN] Reseteá el dispositivo (BOOT 3s) y configura el ID.");
    Serial.println("[WARN] Continuando sin student_id...");
  }
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
 * Auto-registra el dispositivo en el backend usando la dirección MAC.
 * Se llama una vez en el setup. Es idempotente (se puede llamar varias veces).
 */
void autoRegisterDevice() {
  if (studentId.length() == 0) {
    Serial.println("[REGISTRO] Saltando auto-registro: no hay student_id configurado.");
    return;
  }

  Serial.println("[REGISTRO] Auto-registrando dispositivo en el backend...");
  Serial.print("[REGISTRO] MAC: ");
  Serial.println(deviceMac);
  Serial.print("[REGISTRO] Estudiante: ");
  Serial.println(studentId);

  HTTPClient http;
  http.begin(REGISTER_URL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["mac_address"] = deviceMac;
  doc["student_id"] = studentId;
  doc["nombre"] = "ESP32 Cardiaco";

  String payload;
  serializeJson(doc, payload);

  Serial.print("[REGISTRO] Payload: ");
  Serial.println(payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[REGISTRO] HTTP ");
    Serial.println(httpCode);

    if (httpCode == 200 || httpCode == 201) {
      Serial.println("[REGISTRO] ✓ Dispositivo registrado/verificado exitosamente.");
      blinkLed(2, 200);
    } else if (httpCode == 409) {
      Serial.println("[REGISTRO] ✓ Dispositivo ya estaba registrado (OK).");
      blinkLed(2, 200);
    } else {
      Serial.print("[REGISTRO] ⚠ Respuesta inesperada: ");
      Serial.println(response);
    }
  } else {
    Serial.print("[REGISTRO] ⚠ Error de conexión: ");
    Serial.println(http.errorToString(httpCode).c_str());
    Serial.println("[REGISTRO] El dispositivo intentará registrarse en el próximo reinicio.");
  }

  http.end();
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
 * Envía la lectura al backend autenticándose por MAC
 */
void sendReading(int bpm, const String& timestamp) {
  HTTPClient http;
  http.begin(READING_URL);

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Mac", deviceMac);  // Autenticación por MAC

  StaticJsonDocument<128> doc;
  doc["bpm"] = bpm;
  doc["timestamp"] = timestamp;

  String payload;
  serializeJson(doc, payload);

  Serial.println("------------------------------");
  Serial.print("[ENVIO] BPM: ");
  Serial.print(bpm);
  Serial.print(" | MAC: ");
  Serial.print(deviceMac);
  Serial.print(" | Timestamp: ");
  Serial.println(timestamp);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.print("[RESPUESTA] HTTP ");
    Serial.println(httpCode);

    if (httpCode == 200 || httpCode == 201) {
      blinkLed(1, 100);
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
 * Maneja errores consecutivos
 */
void handleError() {
  consecutiveErrors++;
  Serial.print("[ERROR] Fallos consecutivos: ");
  Serial.println(consecutiveErrors);

  blinkLed(3, 100);

  if (consecutiveErrors >= 5) {
    Serial.println("[ERROR] Demasiados fallos. Reiniciando...");
    delay(2000);
    ESP.restart();
  }
}

/**
 * Parpadea el LED un número de veces
 */
void blinkLed(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}