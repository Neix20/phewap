from phew import connect_to_wifi, is_connected_to_wifi, logging

from ict_pico import uart_main
from ws_server import server_main

from utils import clsConst, clsUtils

import utime
import ujson
import _thread

import os

# ========================================================
#region Constants

VGT_WIFI_CREDS = { "ssid": "wifi", "password": "password", "ip_address": "127.0.0.1", "mac_address": "127.0.0.1" }

#endregion
# ========================================================

# ========================================================
#region Utilities

def pico_reset_btn():

    button = clsUtils.gen_reset_button()

    btn_online, BTN_ONLINE_TIME = 1, 20

    while True:

        # Check Thread
        if pico_reset_btn_thread_flag == False:
            _thread.exit()

        # Button Check
        if btn_online % BTN_ONLINE_TIME == 0:

            # Whenever I Press Button, IT will always RESET WiFi, and set program to WiFi Mode
            clsUtils.write_to_btn_file("WiFi Server")

            # Remove WiFi File
            try:
                os.remove(clsConst.WIFI_FILE)
            except Exception as ex:
                print(f"Exception: {ex}")

            # Reset Machine
            clsUtils.machine_reset()

            # Reset Everything
            btn_online = 1

        if button.value() == 0:
            btn_online += 1
        else:
            btn_online -= 1
            btn_online = max(btn_online, 1)
            
        utime.sleep(.1)

#endregion
# ========================================================

pico_reset_btn_thread_flag = True

def main():

    global pico_reset_btn_thread_flag

    data = "Ict Bill"

    led = clsUtils.gen_led()

    # Show Power On
    for _ in range(4):
        led.toggle()
        utime.sleep(.5)

    # Read From File
    try:
        with open(clsConst.EXECUTION_FILE, "r") as file:
            data = file.read()
        file.close()
    except Exception as ex:
        # By Default It Should be Ict Bill Mode
        logging.error(f"Exception: {ex}")

    # Read From WiFi File
    try:
        with open(clsConst.WIFI_FILE) as file:
            wifi_creds = ujson.load(file)
            VGT_WIFI_CREDS.update(wifi_creds)

        file.close()
    except Exception as ex:
        # By Default It Should be Ict Bill Mode
        logging.error(f"Exception: {ex}")

    # Program To Run
    log_entry = "Running program {} ....".format(data)
    logging.info(log_entry)

    if data == "Ict Bill":

        _thread.start_new_thread(pico_reset_btn, ())

        utime.sleep(2)

        for _ in range(2):
            led.toggle()
            utime.sleep(.5)

        for _ in range(2):
            ip_address, mac_address = connect_to_wifi(VGT_WIFI_CREDS["ssid"], VGT_WIFI_CREDS["password"])

            if is_connected_to_wifi():

                VGT_WIFI_CREDS["ip_address"] = ip_address
                VGT_WIFI_CREDS["mac_address"] = mac_address

                logging.info(f"Connected to wifi, IP address {ip_address}, Mac Address {mac_address}")

                break

        pico_reset_btn_thread_flag = False

        # Show Signs it is either connected or not connected
        num_of_blink = 2
        if VGT_WIFI_CREDS["ip_address"] != "127.0.0.1":
            num_of_blink = 4
        
        for _ in range(num_of_blink):
            led.toggle()
            utime.sleep(.5)

        # Turn On Light
        utime.sleep(2)

        led.value(1)

        # Write To File "Ict Bill"
        clsUtils.write_to_btn_file("Ict Bill")

        uart_main(VGT_WIFI_CREDS)
        
    # For Some Reason, It Jumps to this, Meaning it Reset Twice
    elif data == "WiFi Server":

        utime.sleep(2)

        for _ in range(4):
            led.toggle()
            utime.sleep(.5)

        # Turn On Light
        utime.sleep(2)

        led.value(1)

        # Write To File "Ict Bill"
        clsUtils.write_to_btn_file("Ict Bill")
        
        # wifi_server()
        server_main()

main()