import time
import logging
import numpy as np

from PIL import Image
from enums import MaskType


class Imager:
    def __init__(self, device):
        self.im = None
        self.cropped_im = None

        self.device = device
        self._logger = logging.getLogger("Imager")

        self.pokestops = []
        self.pokemon = []
        self.gyms = []
        self.teamrocket = []

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
    def _apply_teamrocket_mask(pixel):
        # Mask out white/grays
        if abs(pixel[0] - pixel[1]) < 50 and abs(pixel[0] - pixel[2]) < 50 and pixel[0] < 70:
            return True

        return False

    @staticmethod
    def _apply_pokestop_mask(pixel):
        # Mask out anything with lower blue levels
        # and higher red levels (for purples)
        if pixel[2] < 230 or pixel[0] > 150:
            return False
        # Mask out white/grays
        elif abs(pixel[0] - pixel[1]) < 50 and abs(pixel[0] - pixel[2]) < 50:
            return False

        return True

    def teamrocket_mask(self, pixel, x, y):
        if self._apply_teamrocket_mask(pixel):
            close = False
            for coordinates in range(0, len(self.teamrocket)):
                if self._coordinates_are_close([x, y], self.teamrocket[coordinates][0]):
                    self.teamrocket[coordinates][1] += 1
                    self.teamrocket[coordinates][2].append(x)
                    self.teamrocket[coordinates][3].append(y)

                    close = True
                    break

            if not close:
                self.teamrocket.append([(x, y), 1, [x], [y]])
                self._logger.debug(
                    "Found potential teamrocket battle at [{}, {}]".format(x, y))
            return False
        return True

    def pokestop_mask(self, pixel, x, y):
        if self._apply_pokestop_mask(pixel):
            close = False
            for coordinates in range(0, len(self.pokestops)):
                if self._coordinates_are_close([x, y], self.pokestops[coordinates][0]):
                    self.pokestops[coordinates][1] += 1
                    self.pokestops[coordinates][2].append(x)
                    self.pokestops[coordinates][3].append(y)

                    close = True
                    break

            if not close:
                self.pokestops.append([(x, y), 1, [x], [y]])
                self._logger.debug(
                    "Found potential pokestop at [{}, {}]".format(x, y))
            return False
        return True

    def mask_final(self, image_array, place, mask_type, visualise=False):
        to_remove = []
        for pokeplace in range(0, len(place)):
            ps = place[pokeplace]
            if ps[1] < 500:
                to_remove.insert(0, pokeplace)
            else:
                # Add 16% resolution back to x coord from crop
                x = (ps[2][round(len(ps[2]) / 2)] + (self.device.r_screen_size[0] / 6.25)
                     ) / self.device.r_screen_size[0] * 100
                # Add 50% resolution back to y coord from crop
                y = (ps[3][round(len(ps[3]) / 2)] + (self.device.r_screen_size[1] / 2)
                     ) / self.device.r_screen_size[1] * 100

                place[pokeplace] = [(x, y), ps[1]]

        for ps in to_remove:
            if visualise:
                for pos in range(0, len(place[ps][2])):
                    image_array[place[ps][3][pos]][
                        place[ps][2][pos]][3] = 0

            self._logger.debug("Removed {} at x{} y{}, density too low".format(
                mask_type, place[ps][0][0], place[ps][0][1]))
            del place[ps]

        if visualise:
            Image.fromarray(image_array).save("visualise_{}_mask.png".format(mask_type))

        place.sort(reverse=True, key=lambda stop: stop[1])

    def apply_mask(self, mask_type, visualise=False):
        switch = {
            MaskType.POKESTOP: self.pokestop_mask,
            MaskType.TEAMROCKET: self.teamrocket_mask
        }

        places = {
            MaskType.POKESTOP: self.pokestops,
            MaskType.TEAMROCKET: self.teamrocket
        }

        if mask_type in switch:
            t = time.time()

            img_array = self.interactable_crop
            img_list = self.interactable_crop.tolist()

            for pixel_row in range(0, len(img_array)):
                for pixel_i in range(0, len(img_array[pixel_row])):
                    if switch[mask_type](img_list[pixel_row][pixel_i], pixel_i, pixel_row):
                        if visualise:
                            img_array[pixel_row][pixel_i][3] = 0

            self._logger.info("Took {}s to mask with {}".format(time.time() - t, mask_type))

            t = time.time()
            self.mask_final(img_array, places[mask_type], mask_type, visualise)
            self._logger.info("Took {}s applying {} mask fix".format(time.time() - t, mask_type))
        else:
            self._logger.warning("Could not apply non-existent mask {}".format(mask_type))

# player is ~ 550 1510c / 50% 63%
