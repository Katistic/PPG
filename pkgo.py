import adb
import time

class PokemonGoHandler(adb.ADBDevice):
    def __init__(self):
        super().__init__()

    def main_close(self):
        self.do_tap([50, 88])
        time.sleep(.5)