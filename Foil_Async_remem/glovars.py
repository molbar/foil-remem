#recognizing string inputs and return as float/int/bolean/string
def conv(value):

    value = value.strip()

    if value:
            
        if value.isdigit() or (value[0] == "-" and value[1:].isdigit()):
            return int(value)

        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        try:
            return float(value)
        
        except ValueError:
            pass
        # If none of the above, return as string
        return value


def get_params():
    try:
        with open("/param.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        # !!! we dont check if variable already exist to save memory not calling globals() and locals() only if it will cause problems manual check: no same name in params.txt!!!
                        global name
                        name, value = line.split(":", 1)
                        name = name.strip()
                        globals()[name] = conv(value)
                    
    except OSError as e:
        print("Error opening file:", e)


vent_log = [None] * 90
cost_log = [None] * 90
tempavg = [0] * 120
humavg = [0] * 120
deltatemp = 0
avgtemp = 0
avghum = 0
deltahum = 0
temp = 0
otemp = 0  #outer temp
ohum = 0  #outer humidity
hum = 0
laston = 0
laston_vent = 0
heat_time = 0
vent_time = 0
heat_status = 0
vent_status = 0
last_measure = 0
status = "startup"
wifi_status = "disconnected"
last_displayed = 0
last_updated_err = 0
last_updated_core = 0
timeset = False
last_timeset = 0
dcost_heat = 0
dcost_vent = 0
today = 0
notification = {
    "data": [{
        "dimension1": None,
        "dimension2": None,
        "value": None
    }]
}
door_open = False
# avg_data = ()
wdt_initialized = False
last_netchk = 0
wdt_last_feed = 0

upload_readings_ts = {
    'field1': None,
    'field2': None,
    'field3': None,
    'field4': None,
    'field5': None,
    'field6': None,
    'field7': None,
    'field8': None,
    'status': None
}
upload_readings_nc = {
    "data": [{
        "dimension1": 'API_NC_temp',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_hum',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_otemp',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_ohum',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_deltatemp',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_avgtemp',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_deltahum',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_avghum',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_heat_time',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_vent_time',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_heat_status',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_vent_status',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_status',
        "dimension2": "%now%",
        "value": None
    }, {
        "dimension1": 'API_NC_memory',
        "dimension2": "%now%",
        "value": None
    }]
}
upload_one = {
    "data": [{
        "dimension1": None,
        "dimension2": "%now%",
        "value": None
    }]
}
get_params()

# import sys

# Print the current module's namespace
# print(dir(sys.modules[__name__]))