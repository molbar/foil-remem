# nettools.py = connect to wifi networks
# Copyright (c) 2019 Clayton Darwin
# symple.design/clayton claytondarwin@gmail.com
import time
import network
import gc
import glovars
import log

gc.collect()
# setup on import
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
network.WLAN(network.AP_IF).active(False)

#wlan.scan()


# scan for WiFi LANs (access points)
def wlan_scan():
    from ubinascii import hexlify as temphex
    wlan = network.WLAN(network.STA_IF)
    state = wlan.active()  # save current state
    wlan.active(True)  # set state active
    for ssid, bssid, channel, RSSI, authmode, hidden in wlan.scan():
        ssid = ssid.decode('ascii')
        bssid = temphex(bssid).decode('ascii')
        if len(bssid) == 12:
            bssid = ':'.join([bssid[x:x + 2] for x in range(0, 12, 2)])
        authmode = ('OPEN', 'WEP', 'WPA-PSK', 'WPA2-PSK',
                    'WPA/WPA2-PSK')[min(4, max(0, authmode))]
        if hidden:
            hidden = True
        else:
            False
        #hidden = (False,True)[min(1,max(0,hidden))]
        print('Network AP:', [ssid, bssid, channel, RSSI, authmode, hidden])
    wlan.active(state)  # return to pervious state
    del temphex


# connect to WiFi AP
def wlan_connect(essid, password, timeout=15):
    print('Network Connect:', essid)
    #tm.scroll(essid)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return_value = ""
    if not wlan.isconnected():
        try:
            wlan.connect(essid, password)
        except (OSError, RuntimeError) as e:
            return_value = e

        time.sleep(0.1)
        for x in range(timeout):
            if wlan.isconnected():
                break
            time.sleep(1)
    if return_value == "":
        return_value = wlan.isconnected()
    print('Network Connect:', essid, return_value)

    return return_value


# disconnect from WiFi AP
def wlan_disconnect(timeout=15):
    print('Network Disconnect')
    wlan = network.WLAN(network.STA_IF)
    return_value = True
    if wlan.active():
        if wlan.isconnected():
            wlan.disconnect()
            time.sleep(0.1)
            for x in range(timeout):
                if not wlan.isconnected():
                    break
                time.sleep(1)
            return_value = not wlan.isconnected()
    wlan.active(False)
    print('Network Disonnect:', return_value)
    return return_value




#wlan_scan()


def connect_wifi():

    if not wlan.isconnected():
        wlan_scan()
        prio = glovars.wifi_prio.split(',')
        for i in prio:
            wifi_name = getattr(glovars, f"wifi_name{i}")
            password = getattr(glovars, f"password{i}")
            wlan_connect(wifi_name, password)
            if glovars.wdt_initialized == True:
                wdt.feed()
            if wlan.isconnected():
                glovars.wifi_status = "connected"
                print("connected to wifi")
                if not glovars.status == "startup":
                    log.log_sys("successful connection to wifi")
                else:
                    log.log_sys("successful connection to wifi startup")
                break
            else:
                glovars.wifi_status = "disconnected"
                log.log_err("Err3", "connect_wifi")
    else:
        glovars.wifi_status = "connected"
