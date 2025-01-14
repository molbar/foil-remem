import glovars
from machine import Pin
import dht
import tm1637_async
import calc
import log
import comm
import time
import ntptime
import uasyncio as asyncio

#display quad 7-segment LED display
tm = tm1637_async.TM1637(dio=Pin(glovars.tm1637_dio), clk=Pin(glovars.tm1637_clk))
tm.write([0, 0, 0, 0])
#sensors:
in_sensor = dht.DHT22(Pin(glovars.in_sensor_pin))
out_sensor = dht.DHT22(Pin(glovars.out_sensor_pin))
#relays:
rel1 = Pin(glovars.rel1_pin, Pin.OUT)  #heat switch, Trigger: Low
rel1.value(1)
rel2 = Pin(glovars.rel2_pin, Pin.OUT)  #vent switch, Trigger: Low
rel2.value(1)


def turn_heat(dr="off"):

    if dr == "on" and rel1.value() == 1:
        rel1.value(0)
        print('heat on')
        glovars.heat_status = 1
        glovars.status = "heating"
        glovars.laston = time.time()
        log.log_sys("heat turend on")

    elif rel1.value() == 0:
        rel1.value(1)
        print('heat off')
        glovars.heat_time = glovars.heat_time + (time.time() - glovars.laston)

        addcost = calc.cost(
            "heat",
            time.time() - glovars.laston
        )  #calculate the cost of the actual just finished heat session

        log.log_dict_file("cost.txt", "Daily cost of heating", addcost)

        glovars.heat_status = 0
        glovars.status = "running"
        log.log_sys("heat turend off")


def turn_vent(dv="off"):

    if dv == "on" and rel2.value() == 1:
        rel2.value(0)
        print('vent on')
        glovars.vent_status = 1
        glovars.status = "venting"
        log.log_sys("vent turned on")
        glovars.laston_vent = time.time()

    elif rel2.value() == 0:
        rel2.value(1)
        print('vent off')
        glovars.vent_time = glovars.vent_time + (time.time() -
                                                 glovars.laston_vent)

        addcost = calc.cost(
            "vent",
            time.time() - glovars.laston_vent
        )  #calculate the cost of the actual just finished vent session
        log.log_dict_file("cost.txt", "Daily cost of venting", addcost)

        glovars.vent_status = 0
        glovars.status = "running"
        log.log_sys("vent turned off")


def take_measurement_isr():

    #read out sensors
    try:
        in_sensor.measure()
    except Exception as e:
        print("cannot measure in_sensor ")
        log.log_err("Err1", "take_measurement_isr", e)

    print("Temp: ", in_sensor.temperature(), "°C, Humidity: ",
          in_sensor.humidity(), "%")

    try:
        out_sensor.measure()
    except Exception as e:
        print("cannot measure outer sensor")
        log.log_err("Err2", "take_measurement_isr", e)
    print("Outer Temp: ", out_sensor.temperature(), "°C, Outer Humidity: ",
          out_sensor.humidity(), "%")

    #assign readings to global variables
    glovars.temp = in_sensor.temperature()
    glovars.hum = in_sensor.humidity()
    glovars.otemp = out_sensor.temperature()
    glovars.ohum = out_sensor.humidity()

    #assign calculated data to global variables
    glovars.avg_data = calc.avg()

    #heat on/off based on latest sensor readings:
    if in_sensor.temperature() <= glovars.heat_on_temp + calc.mod_curve("linear"):
        if not rel1.value() == 0:
            turn_heat("on")

    elif in_sensor.temperature() >= glovars.heat_off_temp + calc.mod_curve("linear"):
        turn_heat("off")

    #vent on/off logic:
    #Case1:  <too humid inside> Humidity higher than set AND outer temp higher than internal minimum temp set AND heating is off
    #Case2: <too warm inside> Internal temp higher than temperature ventillation set AND outer temp higher than internal minimum temp set AND heating is off
    if (in_sensor.humidity() >= glovars.vent_on_humidity
            and out_sensor.temperature() > glovars.heat_on_temp
            and glovars.status != "heating") or (
                in_sensor.temperature() >= glovars.vent_on_temp
                and out_sensor.temperature() > glovars.heat_on_temp
                and glovars.status != "heating"):
        if not rel2.value() == 0:
            turn_vent("on")
            print(
                f"humidity internal:{in_sensor.humidity()} temp:{in_sensor.temperature()} out: {out_sensor.temperature()} call turning vent on"
            )

    elif in_sensor.humidity(
    ) <= glovars.vent_off_humidity or in_sensor.temperature(
    ) <= glovars.vent_off_temp or glovars.status == "heating":
        turn_vent("off")
        print(
            f"humidity:{in_sensor.humidity()} temp:{in_sensor.temperature()} call turning vent off"
        )


# show info on quad 7-segment LED display
async def displays():
    print("displays called")
    if glovars.last_displayed == 1:
        tm.scroll("inner temp")  #inner temp
        for i in range(3):
            await asyncio.sleep(0.3)
            tm.temperature(int(glovars.temp))
            await asyncio.sleep(0.3)
            i += 1

    elif glovars.last_displayed == 2:
        tm.scroll("outer temp")  #outer temp
        for i in range(3):
            await asyncio.sleep(0.3)
            tm.temperature(int(glovars.otemp))
            await asyncio.sleep(0.3)
            i += 1
    elif glovars.last_displayed == 3:
        tm.scroll("inter humid")  #internal humid
        for i in range(3):

            await asyncio.sleep(0.3)
            humdisp = f"{int(glovars.hum)} p"  #internal humidity
            tm.show(str(humdisp))
            await asyncio.sleep(0.3)
            i += 1

    elif glovars.last_displayed == 4:
        tm.scroll(glovars.status)
    elif glovars.last_displayed == 5:
        tm.scroll(f"wifi status {glovars.wifi_status}")  #wifi status

    if glovars.last_displayed == 5:
        glovars.last_displayed = 1
    else:
        glovars.last_displayed += 1

    await asyncio.sleep(3)


def upload_build():
    #build upload readings and data and logs and notes and to TS and NC servers
    #update global fix dictionaries with actual uploadables /data
    #for TS server
    if glovars.TS_API:
        glovars.upload_readings_ts["field1"] = glovars.temp
        glovars.upload_readings_ts["field2"] = glovars.hum
        glovars.upload_readings_ts["field3"] = glovars.deltatemp
        glovars.upload_readings_ts["field4"] = glovars.avgtemp
        glovars.upload_readings_ts["field5"] = glovars.deltahum
        glovars.upload_readings_ts["field6"] = glovars.avghum
        glovars.upload_readings_ts["field7"] = glovars.heat_time / 60
        glovars.upload_readings_ts["field8"] = glovars.heat_status
        glovars.upload_readings_ts["status"] = glovars.status
        comm.upload_data("dt", "ts")

    #for NC server
    if glovars.NC_API:
        glovars.upload_readings_nc["data"][0]["value"] = glovars.temp
        glovars.upload_readings_nc["data"][1]["value"] = glovars.hum
        glovars.upload_readings_nc["data"][2]["value"] = glovars.otemp
        glovars.upload_readings_nc["data"][3]["value"] = glovars.ohum
        glovars.upload_readings_nc["data"][4]["value"] = glovars.deltatemp
        glovars.upload_readings_nc["data"][5]["value"] = glovars.avgtemp
        glovars.upload_readings_nc["data"][6]["value"] = glovars.deltahum
        glovars.upload_readings_nc["data"][7]["value"] = glovars.avghum
        glovars.upload_readings_nc["data"][8]["value"] = glovars.heat_time / 60
        glovars.upload_readings_nc["data"][9][
            "dimension1"] = glovars.heat_status
        glovars.upload_readings_nc["data"][10][
            "dimension1"] = glovars.vent_status
        glovars.upload_readings_nc["data"][11]["dimension1"] = glovars.status
        glovars.upload_readings_nc["data"][12]["value"] = calc.free()
        comm.upload_data("dt", "nc")

    #decide if notification needed to be built and prompt send to upload if needed
    Note=None 
    if glovars.temp > glovars.man_ventillation_limit_temp and glovars.door_open != True and glovars.deltatemp > 1:
        dim1=f"Foil door could be OPENED as TEMP exceeding {glovars.man_ventillation_limit_temp}C and rising!"[:64]
        dim2="Internal TEMPERATURE sensor"
        value=glovars.temp
        door=True
        Note=True

    if glovars.temp < glovars.man_close_reminder_limit and glovars.door_open == True and glovars.deltatemp < 1:
        dim1=f"Foil door should be CLOSED as TEMP is below {glovars.man_close_reminder_limit}C and falling!"[:64]
        dim2="Internal TEMPERATURE sensor"
        value=glovars.temp
        door=False
        Note=True
        

    if glovars.hum > glovars.man_ventillation_limit_hum and glovars.door_open != True and glovars.hum > glovars.ohum and glovars.otemp > glovars.treshold_humid_note_otemp:
        dim1=f"Foil door could be OPENED as HUMIDITY is exceeding {glovars.man_ventillation_limit_hum}%"[:64]
        dim2="Internal HUMIDITY sensor"
        value=glovars.hum
        door=True
        Note=True
    
    if Note:
        log.build_one_log(dim1, dim2,value)
        if comm.upload_data("note") == "success":
            glovars.door_open = door

#upload costs to NC server

    if ntptime.time_format(
            "day"
    ) != glovars.today and glovars.today != 0:  #napforduló éjfél után

        iter = 2
        for i in range(iter):
            if i % 2 == 0:
                t = "heat"
            else:
                t = "vent"
            cost = log.get_from_dict_file(
                "cost.txt", f"daily_{t}_cost",
                ntptime.time_format("short"))  #get cost log
            log.build_one_log("Daily Cost of HEATING",
                              ntptime.time_format("daybefore"), cost)
            if cost is not None:
                try:
                    comm.upload_data("cost")
                except Exception as e:
                    log.log_err("Err4", "upload_buid_cost", e)
