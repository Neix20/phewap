
import os
import gc
import machine
import utime
import ujson
import _thread

from machine import Pin, UART
from umqtt.simple import MQTTClient

from phew import is_connected_to_wifi, logging

from utils import clsUtils, clsConst
gc.collect()

# ========================================================
#region General Utilities

def convert_str_hex(data):
    data = int(data, 16)
    data = data.to_bytes(1, 'big')  # Convert to a single byte in big-endian format
    return data

#endregion
# ========================================================

# ========================================================
#region Const

ack_s1_chk, ACK_S1_CHK_LIMIT = 1, 4
ack_s3_chk, ACK_S3_CHK_LIMIT = 1, 2

#endregion
# ========================================================

# ========================================================
#region WiFi Connection, UART, Message Queue

def gen_mqtt_client():

    global ack_s1_chk
    global ack_s3_chk

    global client

    if client != None:
        return client

    # Generate MQTT Client
    if ip_address == "127.0.0.1":
        return None

    def callback(topic, msg):
        
        logging.info("Received message on topic: {}, message: {}".format(topic, msg))

        # Add your message handling logic here

        mb_uart = clsUtils.gen_mb_uart()
        ict_uart = clsUtils.gen_ict_uart()

        # Two Types of Message:

        # 1. Check Device Status to ICT Device
        # 2. Send Several Cash Status to MB Device

        global ack_s1_chk
        global ack_s3_chk

        try:
            msg = ujson.loads(msg)

            mqtt_action = "S1"

            if "Action" in msg: 
                mqtt_action = msg["Action"]

            if mqtt_action == "S1":
                status = msg["Status"]

                # Provide Acknowldgement
                if status == "00":
                    ack_s1_chk = 10

            if mqtt_action == "S3":
                status = msg["Status"]

                # Provide Acknowldgement
                if status == "00":
                    ack_s3_chk = 10

            if mqtt_action == "S5" and not clsUtils.is_just_restarted():
                # Check If Machine Just Restarted
                clsUtils.machine_reset()

            if mqtt_action == "S4":
                
                ict_command_ls = msg["Amount"]

                for ict_command in ict_command_ls:

                    ict_command += "10"

                    for ind in range(0, len(ict_command) , 2):
                        command = ict_command[ind:ind + 2]

                        command = convert_str_hex(command)
                        mb_uart.write(command)

                        # logging.info("Sending Data to MB: {}".format(command.hex()))
                        utime.sleep(.5)

                # Action Data, Send Status Done
                data = {
                    "MachineId": client_id,
                    "Action": "A4"
                }
                data = clsUtils.gen_request(data)

                # Send Data
                data = ujson.dumps(data)
                mqtt_pub(client, data)

        except Exception as ex:
            print(f"gen_mqtt_client | Exception: {ex}")

    # Instantiate MQTT client
    logging.info("Connecting to MQTT Broker...")
    client = MQTTClient(
        client_id=client_id, 
        server=clsConst.MQTT_HOSTNAME, 
        port=clsConst.MQTT_PORT, 
        user=clsConst.MQTT_USERNAME, 
        password=clsConst.MQTT_PASSWORD,
        keepalive=135
    )

    # Set callback function
    client.set_callback(callback)

    # Connect to MQTT broker
    client.connect()

    # Subscribe to topic
    client.subscribe("vgppq/{}".format(client_id))

    logging.info(f"Client now publishing to topic {clsConst.ICT_TOPIC} ...")

    while True:
        # Action Data, Publish Client Id To Server
        data = {
            "MachineId": client_id,
            "Action": "A1"
        }
        data = clsUtils.gen_request(data)

        # Send Data
        data = ujson.dumps(data)
        mqtt_pub(client, data)

        # Wait For Message Queue
        try:
            if client != None:
                client.check_msg()
        except Exception as ex:
            print(f"Exception: {ex}")

        if ack_s1_chk >= ACK_S1_CHK_LIMIT:
            break

        ack_s1_chk += 1
        utime.sleep(2)

    ack_s1_chk = 1
    logging.info("Connection to MQTT Broker has been established...")
    gc.collect()

    return client

# Function to send hex signal
def send_hex_signal(uart, hex_value):

    # Define the hexadecimal data you want to send
    hex_data = bytearray(hex_value)

    # Send the hexadecimal data over UART
    uart.write(hex_data)

def mqtt_pub(client, data):
    if client == None:
        return
    try:
        logging.info(data)
        client.publish(clsConst.ICT_TOPIC, data)
    except Exception as ex:
        raise ex

#endregion
# ========================================================


# ========================================================
#region Pico Multi-Thread UART, Button Reset, Poll Check, Message Queue

def pico_btn_poll_msg():

    mb_uart = clsUtils.gen_mb_uart()
    button = clsUtils.gen_reset_button()

    btn_online, BTN_ONLINE_TIME = 1, 20
    poll_chk, POL_CHK_TIME = 1, 600

    wifi_chk, WIFI_CHK_TIME = 1, 3 * 600

    error_chk, ERROR_CHK_TIME = 1, 8

    utime.sleep(5)

    client = gen_mqtt_client()

    while True:
        try:

            # Check WiFi Connection Every 3 Minutes
            if wifi_chk % WIFI_CHK_TIME == 0:
                if not is_connected_to_wifi():
                    logging.error("Device has disconnected from WiFi {} ...".format(wifi_ssid))

                    # Reset Machine
                    clsUtils.machine_reset()
                else:
                    logging.info("Device is still connected to WiFi {} ...".format(wifi_ssid))

                wifi_chk = 1

            try:
                if client != None:
                    client.check_msg()
            except Exception as ex2:
                logging.error("client.check_msg | Exception: {}".format(ex2))

                if error_chk % ERROR_CHK_TIME == 0:
                    # Reset Machine
                    clsUtils.machine_reset()

                error_chk += 1
    
            # Poll Every Minute
            if poll_chk % POL_CHK_TIME == 0:
    
                # Action Data, Publish Message MotherBoard and Ict Board is Online
                data = {
                    "MachineId": client_id,
                    "Action": "A2",
                    "ICTStatus": "00" if ict_online else "01",
                    "MBStatus": "00" if mb_online else "01"
                }
                data = clsUtils.gen_request(data)
    
                # Push To Message Queue
                data = ujson.dumps(data)
                mqtt_pub(client, data)
    
                poll_chk = 1
    
            # Button Check
            if btn_online % BTN_ONLINE_TIME == 0:
    
                # Whenever I Press Button, IT will always RESET WiFi, and set program to WiFi Mode
                clsUtils.write_to_btn_file("WiFi Server")
    
                # Remove WiFi File
                try:
                    os.remove(clsConst.WIFI_FILE)
                except Exception as ex2:
                    logging.error("os_remove | Exception: {}".format(ex2))
    
                # Reset Machine
                clsUtils.machine_reset()
    
                # Reset Everything
                btn_online = 1
    
            if button.value() == 0:
                btn_online += 1
            else:
                btn_online -= 1
                btn_online = max(btn_online, 1)
    
            poll_chk += 1
            wifi_chk += 1

            gc.collect()
            utime.sleep(.1)
        except Exception as ex:
            logging.error(f"pico_btn_poll_msg | Exception: {ex}")

def uart_main(wifi_creds):

    #region Message Queue
    global client_id
    global ip_address
    global mb_online
    global ict_online
    global wifi_ssid
    global wifi_pswd

    wifi_ssid = wifi_creds["ssid"]
    wifi_pswd = wifi_creds["password"]
    ip_address = wifi_creds["ip_address"]

    client_id = "VGT_{}".format(wifi_creds["mac_address"])
    client_id = client_id.replace(":", "")

    client = gen_mqtt_client()
    #endregion

    # Multi-Threading
    _thread.start_new_thread(pico_btn_poll_msg, ())

    ict_chk_status, ICT_CHK_STATUS_TIME = 1, 150
    error_chk, ERROR_CHK_TIME = 1, 5

    # Main loop
    while True:
        try:

            if ict_chk_status % ICT_CHK_STATUS_TIME == 0:
    
                logging.info("Checking Device Status...")

                utime.sleep(.1)
                logging.info("ICT Device has return acknowledgement...")
                
                ict_chk_status = 1
            
            ict_chk_status += 1
            gc.collect()
            utime.sleep(.1)  # Wait for a short time before checking again
        except Exception as ex:
            logging.error(f"uart_main | Exception: {ex}")
            if error_chk % ERROR_CHK_TIME == 0:
                # Reset Machine
                clsUtils.machine_reset()
            error_chk += 1


#endregion
# ========================================================

# ========================================================
# Main Program
# ========================================================

client, client_id, ip_address = None, "", "127.0.0.1"
wifi_ssid, wifi_pswd = "", ""
mb_online, ict_online = False, False