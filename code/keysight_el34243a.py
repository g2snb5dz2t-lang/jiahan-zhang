# Electronic load driver over USB (PyVISA).
#
# Find the instrument address, then pass a usb_pyvisa object to the class:
#
#   devices = usb_pyvisa.query()
#   print(devices)  # check the addresses and IDNs
#   addr = usb_pyvisa.getAddrFromIdn("EL34243A")
#   eload = keysight_el34243a_usb(usb_pyvisa(addr))

class keysight_el34243a_usb():
    def __init__(self, usb_pyvisa):
        self.usb = usb_pyvisa
        self.num_channels = 2
        self.mode = [None for _ in range(self.num_channels)]
        self.allowedModes = ["CURR", "VOLT", "RES", "POW"]

    def setPosSlew(self, value, chan=1):
        self.usb.write(f"{self.mode[chan-1]}:SLEW:POS {value}, (@{chan})")

    def setNegSlew(self, value, chan=1):
        self.usb.write(f"{self.mode[chan-1]}:SLEW:NEG {value}, (@{chan})")

    def setSlew(self, value, chan=1):
        # Slew in A/s
        self.setPosSlew(value, chan)
        self.setNegSlew(value, chan)

    def setMode(self, mode=None, remote_sense=False, chan=1):
        # Mode can be CURR, VOLT, RES, POW
        if mode in self.allowedModes:
            self.mode[chan-1] = mode
            self.usb.write(f"FUNC {mode}, (@{chan})")
            if remote_sense:
                self.usb.write(f"VOLT:SENS:SOUR EXT, (@{chan})")
            else:
                self.usb.write(f"VOLT:SENS:SOUR INT, (@{chan})")
        else:
            raise ValueError(f"Unsupported mode {mode}")

    def setValue(self, value, chan=1):
        self.usb.write(f"{self.mode[chan-1]} {value}, (@{chan})")

    def readVoltage(self, chan=1):
        return float(self.usb.read(f"MEAS:VOLT? (@{chan})"))

    def readCurrent(self, chan=1):
        return float(self.usb.read(f"MEAS:CURR? (@{chan})"))

    def readPower(self, chan=1):
        return float(self.usb.read(f"MEAS:POW? (@{chan})"))

    def activate(self, chan=1):
        self.usb.write(f"INP ON, (@{chan})")

    def deactivate(self, chan=1):
        self.usb.write(f"INP OFF, (@{chan})")

    def activateAll(self):
        # TODO: Can use list of channels for one command
        for ch in range(1, self.num_channels+1):
            self.activate(ch)

    def deactivateAll(self):
        # TODO: Can use list of channels for one command
        for ch in range(1, self.num_channels+1):
            self.deactivate(ch)
