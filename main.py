from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server, logging
from phew.template import render_template

from ict.pico import uart_main
from machine import Pin

import json
import machine
import os
import utime
import _thread

# AP_NAME = "VG PPQ"
# AP_DOMAIN = "vqrs-pico-wifi.net"
# AP_TEMPLATE_PATH = "ap_templates"
# APP_TEMPLATE_PATH = "app_templates"
# WIFI_FILE = "wifi.json"
# WIFI_MAX_ATTEMPTS = 3
# VGT_WIFI_CREDS = { "ssid": "vigtech@unifi", "password": "password" }

# def machine_reset():
#     utime.sleep(1)
#     print("Resetting...")
#     machine.reset()

# def setup_mode():
#     logging.info("Entering setup mode...")
    
#     def ap_index(request):
#         if request.headers.get("host").lower() != AP_DOMAIN.lower():
#             return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN.lower())

#         return render_template(f"{AP_TEMPLATE_PATH}/index.html")

#     def ap_configure(request):
#         logging.info("Saving wifi credentials...")

#         with open(WIFI_FILE, "w") as f:
#             json.dump(request.form, f)
#             f.close()

#         # Reboot from new thread after we have responded to the user.
#         _thread.start_new_thread(machine_reset, ())
#         return render_template(f"{AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
#     def ap_catch_all(request):
#         if request.headers.get("host") != AP_DOMAIN:
#             return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN)

#         return "Not found.", 404

#     server.add_route("/", handler = ap_index, methods = ["GET"])
#     server.add_route("/configure", handler = ap_configure, methods = ["POST"])
#     server.set_callback(ap_catch_all)

#     ap = access_point(AP_NAME)
#     ip = ap.ifconfig()[0]
#     dns.run_catchall(ip)

# def application_mode(creds):
    
#     logging.info("Entering application mode.")

#     def app_index(request):
#         return render_template(f"{APP_TEMPLATE_PATH}/index.html", wifi_name = creds["ssid"])
    
#     def app_vgppq(request):
#         uart_main(creds)
#         return "OK"
    
#     def app_reset(request):
#         # Deleting the WIFI configuration file will cause the device to reboot as
#         # the access point and request new configuration.
#         os.remove(WIFI_FILE)
#         # Reboot from new thread after we have responded to the user.
#         _thread.start_new_thread(machine_reset, ())
#         return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

#     def app_catch_all(request):
#         return "Not found.", 404

#     server.add_route("/", handler = app_index, methods = ["GET"])
#     server.add_route("/vgppq", handler = app_vgppq, methods = ["GET"])
#     server.add_route("/reset", handler = app_reset, methods = ["GET"])

#     # Add other routes for your application...
#     server.set_callback(app_catch_all)

# # Figure out which mode to start up in...
# try:
#     os.stat(WIFI_FILE)

#     # File was found, attempt to connect to wifi...
#     with open(WIFI_FILE) as f:
#         wifi_current_attempt = 1
#         wifi_credentials = json.load(f)
        
#         while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
#             ip_address = connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])
#             wifi_credentials["ip_address"] = ip_address

#             if is_connected_to_wifi():
#                 logging.info(f"Connected to wifi, IP address {ip_address}")
#                 break
#             else:
#                 wifi_current_attempt += 1

#         # Push To Message Queue
#         if is_connected_to_wifi():
#             application_mode(wifi_credentials)
#         else:
#             # Bad configuration, delete the credentials file, reboot
#             # into setup mode to get new credentials from the user.
#             logging.error("Bad wifi connection!")
#             os.remove(WIFI_FILE)
#             machine_reset()

# except Exception:
#     # Either no wifi configuration file found, or something went wrong, 
#     # so go into setup mode.
#     setup_mode()

# # Start the web server...
# server.run()

# while True:
#     ip_address = connect_to_wifi(VGT_WIFI_CREDS["ssid"], VGT_WIFI_CREDS["password"])

#     VGT_WIFI_CREDS["ip_address"] = ip_address

#     if is_connected_to_wifi():
#         logging.info(f"Connected to wifi, IP address {ip_address}")
#         break

# uart_main(VGT_WIFI_CREDS)

ICT_PIN_TX = 4

button = Pin(ICT_PIN_TX, Pin.IN, Pin.PULL_UP)

while True:
    if button.value() == 0:
        print("Button is Pressed")
    else:
        print("Button is not Pressed")
    utime.sleep(0.1)
