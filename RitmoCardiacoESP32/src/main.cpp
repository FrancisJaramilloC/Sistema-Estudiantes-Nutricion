#include "config.h"
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <Preferences.h>
#include <time.h>
#include <lwip/netdb.h>


WiFiManager wm;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
Preferences preferences;

unsigned long lastSendTime = 0;
int consecutiveErrors = 0;
bool timeInitialized = false;
bool shouldSaveConfig = false;

String deviceMac = "";
String pairingCode = "";
String mqttBroker = "";
int mqttBrokerPort = MQTT_PORT;
String mqttUsername = "";
String mqttPassword = "";
bool registered = false;

void checkFactoryReset();
void setupWiFiManager();
void saveConfigCallback();
void loadNVS();
void savePairingCode(const String& code);
void saveMqttCredentials(const String& broker, int port, const String& user, const String& pass);
void loadMqttCredentials();
void initNTP();
void autoRegisterDevice();
int generateBPM();
String generateTimestamp();
bool connectMqtt();
void publishReading(int bpm, const String& timestamp);
void handleError();
void blinkLed(int times, int delayMs);

void mqttCallback(char* topic, byte* payload, unsigned int length) {}

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(RESET_PIN, INPUT_PULLUP);

  Serial.println();
  Serial.println("==========================================");
  Serial.println("  Monitor de Ritmo Cardíaco v3.0");
  Serial.println("  WiFiManager + MQTT");
  Serial.println("==========================================");

  deviceMac = WiFi.macAddress();
  Serial.print("[MAC] Dirección MAC: ");
  Serial.println(deviceMac);

  checkFactoryReset();

  loadNVS();

  setupWiFiManager();

  initNTP();

  randomSeed(analogRead(0));

  autoRegisterDevice();

  if (mqttBroker.length() > 0 && mqttUsername.length() > 0 && mqttPassword.length() > 0) {
    mqttClient.setServer(mqttBroker.c_str(), mqttBrokerPort);
    mqttClient.setCallback(mqttCallback);
    connectMqtt();
  } else {
    Serial.println("[MQTT] Sin credenciales MQTT. No se podrán enviar lecturas.");
  }

  Serial.println("[SETUP] Listo. Publicando lecturas cada 5 segundos por MQTT...");
  Serial.println("==========================================");
}

void loop() {
  unsigned long now = millis();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Conexión perdida. Reconectando...");
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

  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;

    if (!timeInitialized) {
      Serial.println("[NTP] Re-sincronizando hora...");
      initNTP();
    }

    int bpm = generateBPM();
    String timestamp = generateTimestamp();
    publishReading(bpm, timestamp);
  }

  delay(10);
}

void checkFactoryReset() {
  Serial.println("[RESET] Verificando botón de reset...");
  Serial.println("[RESET] Mantén presionado BOOT (GPIO 0) por 3 segundos para resetear.");

  unsigned long startCheck = millis();
  bool buttonHeld = true;

  while (millis() - startCheck < 3000) {
    if (digitalRead(RESET_PIN) == HIGH) {
      buttonHeld = false;
      break;
    }
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
  digitalWrite(LED_PIN, LOW);

  if (buttonHeld) {
    Serial.println("==========================================");
    Serial.println("[RESET] ¡FACTORY RESET ACTIVADO!");
    Serial.println("[RESET] Borrando configuración WiFi...");
    Serial.println("[RESET] Borrando código de emparejamiento...");
    Serial.println("[RESET] Borrando credenciales MQTT...");
    Serial.println("==========================================");

    wm.resetSettings();

    preferences.begin("sensor", false);
    preferences.clear();
    preferences.end();

    Serial.println("[RESET] Todo borrado. Reiniciando en modo Portal Cautivo...");
    delay(1000);
    ESP.restart();
  }

  Serial.println("[RESET] No se solicitó reset. Continuando arranque normal.");
}

void saveConfigCallback() {
  Serial.println("[WIFI] Configuración guardada por WiFiManager.");
  shouldSaveConfig = true;
}

void loadNVS() {
  preferences.begin("sensor", true);
  pairingCode = preferences.getString("pairing_code", "");
  mqttBroker = preferences.getString("mqtt_broker", "");
  mqttBrokerPort = preferences.getInt("mqtt_port", MQTT_PORT);
  mqttUsername = preferences.getString("mqtt_user", "");
  mqttPassword = preferences.getString("mqtt_pass", "");
  registered = preferences.getBool("registered", false);
  preferences.end();

  if (pairingCode.length() > 0) {
    Serial.println("[NVS] Código de emparejamiento cargado.");
  }
  if (mqttBroker.length() > 0) {
    Serial.println("[NVS] Credenciales MQTT cargadas.");
  }
}

void savePairingCode(const String& code) {
  preferences.begin("sensor", false);
  preferences.putString("pairing_code", code);
  preferences.end();
  Serial.println("[NVS] Código de emparejamiento guardado.");
}

void saveMqttCredentials(const String& broker, int port, const String& user, const String& pass) {
  preferences.begin("sensor", false);
  preferences.putString("mqtt_broker", broker);
  preferences.putInt("mqtt_port", port);
  preferences.putString("mqtt_user", user);
  preferences.putString("mqtt_pass", pass);
  preferences.putBool("registered", true);
  preferences.end();
  Serial.println("[NVS] Credenciales MQTT guardadas.");
}

void setupWiFiManager() {
  Serial.println("[WIFI] Iniciando WiFiManager...");

  WiFiManagerParameter custom_pairing_code(
    "pairing_code",
    "Código de emparejamiento",
    pairingCode.c_str(),
    16
  );

  wm.setSaveConfigCallback(saveConfigCallback);
  wm.addParameter(&custom_pairing_code);
  wm.setConfigPortalTimeout(CONFIG_PORTAL_TIMEOUT);
  wm.setConnectTimeout(20);

  wm.setTitle("Sensor de Ritmo Cardíaco");

  String macClean = deviceMac;
  macClean.replace(":", "");
  String apName = String(AP_NAME_PREFIX) + macClean.substring(macClean.length() - 4);

  Serial.print("[WIFI] Nombre del AP: ");
  Serial.println(apName);

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

  if (shouldSaveConfig) {
    String newPairingCode = String(custom_pairing_code.getValue());
    newPairingCode.trim();
    newPairingCode.toUpperCase();

    if (newPairingCode.length() > 0) {
      pairingCode = newPairingCode;
      savePairingCode(pairingCode);
    }
  }

  if (pairingCode.length() == 0) {
    Serial.println("[WARN] ¡No se ha configurado un código de emparejamiento!");
    Serial.println("[WARN] Reseteá el dispositivo (BOOT 3s) y configura el código.");
  }
}

void initNTP() {
  Serial.println("[NTP] Inicializando...");

  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);

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

void autoRegisterDevice() {
  if (registered) {
    Serial.println("[REGISTRO] Dispositivo ya registrado previamente.");
    return;
  }

  if (pairingCode.length() == 0) {
    Serial.println("[REGISTRO] Saltando auto-registro: no hay código de emparejamiento.");
    return;
  }

  Serial.println("[REGISTRO] Auto-registrando dispositivo en el backend...");

  HTTPClient http;
  http.begin(REGISTER_URL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["mac_address"] = deviceMac;
  doc["pairing_code"] = pairingCode;
  doc["nombre"] = "ESP32 Cardiaco";

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();

    if (httpCode == 200 || httpCode == 201) {
      Serial.println("[REGISTRO] ✓ Dispositivo registrado exitosamente.");
      blinkLed(2, 200);

      StaticJsonDocument<512> respDoc;
      DeserializationError error = deserializeJson(respDoc, response);

      if (!error) {
        const char* broker = respDoc["mqtt_broker"] | "";
        const char* mqttUser = respDoc["mqtt_username"] | "";
        const char* mqttPass = respDoc["mqtt_password"] | "";

        if (strlen(broker) > 0 && strlen(mqttUser) > 0 && strlen(mqttPass) > 0) {
          String brokerHost = String(broker);
          int port = MQTT_PORT;
          int colonIdx = brokerHost.indexOf(':');
          if (colonIdx > 0) {
            port = brokerHost.substring(colonIdx + 1).toInt();
            brokerHost = brokerHost.substring(0, colonIdx);
          }

          mqttBroker = brokerHost;
          mqttBrokerPort = port;
          mqttUsername = String(mqttUser);
          mqttPassword = String(mqttPass);
          registered = true;

          saveMqttCredentials(mqttBroker, mqttBrokerPort, mqttUsername, mqttPassword);
        }
      }
    } else if (httpCode == 400 || httpCode == 404) {
      Serial.println("[REGISTRO] ✗ Código de emparejamiento inválido, expirado o ya usado.");
      Serial.println("[REGISTRO] Generá un nuevo código y reconfigurá (BOOT 3s).");
      blinkLed(3, 300);
    } else {
      Serial.print("[REGISTRO] ⚠ Respuesta inesperada: ");
      Serial.println(response);
    }
  } else {
    Serial.print("[REGISTRO] ⚠ Error de conexión: ");
    Serial.println(http.errorToString(httpCode).c_str());
  }

  http.end();
}

int generateBPM() {
  int variation = random(-BPM_VARIATION, BPM_VARIATION + 1);

  if (random(0, 100) < 10) {
    variation += random(10, 30);
  }

  int bpm = BPM_BASE + variation;
  return constrain(bpm, 40, 180);
}

String generateTimestamp() {
  struct tm timeinfo;

  if (timeInitialized && getLocalTime(&timeinfo)) {
    char buffer[30];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);

    Serial.print("[TIMESTAMP] Hora real: ");
    Serial.println(buffer);

    return String(buffer);
  }

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

bool connectMqtt() {
  if (mqttBroker.length() == 0) {
    Serial.println("[FASE:MQTT-1] ERROR: broker hostname vacío");
    return false;
  }

  // --- FASE 1: Verificar WiFi ---
  Serial.println("====== DIAGNÓSTICO MQTT ======");
  Serial.print("[FASE:MQTT-1] WiFi status: ");
  Serial.print(WiFi.status());
  Serial.print(" (");
  switch (WiFi.status()) {
    case WL_CONNECTED: Serial.print("WL_CONNECTED"); break;
    case WL_DISCONNECTED: Serial.print("WL_DISCONNECTED"); break;
    case WL_CONNECT_FAILED: Serial.print("WL_CONNECT_FAILED"); break;
    case WL_NO_SSID_AVAIL: Serial.print("WL_NO_SSID_AVAIL"); break;
    default: Serial.print("DESCONOCIDO"); break;
  }
  Serial.println(")");
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[FASE:MQTT-1] ERROR: WiFi no conectado");
    return false;
  }
  Serial.print("[FASE:MQTT-1] WiFi OK - IP: ");
  Serial.print(WiFi.localIP());
  Serial.print(" | GW: ");
  Serial.println(WiFi.gatewayIP());

  // --- FASE 2: Resolver DNS ---
  Serial.print("[FASE:MQTT-2] Resolviendo hostname: ");
  Serial.println(mqttBroker);
  struct hostent *he = gethostbyname(mqttBroker.c_str());
  if (he == NULL) {
    Serial.print("[FASE:MQTT-2] ERROR: DNS lookup falló (errno: ");
    Serial.print(errno);
    Serial.println(")");
  } else {
    struct in_addr addr;
    memcpy(&addr, he->h_addr_list[0], sizeof(addr));
    Serial.print("[FASE:MQTT-2] DNS OK -> IP: ");
    Serial.println(inet_ntoa(addr));
  }

  // --- FASE 3: Test TCP ---
  Serial.print("[FASE:MQTT-3] Test TCP a ");
  Serial.print(mqttBroker);
  Serial.print(":");
  Serial.println(mqttBrokerPort);

  WiFiClient testClient;
  int tcpResult = -1;
  for (int tcpAttempt = 0; tcpAttempt < 3; tcpAttempt++) {
    if (tcpAttempt > 0) {
      Serial.print("[FASE:MQTT-3] Reintento TCP #");
      Serial.println(tcpAttempt + 1);
      delay(1000);
    }
    bool connected = testClient.connect(mqttBroker.c_str(), mqttBrokerPort);
    if (connected) {
      tcpResult = 0;
      break;
    } else {
      tcpResult = 1;
      Serial.print("[FASE:MQTT-3] TCP falló (intento ");
      Serial.print(tcpAttempt + 1);
      Serial.println("/3)");
    }
  }
  testClient.stop();

  if (tcpResult != 0) {
    Serial.println("[FASE:MQTT-3] ERROR: No se pudo establecer TCP");
    return false;
  }
  Serial.println("[FASE:MQTT-3] TCP OK - conexión establecida");

  // --- FASE 4: MQTT CONNECT ---
  Serial.print("[FASE:MQTT-4] Enviando MQTT CONNECT...");
  Serial.print(" clientId=ESP32_");
  Serial.print(deviceMac);
  Serial.print(" user=");
  Serial.println(mqttUsername);

  String clientId = "ESP32_" + deviceMac;
  clientId.replace(":", "");
  mqttClient.setServer(mqttBroker.c_str(), mqttBrokerPort);

  int attempts = 0;
  while (!mqttClient.connected() && attempts < 3) {
    if (mqttClient.connect(clientId.c_str(), mqttUsername.c_str(), mqttPassword.c_str())) {
      Serial.println("[FASE:MQTT-4] ✓ CONNECT aceptado");
      blinkLed(1, 100);
      return true;
    } else {
      attempts++;
      int state = mqttClient.state();
      Serial.print("[FASE:MQTT-4] ✗ CONNECT rechazado (intento ");
      Serial.print(attempts);
      Serial.print("/3) estado=");
      Serial.print(state);
      Serial.print(" (");
      switch (state) {
        case -4: Serial.print("CONNECTION_TIMEOUT - no hubo respuesta"); break;
        case -3: Serial.print("CONNECTION_LOST - se perdió la conexión"); break;
        case -2: Serial.print("CONNECT_FAILED - TCP no conectó"); break;
        case -1: Serial.print("DISCONNECTED - cliente desconectado"); break;
        case 1: Serial.print("BAD_PROTOCOL - versión MQTT no soportada"); break;
        case 2: Serial.print("BAD_CLIENT_ID - ID de cliente rechazado"); break;
        case 3: Serial.print("UNAVAILABLE - servidor no disponible"); break;
        case 4: Serial.print("BAD_CREDENTIALS - usuario o contraseña incorrecto"); break;
        case 5: Serial.print("UNAUTHORIZED - no autorizado"); break;
        default: Serial.print("DESCONOCIDO"); break;
      }
      Serial.println(")");
      delay(2000);
    }
  }

  Serial.println("[FASE:MQTT-4] ERROR: No se pudo conectar al broker MQTT.");
  Serial.println("[FASE:MQTT-5] Borrando credenciales y forzando re-registro...");
  preferences.begin("sensor", false);
  preferences.remove("mqtt_broker");
  preferences.remove("mqtt_port");
  preferences.remove("mqtt_user");
  preferences.remove("mqtt_pass");
  preferences.putBool("registered", false);
  preferences.end();
  mqttBroker = "";
  registered = false;
  Serial.println("[FASE:MQTT-5] Credenciales borradas. Reiniciando en 2s...");
  delay(2000);
  ESP.restart();
  return false;
}

void publishReading(int bpm, const String& timestamp) {
  if (!mqttClient.connected()) {
    bool reconnected = connectMqtt();
    if (!reconnected) {
      handleError();
      return;
    }
  }

  String topic = String(MQTT_TOPIC_PREFIX) + "/" + deviceMac + "/lecturas";
  topic.toLowerCase();

  StaticJsonDocument<128> doc;
  doc["bpm"] = bpm;
  doc["timestamp"] = timestamp;

  String payload;
  serializeJson(doc, payload);

  Serial.println("------------------------------");
  Serial.print("[PUB] Topic: ");
  Serial.println(topic);
  Serial.print("[PUB] BPM: ");
  Serial.print(bpm);
  Serial.print(" | MAC: ");
  Serial.print(deviceMac);
  Serial.print(" | Timestamp: ");
  Serial.println(timestamp);

  if (mqttClient.publish(topic.c_str(), payload.c_str(), true)) {
    blinkLed(1, 100);
    consecutiveErrors = 0;
    Serial.println("[OK] Lectura publicada exitosamente");
  } else {
    Serial.println("[ERROR] Falló la publicación MQTT");
    handleError();
  }
}

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

void blinkLed(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}
