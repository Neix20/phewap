
from . import clsConst

import utime
import machine

from machine import Pin, UART

from phew import logging

# ========================================================
#region GPIO Pins

def gen_request(data):

    ts = utime.time()

    obj = {
        "TradeNo": "T{}".format(ts),
        "VersionNo": clsConst.VERSION_NO,
    }

    obj.update(data)

    return obj


def write_to_btn_file(data):

    # Remove File First
    try:
        logging.info("Writing {} to {}".format(data, clsConst.EXECUTION_FILE))
        with open(clsConst.EXECUTION_FILE, "w") as file:
            file.write(data)

        file.close()
    except Exception as ex:
        logging.error(f"Error! Unable to write Data to {clsConst.EXECUTION_FILE}! Exception: {ex}")

def machine_reset():
    utime.sleep(1)

    # Turn on LED Light for 5 Seconds
    blink_chk, BLINK_CHK_TIME = 1, 10
    while blink_chk % BLINK_CHK_TIME != 0:
        led.toggle()

        blink_chk += 1
        utime.sleep(.5)

    led.value(0)

    logging.info("Resetting...")
    machine.reset()

def datetime_string():
    dt = machine.RTC().datetime()
    return "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*dt)

#endregion
# ========================================================

# ========================================================
#region GPIO Pins

logging.info("MB UART is Starting....")

mb_uart = UART(0, baudrate=9600, tx=Pin(clsConst.MB_PIN_TX), rx=Pin(clsConst.MB_PIN_RX))
mb_uart.init(bits=8, parity=None, stop=1)

logging.info("ICT UART is Starting....")

ict_uart = UART(1, baudrate=9600, tx=Pin(clsConst.ICT_PIN_TX), rx=Pin(clsConst.ICT_PIN_RX))
ict_uart.init(bits=8, parity=None, stop=1)

logging.info("Registering Reset Button...")

button = Pin(clsConst.RESET_BTN_PIN_TX, Pin.IN, Pin.PULL_UP)

logging.info("Registering LED Pins...")

led = Pin('LED', Pin.OUT)

def gen_mb_uart():
    return mb_uart

def gen_ict_uart():
    return ict_uart

def gen_reset_button():
    return button

def gen_led():
    return led

#endregion
# ========================================================