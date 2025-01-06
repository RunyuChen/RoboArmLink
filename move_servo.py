import time
from Arm_Lib import Arm_Device
 
Arm = Arm_Device()

def servo_init():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    
def nod():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 160, 20, 40, 90, 180, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 90, 90, 90, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 40, 90, 180, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 90, 90, 90, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 500)
    time.sleep(0.5)

    
def clip():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 60, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 60, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 300)
    time.sleep(0.3)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 500)
    time.sleep(0.5)
    
def wiggle():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 60, 140, 60, 90, 60, 800)
    time.sleep(0.8)
    Arm.Arm_serial_servo_write6(90, 120, 40, 120, 90, 120, 800)
    time.sleep(0.8)
    Arm.Arm_serial_servo_write6(90, 60, 140, 60, 90, 60, 800)
    time.sleep(0.8)
    Arm.Arm_serial_servo_write6(90, 120, 40,120, 90, 120, 800)
    time.sleep(0.8)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 500)
    time.sleep(0.5)
    
def turned():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(0, 120, 60, 0, 180, 180, 500)
    time.sleep(0.5)
    Arm.Arm_serial_servo_write6(180, 120, 60, 0, 0, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(0, 120, 60, 0, 180, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 500)
    time.sleep(0.5)
    
def rapper():
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 95, 0, 0, 90, 0, 500)
    time.sleep(0.7)
    Arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 0, 300)
    time.sleep(0.9)
    Arm.Arm_serial_servo_write6(90, 95, 0, 0, 90, 0, 500)
    time.sleep(0.7)
    Arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 0, 300)
    time.sleep(0.9)
    Arm.Arm_serial_servo_write6(90, 95, 0, 0, 90, 0, 500)
    time.sleep(0.7)
    Arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 0, 300)
    time.sleep(0.9)
    Arm.Arm_serial_servo_write6(90, 95, 0, 0, 90, 0, 500)
    time.sleep(0.7)
    Arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 0, 300)
    time.sleep(0.9)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 500)
    time.sleep(0.5)
    
def bow():    
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 60, 60, 60, 90, 180, 1000)
    time.sleep(1)
    Arm.Arm_serial_servo_write6(90, 160, 20, 0, 90, 180, 1000)
    time.sleep(1)
    
    