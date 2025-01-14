import glovars
import net
import ntptime
import log
import requests
import micropython


def make_request(mod, url=None, payload=None, server=None):
    user = glovars.API_USR_NC
    passw = glovars.API_AUTH_NC
    HTTP_HEADERS = {'Content-Type': 'application/json'}

    #if wifi obviously not connected dont even try uploading
#     print(f"wifi status: {net.wlan.isconnected()}")

    if not net.wlan.isconnected():
        glovars.wifi_status = "disconnected"
        return "disconnected"
    else:
        response = None
#         print("trying to upload data....\n\n memory data:\n")
        print("before request")
        print(micropython.mem_info())

        r = None
        try:
            #thingspeak server post
#             print(f"request:{payload}")
            if glovars.TS_API and server == "ts":
                response = requests.post(f"{url}={glovars.API_AUTH_TS}",
                                         json=payload,
                                         headers=HTTP_HEADERS)
            #nextcould analytics post
            elif glovars.NC_API:
                response = requests.post(url,
                                         json=payload,
                                         headers=HTTP_HEADERS,
                                         auth=(user, passw))
#             print(f"response: {response.status_code}")
            response.close()
        except Exception as e:
            print("Request failed:", e)
            if response is not None:
                print(f"Reason code: {response.reason}")
            log.log_err("Err4", "upload_data_TS", e)
            glovars.wifi_status = "disconnected"

        else:
            #update gobal variables content if necessary
            if mod == "cost":
                glovars.today = ntptime.time_format("day")
                r = "success"
        finally:
            if response:
                print("before response close")
                print(micropython.mem_info())
                response.close()
                print("after response close")
            
            return r


def upload_data(mod, server=None):
    url = None
    payload = None

    #build data upload structures
    if mod == "dt":
        if server == "nc":
            url = glovars.API_URL_NC
            payload = glovars.upload_readings_nc
        elif server == "ts":
            url = glovars.API_URL_TS
            payload = glovars.upload_readings_ts

    #build error log upload structures
    elif mod == "err":
        url = glovars.API_URL_NC_ERR
        payload = glovars.upload_one

    #build system log upload structures
    elif mod == "sys":
        url = glovars.API_URL_NC_SYS
        payload = glovars.upload_one

    #build cost log upload structures
    elif mod == "cost":
        url = glovars.API_URL_NC_COST
        #print(f"dataset {dataset}")
        payload = glovars.upload_one

    #build notes upload structures
    elif mod == "note":
        url = glovars.API_URL_NC_NOTE
        #print(f"dataset {dataset}")
        payload = glovars.upload_one
    else:
        return "error"

    #call api upload
    if url and payload:
        return make_request(mod, url, payload, server)
