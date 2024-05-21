
from . import clsConst

import utime
import machine

from machine import Pin, UART

from phew import logging

def write_to_btn_file(data):

    # Remove File First
    try:
        with open(clsConst.EXECUTION_FILE, "w") as file:
            file.write(data)

        file.close()
    except Exception as ex:
        print(f"Error! Unable to write Data to {clsConst.EXECUTION_FILE}! Exception: {ex}")

def machine_reset():
    utime.sleep(1)
    logging.info("Resetting...")
    machine.reset()

mb_uart = UART(0, baudrate=9600, tx=Pin(clsConst.MB_PIN_TX), rx=Pin(clsConst.MB_PIN_RX))
mb_uart.init(bits=8, parity=None, stop=1)

ict_uart = UART(1, baudrate=9600, tx=Pin(clsConst.ICT_PIN_TX), rx=Pin(clsConst.ICT_PIN_RX))
ict_uart.init(bits=8, parity=None, stop=1)

button = Pin(clsConst.RESET_BTN_PIN_TX, Pin.IN, Pin.PULL_UP)

led = Pin('LED', Pin.OUT)

def gen_mb_uart():
    logging.info("MB UART is Starting....")
    return mb_uart

def gen_ict_uart():
    logging.info("ICT UART is Starting....")
    return ict_uart

def gen_reset_button():
    logging.info("Registering Reset Button...")
    return button

def gen_led():
    logging.info("Registering LED Pins...")
    return led