import glovars
import gc
import os


def mod_curve(mode):
    if mode=="linear":
        c=abs(round(glovars.otemp*0.07,1))
        if glovars.otemp<-3:
            return c
        else:
            return 0
    
    #not enough data yet to prepare manual curve however real life probably not linear
    elif mode=="manual":
        pass


def cost(unit, last):  #calculate kwh

    if unit == "heat":
        watt = glovars.watt_heat
    elif unit == "vent":
        watt = glovars.watt_vent

    c = glovars.cost_elec  #cost electricity per kwh
    actual_cost = watt / 1000 * last / 3600 * c

    return actual_cost


#this function is suppoused to update preallocated list instead of using .pop() for memory fragmentation constrains
#significantly slower until list is filled up because it itirates backwards
def shift_and_add(my_list, new_element):
    for i in range(len(my_list) - 1, 0, -1):
        my_list[i] = my_list[i - 1]
    # Insert the new element at the start
    my_list[0] = new_element


def get_last_element(my_list):
    for item in reversed(my_list):
        if item is not None and item != 0:
            return item
    return None  # Return None instead of 0 if no valid element is found



def avg():
    x = glovars.tempavg.index(0)
    y = glovars.humavg.index(0)

    if x < 119:
#         print(type(x))
#         print(x)
        glovars.tempavg[x] = glovars.temp if glovars.temp != 0 else 0.00001
    else:
        shift_and_add(glovars.tempavg, glovars.temp)
    glovars.avgtemp = round(sum(glovars.tempavg) / len(glovars.tempavg), 2)
    glovars.deltatemp = round(
        glovars.tempavg[len(glovars.tempavg) - 1] - glovars.tempavg[0], 2)

    if y < 119:
        glovars.humavg[y] = glovars.hum if glovars.hum != 0 else 0.00001
    else:
        shift_and_add(glovars.humavg, glovars.hum)
    glovars.avghum = round(sum(glovars.humavg) / len(glovars.humavg), 2)
    glovars.deltahum = round(
        glovars.humavg[len(glovars.humavg) - 1] - glovars.humavg[0], 2)


def free(full=False):
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F + A
    #P = '{0:.2f}%'.format(F/T*100)
    P = (F / T * 100)
    if not full:
        return round(P, 2)
    else:
        return ('Total:{0} Free:{1} ({2})'.format(T, F, P))


def df():
    s = os.statvfs('//')
    return ('{0} MB'.format((s[0] * s[3]) / 1048576))
