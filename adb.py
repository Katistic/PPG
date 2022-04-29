import os
import re
import time
import logging

logging.basicConfig(level=logging.INFO)

class ADBDevice:
    def __init__(self):
        self._logger = logging.getLogger("ADBDevice")

        self.d_screen_size = [int(size) for size in re.findall(
            "(?<=Physical size: )(\d*)x(\d*)", self.do_adb_command("wm size"))[0]]
        self.d_screen_density = float(re.findall("(?<=Physical density: )\d*", self.do_adb_command("wm density"))[0])

        self._screen_size = (self.d_screen_size[0] / self.d_screen_density,
                             self.d_screen_size[1] / self.d_screen_density)

    def do_adb_command(self, command, shell=True):
        command = "adb {}{}".format("shell " if shell else "", command)
        result = os.popen(command)
        result = result.read()

        self._logger.debug("Executed ADB command '{}' -> '{}'".format(command, result.replace("\n", "\\n")))
        return result

    def pull_screen(self):
        if os.path.exists("./screengrab.png"):
            os.remove("./screengrab.png")

        timer = time.time()
        self.do_adb_command("exec-out screencap -p > screengrab.png", False)

        self._logger.info("Pulled screen (took {}s)".format((time.time() - timer).__round__()))
        return timer

    def set_size(self, resolution=None):
        if resolution is None:
            resolution = self.d_screen_size

        self.do_adb_command("wm size {}x{}".format(resolution[0], resolution[1]))
        dpi = self._get_density(resolution)
        self._set_density(dpi[0])

        if dpi[0] != dpi[1]:
            self._logger.warning("Bad resolution {}x{} (xDPI: {}, yDPI: {})".format(
                resolution[0], resolution[1], dpi[0], dpi[1]))

    def _set_density(self, density):
        self.do_adb_command("wm density {}".format(density))

    def set_immersive(self, package='com.nianticlabs.pokemongo'):
        self.do_adb_command("settings put global policy_control immersive.full={}".format(package))

    def do_tap(self, coordinates):
        self.do_adb_command("input tap {} {}".format(coordinates[0], coordinates[1]))

    def do_swipe(self, start_coordinates, end_coordinates, tween_time=200):
        self.do_adb_command("input swipe {} {} {} {} {}".format(
            start_coordinates[0], start_coordinates[1], end_coordinates[0],
            end_coordinates[1], tween_time))

    def _get_density(self, resolution):
        dpi_0 = (resolution[0] / self._screen_size[0]).__round__()
        dpi_1 = (resolution[1] / self._screen_size[1]).__round__()

        return (dpi_0, dpi_1)