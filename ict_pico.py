import os
import machine
import utime
import ujson
import _thread

from machine import Pin, UART
from umqtt.simple import MQTTClient

from phew import logging

from utils import clsUtils, clsConst

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
    # logging.info("Connecting to MQTT Broker...")
    client = MQTTClient(client_id, clsConst.MQTT_HOSTNAME, clsConst.MQTT_PORT, clsConst.MQTT_USERNAME, clsConst.MQTT_PASSWORD)

    # Set callback function
    client.set_callback(callback)

    # Connect to MQTT broker
    client.connect()

    # Subscribe to topic
    client.subscribe("vgppq/{}".format(client_id))

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
        client.check_msg()

        if ack_s1_chk >= ACK_S1_CHK_LIMIT:
            break

        ack_s1_chk += 1
        utime.sleep(2)

    ack_s1_chk = 1

    # logging.info("Connection to MQTT Broker has been established...")

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
        client.publish(clsConst.ICT_TOPIC, data.encode())
    except Exception as ex:
        print()
        raise ex

#endregion
# ========================================================


# ========================================================
#region Pico Multi-Thread UART, Button Reset, Poll Check, Message Queue

def pico_btn_poll_msg():

    global pico_btn_poll_msg_thread

    mb_uart = clsUtils.gen_mb_uart()
    button = clsUtils.gen_reset_button()

    btn_online, BTN_ONLINE_TIME = 1, 20
    poll_chk, POL_CHK_TIME = 1, 600

    utime.sleep(5)

    client = gen_mqtt_client()

    while True:
        try:

            if client != None:
                client.check_msg()
    
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
                    print(f"os_remove | Exception: {ex2}")
    
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
            utime.sleep(.1)
        except Exception as ex:
            logging.error(f"pico_btn_poll_msg | Exception: {ex}")

def uart_main(wifi_creds):

    #region Message Queue
    global client_id
    global ip_address
    global mb_online
    global ict_online

    global ack_s3_chk

    mb_uart = clsUtils.gen_mb_uart()
    ict_uart = clsUtils.gen_ict_uart()

    ip_address = wifi_creds["ip_address"]

    client_id = "VGT_{}".format(wifi_creds["mac_address"])
    client_id = client_id.replace(":", "")

    client = gen_mqtt_client()
    #endregion

    # Multi-Threading
    _thread.start_new_thread(pico_btn_poll_msg, ())

    last_ict_command, ict_stack, money_amount = "", [], 0
    ict_chk_status, ICT_CHK_STATUS_TIME = 1, 150

    # Check If Device Has Been Deactivated
    send_hex_signal(ict_uart, [0x0c])

    # Main loop
    while True:

        try:
            # ICT Device: Periodically Check Status of ICT Device
            if ict_chk_status % ICT_CHK_STATUS_TIME == 0:
    
                logging.info("Checking Device Status...")
    
                send_hex_signal(ict_uart, [0x0c])
                logging.info("Sending data to ICT: 0C")
    
                ict_chk_online, ICT_CHK_ONLINE_TIME = 1, 150
    
                while True:
    
                    # Check Thread If Device is Online
                    if ict_chk_online % ICT_CHK_ONLINE_TIME == 0:
                        logging.info("ICT Device did not return acknowledgement...")
                        ict_chk_online = 1
                        ict_online = False
                        break
    
                    if ict_uart.any():
                        ict_data = ict_uart.read()
                        last_ict_command = ict_data.hex()
                        logging.info(f"Incoming data from ICT: {last_ict_command}")
                        break
    
                    ict_chk_online += 1
                    utime.sleep(.1)
    
                ict_chk_status = 1
    
            # MB Device: Check if there is data available to read
            if mb_uart.any(): 
    
                mb_data = mb_uart.read()
                mb_data = mb_data.hex()
    
                logging.info(f"Incoming data from MB: {mb_data}")
    
                if "02" in mb_data:
                    # Log Message
                    mb_online = True
                    logging.info("MB Device is now online...")
    
                    # Send To Ict As Well
                    send_hex_signal(ict_uart, [0x02])
                    logging.info("ICT Device is now online...")
    
            # ICT Device: Check if there is data available to read 
            if ict_uart.any(): 
    
                # Read 10 bytes of data
                ict_data = ict_uart.read()
    
                # Convert To Hex Data
                last_ict_command = ict_data.hex()
    
                # Ict Online Status
                ict_online = True
    
                logging.info(f"Incoming data from ICT: {last_ict_command}")
    
            # ICT Device: Check When Money has been Deposited
            if "10" in last_ict_command:
    
                logging.info("MotherBoard has received cash...")
                # utime.sleep(.5)
    
                # Send 10 To Motherboard
                send_hex_signal(mb_uart, [0x10])
                logging.info("Sending Data to MB: {}".format(last_ict_command))

                # Log Number of Cash
                money_amount += 1
                logging.info("Note No.: {}".format(money_amount))

                # Send Data
                data = {
                    "MachineId": client_id,
                    "Amount": ict_stack[0],
                    "Action": "A3",
                    "CreatedDate": clsUtils.datetime_string(),
                    "Note No.": money_amount
                }
                data = clsUtils.gen_request(data)

                # Problem is 2nd Loop
                while True:
    
                    # Push To Message Queue
                    data = ujson.dumps(data)
                    mqtt_pub(client, data)
        
                    # Wait For Message Queue
                    client.check_msg()
                    utime.sleep(.5)

                    if ack_s3_chk >= ACK_S3_CHK_LIMIT:
                        break
    
                    ack_s3_chk += 1
    
                ack_s3_chk = 1
                ict_stack = []
                last_ict_command = ""
    
            # ICT Device: Check When Device has been initialized
            if "808f" in last_ict_command:
    
                logging.info("Initializing ICT Device...")
    
                command = convert_str_hex("80")
                mb_uart.write(command)
    
                utime.sleep(.5)
    
                command = convert_str_hex("8f")
                mb_uart.write(command)
    
                mb_chk_payment, MB_CHK_PAYMENT_TIME = 1, 100
    
                while True:
    
                    if mb_chk_payment % MB_CHK_PAYMENT_TIME == 0:
                        logging.info("MotherBoard did not return acknowledgement....")
                        mb_chk_payment = 1
                        mb_online = False
                        break
    
                    if mb_uart.any():
    
                        mb_data = mb_uart.read()
                        mb_data = mb_data.hex()
    
                        logging.info(f"Incoming data from MB: {mb_data}")
    
                        if "02" in mb_data:
                            # Send Hex Signal From Motherboard
                            send_hex_signal(ict_uart, [0x02])
                            logging.info("MotherBoard has returned acknowledgement....")
    
                            break
    
                    mb_chk_payment += 1
                    utime.sleep(.1)
    
                last_ict_command = ""
    
            # ICT Device: Check When Ict Device is not accepting Cash
            if "5e" in last_ict_command:
    
                command = convert_str_hex("3e")
                ict_uart.write(command)
    
                utime.sleep(.5)
    
                last_ict_command = ""
    
            # ICT Device: Check When User has insert Money
            try:
                # 8140
                ict_bill_ind = last_ict_command.find("81")
                if ict_bill_ind != -1 and ict_bill_ind + 2 < len(last_ict_command):

                    last_ict_command = last_ict_command[ict_bill_ind:ict_bill_ind + 4]
    
                    bill_a = last_ict_command[:2]
                    bill_b = last_ict_command[2:]

                    last_ict_command = ""
    
                    if bill_a == str(81) and bill_b in [str(i) for i in range(40, 44)]:
    
                        # Write to Log
                        logging.info("Device has accepted bill....")
    
                        # Wait For MotherBoard Signal Here
                        command = convert_str_hex(bill_a)
                        mb_uart.write(command)
                        logging.info("Sending Data to MB: {}".format(bill_a))
    
                        utime.sleep(.5)
    
                        command = convert_str_hex(bill_b)
                        mb_uart.write(command)
                        logging.info("Sending Data to MB: {}".format(bill_b))
    
                        mb_chk_payment, MB_CHK_PAYMENT_TIME = 1, 100
    
                        while True:
    
                            # .1 * 10 = 1 Seconds
                            # .1 * 10 * 10 = 10 seconds
                            if mb_chk_payment % MB_CHK_PAYMENT_TIME == 0:
                                logging.info("MotherBoard did not return acknowledgement....")
                                mb_chk_payment = 1
                                mb_online = False
                                break
    
                            if mb_uart.any():
    
                                mb_data = mb_uart.read()
                                mb_data = mb_data.hex()
    
                                logging.info(f"Incoming data from MB: {mb_data}")
    
                                if "02" in mb_data:
    
                                    # Append Bill to Ict Stack
                                    ict_stack.append(last_ict_command)
    
                                    # Send Hex Signal From Motherboard
                                    send_hex_signal(ict_uart, [0x02])
                                    logging.info("MotherBoard has returned acknowledgement....")
    
                                    break
    
                            mb_chk_payment += 1
                            utime.sleep(.1)
            except Exception as ex2:
                print()
                raise ex2
    
            # ICT Device: Reset Last Ict Device Command
            if last_ict_command in clsConst.ICT_RESPONSE_CODE:
                res = clsConst.ICT_RESPONSE_CODE[last_ict_command]

                logging.info(res)
                last_ict_command = ""
        except Exception as ex:
            logging.error(f"uart_main | Exception: {ex}")

        ict_chk_status += 1
        utime.sleep(.1)  # Wait for a short time before checking again

#endregion
# ========================================================

# ========================================================
# Main Program
# ========================================================

client, client_id, ip_address = None, "", "127.0.0.1"
mb_online, ict_online = False, False