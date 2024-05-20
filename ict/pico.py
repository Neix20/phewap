import machine
import network
import utime
import urandom
import ubinascii
import ujson

from umqtt.simple import MQTTClient

# ========================================================
#region Constants

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
    "5e": "Controller Disable Bill",
}

MQTT_USERNAME = b'gan'
MQTT_PASSWORD = b'123456'
MQTT_HOSTNAME = b'47.254.229.107'
MQTT_PORT = 1883

ICT_TOPIC = "ict/subscribe"
PICO_LOCATION = "VigTech"

MB_PIN_TX = 12
MB_PIN_RX = 13

ICT_PIN_TX = 4
ICT_PIN_RX = 5

#endregion
# ========================================================

# ========================================================
#region Logging

def convert_str_hex(data):

    data = int(data, 16)
    data = data.to_bytes(1, 'big')  # Convert to a single byte in big-endian format

    return data

def info_log(data):

    dt = gen_today_dt()

    fp = "{}.log".format(dt)

    ts = gen_ts()

    try:
        with open(fp, "a", encoding="utf-8") as file:
            # json.dump(data, file)
            file.write("{} at {} | INFO | {} \n".format(dt, ts, data))

        file.close()

        print("{} at {} | INFO | {}".format(dt, ts, data))
    except Exception as ex:
        print(f"Error! Unable to write Data to {fp}! Exception: {ex}")

def error_log(data):

    dt = gen_today_dt()
    
    fp = "exception_{}.log".format(dt)

    ts = gen_ts()

    try:
        with open(fp, "a", encoding="utf-8") as file:
            # json.dump(data, file)
            file.write("{} at {} | ERROR | {} \n".format(dt, ts, data))

        file.close()

        print("{} at {} | ERROR | {}".format(dt, ts, data))
    except Exception as ex:
        print(f"Error! Unable to write Data to {fp}! Exception: {ex}")

#endregion
# ========================================================

# ========================================================
#region General Utilities

def gen_random_client_id(length=8):
    rand_bytes = bytearray(urandom.getrandbits(8) for _ in range(length))
    res = ubinascii.hexlify(rand_bytes).decode()
    return f"pico_{res}"

def gen_today_dt():
    dt = machine.RTC().datetime()
    return "{0:04d}-{1:02d}-{2:02d}".format(*dt)

def gen_ts():
    dt = machine.RTC().datetime()
    return "{4:02d}:{5:02d}:{6:02d}".format(*dt)

#endregion
# ========================================================

# ========================================================
#region WiFi Connection, UART, Message Queue

def gen_mqtt_client():

    def callback(topic, msg):
        
        info_log("Received message on topic: {}, message: {}".format(topic, msg))

        # Add your message handling logic here

        global mb_uart
        global ict_uart

        # Two Types of Message:

        # 1. Check Device Status to ICT Device
        # 2. Send Several Cash Status to MB Device

        try:
            msg = ujson.loads(msg)

            ict_command = msg["command"]

            if msg["machine_code"] == 20:

                if len(ict_command) >= 4:
                    for ind in range(0, len(ict_command) , 2):
                        command = ict_command[ind:ind + 2]
                        command = convert_str_hex(command)
                        mb_uart.write(command)
                        info_log("Sending Data to MB: {}".format(command))
                    
                        utime.sleep(.5)

                    utime.sleep(2)
                    send_hex_signal(mb_uart, [0x10])
                else:
                    command = convert_str_hex(ict_command)
                    mb_uart.write(command)
                    info_log("Sending Data to MB: {}".format(command))
            
            if msg["machine_code"] == 10:
                command = convert_str_hex(ict_command)
                ict_uart.write(command)
                info_log("Sending Data to ICT: {}".format(command))

        except Exception as ex:
            error_log(f"Exception: {ex}")

    global client_id

    client_id = gen_random_client_id()
    info_log("Generated Client ID: {}".format(client_id))

    # Instantiate MQTT client
    info_log("Connecting to MQTT Broker...")
    client = MQTTClient(client_id, MQTT_HOSTNAME, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD)

    # Set callback function
    client.set_callback(callback)

    # Connect to MQTT broker
    client.connect()

    # Subscribe to topic
    client.subscribe(f"{client_id}/subscribe")

    # Publish Client Id To Server
    data = {
        "client_id": client_id,
        "location": PICO_LOCATION,
        "ip_address": ip_address,
        "machine_code": 10
    }
    data = ujson.dumps(data)

    client.publish(ICT_TOPIC, data)
    info_log("Connection to MQTT Broker has been established...")

    return client

# Function to send hex signal
def send_hex_signal(uart, hex_value):

    # Define the hexadecimal data you want to send
    hex_data = bytearray(hex_value)

    uart.write(hex_data)  # Send the hexadecimal data over UART

def mqtt_pub(client, data):
    if client == None:
        return
    client.publish(ICT_TOPIC, data.encode())

#endregion
# ========================================================

# ========================================================
#region PICO UART PYTHON CODE

def uart_main(wifi_creds):

    global mb_uart
    global ict_uart
    global ip_address

    ip_address = wifi_creds["ip_address"]

    # Generate MQTT Client
    if ip_address != "127.0.0.1":
        client = gen_mqtt_client()
    else:
        client = None

    mb_online, ict_online = False, False
    ict_data, last_ict_command, ict_stack = "", "", []

    ict_chk_status, ICT_CHK_STATUS_TIME = 1, 300

    # Check If Device Has Been Deactivated
    send_hex_signal(ict_uart, [0x0c])

    # Main loop
    while True:

        # Check Client
        if client != None:
            client.check_msg()

        if ict_chk_status % ICT_CHK_STATUS_TIME == 0:
            info_log("Checking Device Status...")
            send_hex_signal(ict_uart, [0x0c])
            info_log("Sending data to ICT: 0C")

            ict_chk_online, ict_chk_online_time = 1, 300

            while True:
                # Check Thread If Device is Online
                if ict_chk_online % ict_chk_online_time == 0:
                    ict_online = False
                    info_log("ICT Device did not return acknowledgement...")
                    break

                if ict_uart.any():
                    ict_data = ict_uart.read()
                    last_ict_command = ict_data.hex()
                    info_log(f"Incoming data from ICT: {last_ict_command}")
                    break

                ict_chk_online += 1
                utime.sleep(.1)

            ict_chk_status = 1

        # Check if there is data available to read
        if mb_uart.any(): 
            mb_data = mb_uart.read()
            mb_data = mb_data.hex()

            info_log(f"Incoming data from MB: {mb_data}")

            if mb_data == "02":
                # Publish Message MotherBoard is Online

                data = {
                    "msg": "MB Device is now online...",
                    "client_id": client_id,
                    "location": PICO_LOCATION,
                    "ip_address": ip_address,
                    "machine_code": 10
                }
                data = ujson.dumps(data)

                mqtt_pub(client, data)

                # Log Message
                info_log("MB Device is now online...")

                mb_online = True

        if ict_uart.any():  # Check if there is data available to read

            # Read 10 bytes of data
            ict_data = ict_uart.read()

            # Convert To Hex Data
            last_ict_command = ict_data.hex()

            info_log(f"Incoming data from ICT: {last_ict_command}")

        if last_ict_command in ["808f", "5e", "3e"]:
            ict_online = True

        if mb_online and ict_online and last_ict_command == "10":

            info_log("MotherBoard has received cash...")

            # Send 10 To Motherboard
            utime.sleep(2)
            send_hex_signal(mb_uart, [0x10])
            info_log("Sending Data to MB: 10")

            # There Will be a Queue Here to Pop
            ict_stack.append(last_ict_command)

            for ict_command in ict_stack:

                data = {
                    "command": ict_command,
                    "client_id": client_id,
                    "location": PICO_LOCATION,
                    "ip_address": ip_address,
                    "machine_code": 10
                }
                data = ujson.dumps(data)

                # Push To Message Queue
                mqtt_pub(client, data)

            ict_stack = []

            last_ict_command = ""

        if mb_online and ict_online and last_ict_command == "808f":

            command = convert_str_hex("80")
            ict_uart.write(command)

            utime.sleep(.5)

            command = convert_str_hex("8f")
            ict_uart.write(command)

            info_log("Sending Data to ICT: 80 8f")

            info_log("Initializing ICT Device....")

            send_hex_signal(ict_uart, [0x02])
            info_log("ICT Device is now online...")

            last_ict_command = ""

        if mb_online and ict_online and last_ict_command == "5e":
            send_hex_signal(ict_uart, [0x3e])
            info_log("ICT Device is now changing to accept bills...")

            last_ict_command = ""

        try:
            if mb_online and ict_online and len(last_ict_command) >= 4:

                bill_a = last_ict_command[:2]
                bill_b = last_ict_command[2:]

                if bill_a == str(81) and bill_b in [str(i) for i in range(40, 46)]:

                    # Write to Log
                    info_log("Device has accepted bill....")

                    # Wait For MotherBoard Signal Here
                    command = convert_str_hex("81")
                    mb_uart.write(command)
                    info_log("Sending Data to MB: 81")

                    utime.sleep(.5)

                    command = convert_str_hex(bill_b)
                    mb_uart.write(command)
                    info_log(f"Sending Data to MB: {bill_b}")

                    mb_chk_payment, MB_CHK_PAYMENT_TIME = 1, 100

                    while True:

                        # .1 * 10 = 1 Seconds
                        # .1 * 10 * 10 = 10 seconds
                        if mb_chk_payment % MB_CHK_PAYMENT_TIME == 0:
                            info_log("MotherBoard did not return acknowledgement....")
                            mb_chk_payment = 1
                            mb_online = False
                            break

                        if mb_uart.any():

                            mb_data = mb_uart.read()
                            mb_data = mb_data.hex()

                            info_log(f"Incoming data from MB: {mb_data}")

                            if mb_data == "02":

                                ict_stack.append(last_ict_command)

                                # Send Hex Signal From Motherboard
                                send_hex_signal(ict_uart, [0x02])
                                info_log("MotherBoard has returned acknowledgement....")

                                break

                        mb_chk_payment += 1
                        utime.sleep(.1)

        except Exception as ex:
            error_log(f"Exception: {ex}")

        if mb_online and ict_online and last_ict_command in ICT_RESPONSE_CODE:

            res = ICT_RESPONSE_CODE[last_ict_command]
            
            info_log(res)
            last_ict_command = ""

        ict_chk_status += 1
        utime.sleep(.1)  # Wait for a short time before checking again

#endregion
# ========================================================

# ========================================================
# Main Program
# ========================================================

info_log("MB UART is Starting....")

mb_uart = machine.UART(0, baudrate=9600, tx=machine.Pin(MB_PIN_TX), rx=machine.Pin(MB_PIN_RX))
mb_uart.init(bits=8, parity=None, stop=1)

info_log("ICT UART is Starting....")

ict_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(ICT_PIN_TX), rx=machine.Pin(ICT_PIN_RX))
ict_uart.init(bits=8, parity=None, stop=1)

client_id, ip_address = "", ""