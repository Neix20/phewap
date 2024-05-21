from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server, logging
from phew.template import render_template

import json
import machine
import os
import utime
import _thread

from machine import Pin, UART

from utils import clsConst, clsUtils

# For Resetting
led = clsUtils.gen_led()

def machine_reset():
    utime.sleep(1)

    # Turn on LED Light for 5 Seconds
    blink_chk, BLINK_CHK_TIME = 1, 10
    while blink_chk % BLINK_CHK_TIME != 0:
        led.toggle()

        blink_chk += 1
        utime.sleep(.5)

    logging.info("Resetting...")
    machine.reset()

def read_file(fp):
    with open(fp, "r") as f:
        data = f.read()
    
    f.close()

    return data

def setup_mode():

    logging.info("Entering setup mode...")
    
    def ap_index(request):
        if request.headers.get("host").lower() != clsConst.AP_DOMAIN.lower():
            return render_template(f"{clsConst.AP_TEMPLATE_PATH}/redirect.html", domain = clsConst.AP_DOMAIN.lower())
        
        # Read File
        vgppq_logo_data = read_file(clsConst.VG_PPQ_LOGO)
        wifi_a_data = read_file(clsConst.WIFI_A_IMG)
        wifi_b_data = read_file(clsConst.WIFI_B_IMG)

        return render_template(f"{clsConst.AP_TEMPLATE_PATH}/index.html", vgppq_logo = vgppq_logo_data, wifi_a = wifi_a_data, wifi_b = wifi_b_data)

    def ap_configure(request):
        logging.info("Saving wifi credentials...")

        with open(clsConst.WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()

        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())

        return render_template(f"{clsConst.AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != clsConst.AP_DOMAIN:
            return render_template(f"{clsConst.AP_TEMPLATE_PATH}/redirect.html", domain = clsConst.AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(clsConst.AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)

    # Write To File "Ict Bill"
    clsUtils.write_to_btn_file("Ict Bill")

def server_main():

    try:
        os.remove(clsConst.WIFI_FILE)
    except Exception as ex:
        print(f"Exception: {ex}")

    setup_mode()

    # Start the web server...
    server.run()
