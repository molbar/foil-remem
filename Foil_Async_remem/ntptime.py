import utime

try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

import machine
import glovars
import log
import net
import time


# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'

# The NTP socket timeout can be configured at runtime by doing: ntptime.timeout = 2



def gettime(host,timeout):
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    EPOCH_YEAR = utime.gmtime(0)[0]
    if EPOCH_YEAR == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 2208988800
    else:
        raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

    return val - NTP_DELTA

#setting the controller's RTC timezone diff from parameters
def settime():
    
    return_value="settime_fail"
    if not net.wlan.isconnected():
        return "disconnected"
    try:
        t=gettime(glovars.ntphost,1)
        
    except Exception as e:
        log.log_err("Err5","settime",e)
        glovars.timeset=False
    else:
        if t>0:
            return_value="success"
            print("settime succeded")
            print(f"time t {t}")
            tm = utime.gmtime(t)
            print(f"time tm {tm}")
#             machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3]+glovars.TMZONE_DIFF, tm[4], tm[5], 0))

            machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
            print(f"time from time_format: {time_format("sec")}")
            
            glovars.timeset=True
            glovars.last_timeset=time.time()
            log.log_sys("Machine RTC updated from NTP")
            log.log_sys("Time set successful from network")
        else:
            return_value="settime_fail"
            print("settime failed")
            log.log_sys("time set FAIL from network")
    
    finally:
        return return_value

 
def time_format(mod):
    #print(f"start timeformat mod:{mod}")
    time_f=None
    
    t=machine.RTC().datetime()
#     print(f"formatting RTC time before format {t}")
    MM=t[5] if len(str(t[5]))==2 else f"0{str(t[5])}" #min
    mm=t[1] if len(str(t[1]))==2 else f"0{str(t[1])}" #month
    dd=t[2] if len(str(t[2]))==2 else f"0{str(t[2])}" #day
    ss=t[6] if len(str(t[6]))==2 else f"0{str(t[6])}" #second
    hh=t[4]+glovars.TMZONE_DIFF if len(str(t[4]))==2 else f"0{str(t[4]+glovars.TMZONE_DIFF)}" #hour
    if mod=="sec":
        time_f=f"{t[0]}-{mm}-{dd} {hh}:{MM}:{ss}"
        #print(f"datda formatpost format: {time_f}")
    elif mod=="ssec":
        time_f=f"{t[0]}-{mm}-{dd} {hh}:{MM}:{t[6]}:{t[7]}"
    elif mod=="min":
        time_f=f"{t[0]}-{mm}-{dd} {hh}:{MM}"
    elif mod=="day":
        time_f=t[2]
    elif mod=="short":
        time_f=f"{t[0]}-{mm}-{dd}"
    
    elif mod=="daybefore" or "day_before_short":
        t = utime.gmtime(time.time()-86400)
        mm=t[1] if len(str(t[1]))==2 else f"0{str(t[1])}" #month
        dd=t[2] if len(str(t[2]))==2 else f"0{str(t[2])}" #day
        
        if mod=="day_before_short":
            time_f=f"{t[0]}-{mm}-{dd}"
        elif mod=="daybefore":
            time_f=t[2]
        
#     print(f"formatted RTC time after format {time_f}")
    return time_f

