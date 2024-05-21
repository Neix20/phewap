from phew import connect_to_wifi, is_connected_to_wifi, logging

from ict_pico import uart_main
from ws_server import server_main

from utils import clsConst

# ========================================================
#region Constants

VGT_WIFI_CREDS = { "ssid": "wifi", "password": "password", "ip_address": "127.0.0.1", "mac_address": "127.0.0.1" }

#endregion
# ========================================================

def main():

    data = "Ict Bill"

    # Read From File
    try:
        with open(clsConst.EXECUTION_FILE, "r") as file:
            data = file.read()
        file.close()
    except Exception as ex:
        # By Default It Should be Ict Bill Mode
        print(f"Exception: {ex}")

    # Program To Run
    log_entry = "Running program {} ....".format(data)
    logging.info(log_entry)

    if data == "Ict Bill" and False:
        # Do The Max Attempts
        wifi_online, WIFI_ONLINE_TIME = 1, 3

        while wifi_online <= WIFI_ONLINE_TIME:
            ip_address, mac_address = connect_to_wifi(VGT_WIFI_CREDS["ssid"], VGT_WIFI_CREDS["password"])

            if is_connected_to_wifi():
                VGT_WIFI_CREDS["ip_address"] = ip_address
                VGT_WIFI_CREDS["mac_address"] = mac_address
                logging.info(f"Connected to wifi, IP address {ip_address}, Mac Address {mac_address}")
                break
            else :
                wifi_online += 1

        uart_main(VGT_WIFI_CREDS)
    elif data == "WiFi Server" or True:
        # wifi_server()
        server_main()

main()