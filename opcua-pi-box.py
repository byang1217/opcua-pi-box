from time import sleep
import math
import sys
import json

from gpiozero import LED
from gpiozero import Button
from gpiozero import DistanceSensor
from opcua import ua, uamethod, Server

global ledR, ledG, ledB, switch1, switch2, rotaryVal, rangeVal, flameVal, sinGen

led_r = LED(18)
led_g = LED(19)
led_b = LED(20)

switch_1 = Button(21)
def switch_1_pressed():
    global switch1
    switch1.set_value(True)
    print("switch_1 On")
def switch_1_released():
    global switch1
    switch1.set_value(False)
    print("switch_1 Off")
switch_1.when_pressed = switch_1_pressed
switch_1.when_released = switch_1_released

switch_2 = Button(22)
def switch_2_pressed():
    global switch2
    switch2.set_value(True)
    print("switch_2 On")
def switch_2_released():
    global switch2
    switch2.set_value(False)
    print("switch_2 Off")
switch_2.when_pressed = switch_2_pressed
switch_2.when_released = switch_2_released

rangeSensor = DistanceSensor(echo=5, trigger=4, queue_len=2)

def get_range_val():
    return rangeSensor.distance * 100

flameSensor = Button(6)
def flameSensorOn():
    global flameVal
    flameVal.set_value(True)
    print("flameSensor On")
def flameSensorOff():
    global flameVal
    flameVal.set_value(False)
    print("flameSensor Off")
flameSensor.when_pressed = flameSensorOn
flameSensor.when_released = flameSensorOff

rotaryCLK = Button(17)
rotaryDT = Button(16)
rotaryBTN = Button(13)
rotaryCurrent = 0

def rotaryCheck():
    global rotaryCurrent
    global rotaryVal
    if rotaryDT.is_pressed:
        rotaryCurrent-=1
    else:
        rotaryCurrent+=1
    if rotaryCurrent < 0:
        rotaryCurrent = 0
    rotaryVal.set_value(rotaryCurrent)
    print("rotary", rotaryCurrent)

def rotaryReset():
    global rotaryCurrent
    global rotaryVal
    rotaryCurrent = 0
    rotaryVal.set_value(rotaryCurrent)
    print("rotary", rotaryCurrent)

rotaryCLK.when_pressed = rotaryCheck
rotaryBTN.when_pressed = rotaryReset

class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        global ledR, ledG, ledB
        #print("Python: New data change event", node, val)
        if ledR == node:
            print("ledR => ", val)
            if val:
                led_r.on()
            else:
                led_r.off()
        if ledG == node:
            print("ledG => ", val)
            if val:
                led_g.on()
            else:
                led_g.off()
        if ledB == node:
            print("ledB => ", val)
            if val:
                led_b.on()
            else:
                led_b.off()

    def event_notification(self, event):
        print("Python: New event", event)


if __name__ == "__main__":
    global ledR, ledG, ledB, switch1, switch2, rotaryVal, rangeVal, flameVal, sinGen

    led_r.off()
    led_g.off()
    led_b.off()
    

    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/pi-box")
    server.set_server_name("OPC-UA Pi Box")
    # set all possible endpoint policies for clients to connect through
    server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign])

    idx = server.register_namespace("opcua-pi-box")

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()
    myobj = objects.add_object(idx, "OPCUA-PI-BOX")

    ledR = myobj.add_variable(idx, "Led_R", False, ua.VariantType.Boolean)
    ledR.set_writable()
    ledG = myobj.add_variable(idx, "Led_G", False, ua.VariantType.Boolean)
    ledG.set_writable()
    ledB = myobj.add_variable(idx, "Led_B", False, ua.VariantType.Boolean)
    ledB.set_writable()

    switch1 = myobj.add_variable(idx, "Switch_1", False, ua.VariantType.Boolean)
    switch2 = myobj.add_variable(idx, "Switch_2", False, ua.VariantType.Boolean)

    rotaryVal = myobj.add_variable(idx, "Rotary", 0, ua.VariantType.UInt32)

    rangeVal = myobj.add_variable(idx, "Range", 0, ua.VariantType.UInt32)

    flameVal = myobj.add_variable(idx, "Flame", False, ua.VariantType.Boolean)

    sinGen = myobj.add_variable(idx, "SineGenerator", 0.0)

    print("Led_R: ", ledR)
    print("Led_G: ", ledG)
    print("Led_B: ", ledB)
    print("Switch_1: ", switch1)
    print("Switch_2: ", switch2)
    print("Rotary: ", rotaryVal)
    print("Range: ", rangeVal)
    print("Flame: ", flameVal)
    print("SineGenerator: ", sinGen)
	
    # starting!
    server.start()

    sub = server.create_subscription(50, SubHandler())
    sub.subscribe_data_change(ledR)
    sub.subscribe_data_change(ledG)
    sub.subscribe_data_change(ledB)

    try:
        count = 0
        while True:
            sleep(0.1)
            count += 0.1
            sinGen.set_value(math.sin(count))
            rangeVal.set_value(get_range_val())
    finally:
        server.stop()
