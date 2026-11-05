# DC power supply driver over USB (PyVISA).
#
# Find the instrument address, then pass a usb_pyvisa object to the class:
#
#   devices = usb_pyvisa.query()
#   print(devices)  # check the addresses and IDNs
#   addr = usb_pyvisa.getAddrFromIdn("N5769A")
#   psu = keysight_n5769a_usb(usb_pyvisa(addr))

class keysight_n5769a_usb():
    def __init__(self, usb_pyvisa):
        self.usb = usb_pyvisa
        self.num_channels = 1

    def setVoltage(self, value):
        self.usb.write(f":VOLT {value}")

    def readVoltage(self):
        return float(self.usb.read(":MEAS:VOLT?"))

    def setCurrent(self, value):
        self.usb.write(f":CURR {value}")

    def readCurrent(self):
        return float(self.usb.read(":MEAS:CURR?"))

    def activate(self):
        self.usb.write(":OUTP ON")

    def deactivate(self):
        self.usb.write(":OUTP OFF")

    def activateAll(self):
        self.activate()

    def deactivateAll(self):
        self.deactivate()
