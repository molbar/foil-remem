import machine
from machine import WDT
import time
import ntptime
import glovars
import devices
import log
import net_async
import uasyncio as asyncio
import gc
import micropython

wdt = None


def wdt_feed():
    wdt.feed()
    if not glovars.wdt_last_feed == 0:
        print(f"wdt return time: {time.time()-glovars.wdt_last_feed}")
        glovars.wdt_last_feed = time.time()

def print_mem():
    gc.collect()
    print("\nFree memory:", gc.mem_free())
    h=gc.mem_alloc()
    print(f"\n gc.mem_alloc: {h}\n")
    print("\n\n\n micropython meminfo:\n")
    print(micropython.mem_info())
    

async def core():
    while True:
        await asyncio.sleep(0.5)
        print("core loop runs")
        #print_mem()
        if time.time() - glovars.last_measure >= glovars.measure_inter:
            try:
                print("take measurement calling")
                devices.take_measurement_isr()
                glovars.last_measure = time.time()

            except KeyboardInterrupt:
                print('Got ctrl-c')
                machine.reset()
        
        if glovars.wdt_initialized:
            wdt_feed()
         


async def prio2():
    counter=0
    while True:
        #set if timeset interval arrived or time not been set, set tile from network ->> and update RTC
        print("prio2 run")
        await asyncio.sleep(1)
        if not glovars.timeset or (time.time() - glovars.last_timeset) > glovars.timeset_interval:
            try:
                ntptime.settime()

            except KeyboardInterrupt:
                print('Got ctrl-c')
                machine.reset()
        
        #if some function experienced network not connected and set the variable disconnected try a reconnect
        if (time.time() - glovars.last_netchk >= glovars.network_check_inter) and (glovars.wifi_status == "disconnected" or not net_async.wlan.isconnected()):
            try:
                print(f"!!! wifi checked, status: {glovars.wifi_status}")
                await net_async.wlan_disconnect()
                if glovars.wdt_initialized:
                    wdt_feed()
               
                await net_async.connect_wifi()
                if glovars.wdt_initialized:
                    wdt_feed()
               
                glovars.last_netchk = time.time()
            
            except KeyboardInterrupt:
                print('Got ctrl-c')
                machine.reset()
        
         #if data upload time arrived, upload core data
        if time.time() - glovars.last_updated_core >= glovars.core_upload_inter:
            
            try:                
                print("uploading core data")
                devices.upload_build()
                
            except KeyboardInterrupt:
                print('Got ctrl-c')
                machine.reset()
            else:
                glovars.last_updated_core=time.time()
        
        try:
            await devices.displays()
        
        except KeyboardInterrupt:
            print('Got ctrl-c')
            machine.reset()
        
        if glovars.wdt_initialized:
            wdt_feed()
        
        print(f"\n counter: {counter}\n")
        if counter%10==0:
            print_mem()
        counter+=1
            


async def init():
    
    print_mem()
    #initiate watchdogs
    if glovars.use_watchdog:
        global wdt
        wdt = WDT(timeout=glovars.watchdog_timeout)
        glovars.wdt_initialized = True
    
    #connect wifi
    await net_async.connect_wifi()
    
    #set time and set global variable value today if successful
    if net_async.wlan.isconnected():
        r = ntptime.settime()
        if r == "success":
            print(f"called settime with success startup time: {ntptime.time_format('sec')}")
            glovars.timeset = True 
            glovars.today = ntptime.time_format("day")
        
    #log startup
    log.log_sys("startup")
    #set status
    glovars.status = "running"
    #start 2 paralel coroutines
    print("init finished")
    print_mem()
    results=await asyncio.gather(core(), prio2(), return_exceptions=True)
    
#     for result in results:
#         if isinstance(result, Exception):
#             print(f"Caught exception in prio2: {result}")
#         else:
#             print(f"Coroutine result: {result}")
    


asyncio.run(init())


