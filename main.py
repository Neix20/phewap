from phew import connect_to_wifi, is_connected_to_wifi, logging

from ict_pico import uart_main
from ws_server import server_main

from utils import clsConst, clsUtils

import utime
import ujson

# ========================================================
#region Constants

VGT_WIFI_CREDS = { "ssid": "wifi", "password": "password", "ip_address": "127.0.0.1", "mac_address": "127.0.0.1" }

#endregion
# ========================================================

led = clsUtils.gen_led()

def main():

    data = "Ict Bill"
    
    # Turn Off The Light
    led.value(0)

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

            # VGT_WIFI_CREDS["ssid"] = wifi_creds["ssid"]
            # VGT_WIFI_CREDS["password"] = wifi_creds["password"]

            VGT_WIFI_CREDS.update(wifi_creds)

        file.close()
    except Exception as ex:
        # By Default It Should be Ict Bill Mode
        logging.error(f"Exception: {ex}")

    # Program To Run
    log_entry = "Running program {} ....".format(data)
    logging.info(log_entry)

    if data == "Ict Bill":
        
        # Do The Max Attempts
        wifi_online, WIFI_ONLINE_TIME = 1, 3

        while wifi_online < WIFI_ONLINE_TIME:
            
            ip_address, mac_address = connect_to_wifi(VGT_WIFI_CREDS["ssid"], VGT_WIFI_CREDS["password"])

            if is_connected_to_wifi():
                VGT_WIFI_CREDS["ip_address"] = ip_address
                VGT_WIFI_CREDS["mac_address"] = mac_address
                logging.info(f"Connected to wifi, IP address {ip_address}, Mac Address {mac_address}")
                break
            else :
                wifi_online += 1

        # Toggle Light
        # Turn on LED Light for 5 Seconds
        blink_chk, BLINK_CHK_TIME = 1, 10
        while blink_chk % BLINK_CHK_TIME != 0:
            led.toggle()

            blink_chk += 1
            utime.sleep(.5)

        led.value(1)

        uart_main(VGT_WIFI_CREDS)
        
        # For Some Reason, It Jumps to this, Meaning it Reset Twice
    elif data == "WiFi Server":
        
        led.value(1)

        # Write To File "Ict Bill"
        clsUtils.write_to_btn_file("Ict Bill")
        
        # wifi_server()
        server_main()

main()