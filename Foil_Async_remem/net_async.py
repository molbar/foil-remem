import asyncio
from ubinascii import hexlify as temphex
import network

import gc
import glovars
import log

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
network.WLAN(network.AP_IF).active(False)


async def wlan_scan():
    wlan = network.WLAN(network.STA_IF)
    state = wlan.active()  # Save current state
    wlan.active(True)  # Set state active
    for ssid, bssid, channel, RSSI, authmode, hidden in wlan.scan():
        ssid = ssid.decode('ascii')
        bssid = temphex(bssid).decode('ascii')
        if len(bssid) == 12:
            bssid = ':'.join([bssid[x:x + 2] for x in range(0, 12, 2)])
        authmode = ('OPEN', 'WEP', 'WPA-PSK', 'WPA2-PSK', 'WPA/WPA2-PSK')[min(4, max(0, authmode))]
        hidden = bool(hidden)
        print('Network AP:', [ssid, bssid, channel, RSSI, authmode, hidden])
    wlan.active(state)  # Return to previous state


async def wlan_connect(essid, password, timeout=15):
    print('Network Connect:', essid)
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return_value = ""
    if not wlan.isconnected():
        try:
            wlan.connect(essid, password)
        except (OSError, RuntimeError) as e:
            return_value = e

        await asyncio.sleep(0.1)
        for _ in range(timeout):
            if wlan.isconnected():
                break
            await asyncio.sleep(1)

    if return_value == "":
        return_value = wlan.isconnected()
    print('Network Connect:', essid, return_value)
    return return_value


async def wlan_disconnect(timeout=15):
    
    print('Network Disconnect')
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    return_value = True
    if wlan.active():
        if wlan.isconnected():
            wlan.disconnect()
            await asyncio.sleep(0.1)
            for _ in range(timeout):
                if not wlan.isconnected():
                    break
                await asyncio.sleep(1)
            return_value = not wlan.isconnected()
    wlan.active(False)
    print('Network Disconnect:', return_value)
    return return_value


async def connect_wifi():
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        await wlan_scan()
        prio = glovars.wifi_prio.split(',')
        for i in prio:
            wifi_name = getattr(glovars, f"wifi_name{i}")
            password = getattr(glovars, f"password{i}")
            print(f"wifiname:{wifi_name} pass: {password}")
            await wlan_connect(wifi_name, password)
            
            if wlan.isconnected():
                glovars.wifi_status = "connected"
                print("connected to wifi")
                if glovars.status != "startup":
                    log.log_sys("successful connection to wifi")
                else:
                    log.log_sys("successful connection to wifi startup")
                break
            else:
                glovars.wifi_status = "disconnected"
                log.log_err("Err3", "connect_wifi")
    else:
        glovars.wifi_status = "connected"
