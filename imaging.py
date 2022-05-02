import time
import logging
import numpy as np

from PIL import Image

class Imager:
    def __init__(self, device):
        self.im = None
        self.device = device
        self._logger = logging.getLogger("Imager")

        self.pokestops = []
        self.pokemon = []
        self.gyms = []

    def load_new_image(self, image):
        if self.im is not None:
            self.im.close()

        self.im = Image.open(image)

    def _crop(self, point1, point2):
        point1 = self.device._point_from_percent(point1)
        point2 = self.device._point_from_percent(point2)

        return self.im.crop([point1[0], point1[1], point2[0], point2[1]])

    def _coords_are_close(self, coord1, coord2):
        if abs(coord1[0] - coord2[0]) < 80 and abs(coord1[1] - coord2[1]) < 80:
            return True

        return False

    def _apply_pokestop_mask(self, pixel):
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
    
    def _apply_pokestop_mask_visualise(self, pixel):
        # Mask out anything will lower blue levels
        if pixel[2] < 230:
            return [0, 0, 0, 0]
        # Mask out white/grays
        elif abs(pixel[0] - pixel[1]) < 50 and abs(pixel[0] - pixel[2]) < 50:
            return [0, 0, 0, 0]
        # Mask out purple (collected pokestops)
        elif pixel[0] > 150:
            return [0, 0, 0, 0]

        return [0, 0, pixel[2], 255]
    

    def pokestop_mask(self, visualise=False):
        # Having visualise=False can save > 1second

        t = time.time()
        img_array = np.array(self._crop([0, 50], [100, 86]))

        for pixel_row in range(0, len(img_array)):
            for pixel_i in range(0, len(img_array[pixel_row])):
                if visualise:
                    pixel = img_array[pixel_row][pixel_i]
                    img_array[pixel_row][pixel_i] = np.array(
                        self._apply_pokestop_mask_visualise(pixel.tolist()), dtype=int)

                    filtered = pixel[3] == 255
                else:
                    filtered = self._apply_pokestop_mask(img_array[pixel_row][pixel_i].tolist())
                
                if filtered:
                    close = False
                    for coords in range(0, len(self.pokestops)):
                        if self._coords_are_close([pixel_i, pixel_row], self.pokestops[coords][0]):
                            self.pokestops[coords][1] += 1
                            self.pokestops[coords][2].append(pixel_i)
                            self.pokestops[coords][3].append(pixel_row)

                            close = True
                            break

                    if not close:
                        self.pokestops.append([(pixel_i, pixel_row), 1, [pixel_i], [pixel_row]])
                        self._logger.debug(
                            "Found potential pokestop at [{}, {}]".format(
                                pixel_i, pixel_row))
                    
        if visualise:
            Image.fromarray(img_array).save("visualise_pokestop_mask.png")

        toremove = []
        for pokestop in range(0, len(self.pokestops)):
            ps = self.pokestops[pokestop]
            if ps[1] < 500:
                toremove.insert(0, pokestop)
            else:
                x = ps[2][round(len(ps[2])/2)]/self.device.r_screen_size[0]*100
                y = (ps[3][round(len(ps[3])/2)]+(self.device.r_screen_size[1]/2))/self.device.r_screen_size[1]*100

                self.pokestops[pokestop] = [(x, y), ps[1]]

        for ps in toremove:
            ''' Doesn't work for now :')
            if visualise:
                for pos in range(0, len(self.pokestops[ps][2])):
                    img_array[self.pokestops[ps][3][pos]][self.pokestops[ps][2][pos]] = np.array([0, 0, 0, 0], dtype=int)
            '''
                    
            self._logger.debug("Removed pokestop at x{} y{}, density too low".format(
                self.pokestops[ps][0][0], self.pokestops[ps][0][1]))
            del self.pokestops[ps]

        self.pokestops.sort(reverse=True, key=lambda stop: stop[1])
        self._logger.debug("Took {}s applying pokestop mask".format(time.time() - t))


# player is ~ 550 1510c / 50% 63%