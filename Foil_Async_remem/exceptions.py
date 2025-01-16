import gvars
import note

#check
#report
#act

def check_exceptions():
    #1 internal temp sensor may be incorrect as average hourly temp is not changing
    if gvars.avg_data[1] ==0:
        #send a note
        note.note("Internal TEMP Sensor","Average hourly TEMP may be constant - restarting system")
        machine_reset()
    if gvars.avg_data[3] ==0:
        #send a note
        note.note("Internal HUMIDITY Sensor","Average hourly HUM may be constant - restarting system")
        machine_reset()
    #the unable to beasure temp->> the sensors are not working
    
        
        
def machine_reset():
    import machine
    machine.reset()
        
        

