
# ========================================================
#region WiFi Server

AP_NAME = "VG PPQ"
AP_DOMAIN = "vqrs-pico-wifi.net"

AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"

WIFI_FILE = "wifi.json"
WIFI_MAX_ATTEMPTS = 3

EXECUTION_FILE = "execution.txt"

#endregion
# ========================================================

# ========================================================
#region Image File

VG_PPQ_LOGO = "img/logo.txt"
WIFI_A_IMG = "img/wifi_a.txt"
WIFI_B_IMG = "img/wifi_b.txt"

#endregion
# ========================================================

# ========================================================
#region MQTT

ICT_RESPONSE_CODE = {
    "10": "Bill Accept Success",
    "11": "Bill Accept Failure",
    "808f": "Power ON",
    "2f": "Error",
    "29": "Machine Error: Bill Accept",
    "8140": "RM 1",
    "8141": "RM 5",
    "8142": "RM 10",
    "8143": "RM 20",
    "8144": "RM 50",
    "3e": "Controller Accept Bill",
    "30": "Controller Reset",
    "5e": "Controller Disable Bill",
}

MQTT_USERNAME = b'gan'
MQTT_PASSWORD = b'123456'
MQTT_HOSTNAME = b'47.254.229.107'
MQTT_PORT = 1883

ICT_TOPIC = "vgppq/server"

#endregion
# ========================================================

# ========================================================
#region GPIO Pins

MB_PIN_TX = 12
MB_PIN_RX = 13

ICT_PIN_TX = 4
ICT_PIN_RX = 5

RESET_BTN_PIN_TX = 16

#endregion
# ========================================================

# ========================================================
#region General

VERSION_NO = "V1.0"

#endregion
# ========================================================