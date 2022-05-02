import time
import logging
import numpy as np

from PIL import Image


class Imager:
    def __init__(self, device):
        self.im = None
        self.cropped_im = None

        self.device = device
        self._logger = logging.getLogger("Imager")

        self.pokestops = []
        self.pokemon = []
        self.gyms = []

    def load_new_image(self, image):
        if self.im is not None:
            self.im.close()

        self.im = Image.open(image)
        self.cropped_im = None

    @property
    def interactable_crop(self):
        if self.cropped_im is None:
            point1 = self.device._point_from_percent([16, 50])
            point2 = self.device._point_from_percent([84, 86])
            self.cropped_im = np.array(self.im.crop([point1[0], point1[1], point2[0], point2[1]]))

        return self.cropped_im

    @staticmethod
    def _coordinates_are_close(coord1, coord2):
        if abs(coord1[0] - coord2[0]) < 80 and abs(coord1[1] - coord2[1]) < 80:
            return True

        return False

    @staticmethod
    def _apply_pokestop_mask(pixel):
        # Mask out anything will lower blue levels
        if pixel[2] < 230:
            return False
        # Mask out white/grays
        elif abs(pixel[0] - pixel[1]) < 50 and abs(pixel[0] - pixel[2]) < 50:
            return False
        # Mask out purple (collected pokestops)
        elif pixel[0] > 150:
            return False

        return True

    def pokestop_mask(self, visualise=False):
        t = time.time()
        img_array = self.interactable_crop

        if visualise:
            Image.fromarray(img_array).save("temp.png")

        for pixel_row in range(0, len(img_array)):
            for pixel_i in range(0, len(img_array[pixel_row])):
                filtered = self._apply_pokestop_mask(img_array[pixel_row][pixel_i].tolist())

                if filtered:
                    close = False
                    for coordinates in range(0, len(self.pokestops)):
                        if self._coordinates_are_close([pixel_i, pixel_row], self.pokestops[coordinates][0]):
                            self.pokestops[coordinates][1] += 1
                            self.pokestops[coordinates][2].append(pixel_i)
                            self.pokestops[coordinates][3].append(pixel_row)

                            close = True
                            break

                    if not close:
                        self.pokestops.append([(pixel_i, pixel_row), 1, [pixel_i], [pixel_row]])
                        self._logger.debug(
                            "Found potential pokestop at [{}, {}]".format(
                                pixel_i, pixel_row))
                elif visualise:
                    img_array[pixel_row][pixel_i][3] = 0

        to_remove = []
        for pokestop in range(0, len(self.pokestops)):
            ps = self.pokestops[pokestop]
            if ps[1] < 500:
                to_remove.insert(0, pokestop)
            else:
                # Add 16% resolution back to x coord from crop
                x = (ps[2][round(len(ps[2]) / 2)] + (self.device.r_screen_size[0] / 6.25)
                     ) / self.device.r_screen_size[0] * 100
                # Add 50% resolution back to y coord from crop
                y = (ps[3][round(len(ps[3]) / 2)] + (self.device.r_screen_size[1] / 2)
                     ) / self.device.r_screen_size[1] * 100

                self.pokestops[pokestop] = [(x, y), ps[1]]

        for ps in to_remove:
            if visualise:
                for pos in range(0, len(self.pokestops[ps][2])):
                    img_array[self.pokestops[ps][3][pos]][
                        self.pokestops[ps][2][pos]][3] = 0

            self._logger.debug("Removed pokestop at x{} y{}, density too low".format(
                self.pokestops[ps][0][0], self.pokestops[ps][0][1]))
            del self.pokestops[ps]

        if visualise:
            Image.fromarray(img_array).save("visualise_pokestop_mask.png")

        self.pokestops.sort(reverse=True, key=lambda stop: stop[1])
        self._logger.debug("Took {}s applying pokestop mask".format(time.time() - t))

# player is ~ 550 1510c / 50% 63%
