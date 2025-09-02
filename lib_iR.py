"""
 2023/08/20
   iR センサーの状態でLED2 を点灯、消灯させる。
"""
import machine
import time

SW   = machine.Pin(1, machine.Pin.IN)
led2 = machine.Pin(13, machine.Pin.OUT)

def human_read():
    return SW.value()

def main():

    while True:
        sense = human_read()
        if sense == 0:
            led2.off()
        if sense == 1:
            led2.on()        

        print(sense)
        time.sleep(0.1)

if __name__=='__main__':
    main()
