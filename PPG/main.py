import imaging
import pkgo
import logging
import time

from enums import MaskType


logging.basicConfig(level=logging.DEBUG)

pokego = pkgo.PokemonGoHandler()
imager = imaging.Imager(pokego)

pokego.set_size([720, 1280])
pokego.pull_screen()
imager.load_new_image("screengrab.png")

imager.apply_mask(MaskType.POKESTOP, False)

for pokestop in imager.pokestops:
    pokego.do_tap(pokestop[0])
    time.sleep(2)

pokego.set_size()

'''
SPEED TESTS

1080x2400 vis 0.786
1080x2400 novis 0.253
1080x1920 vis 0.659
1080x1920 novis 0.187
720x1280 vis 0.319
720x1280 novis 0.084

OLD SPEED TESTS

1080x2400 full 16.88
1080x2400 full/novisualise 7.92
1080x2400 crop 4.57
1080x2400 crop/novisualise 1.38
1080x1920 full 13.67
1080x1920 full/novisualise 6.71
1080x1920 crop 3.66
1080x1920 crop/novisualise 1.13
720x1280 full 6.03
720x1280 full/novisualise 2.78
720x1280 crop 1.63
720x1280 crop/novisualise 0.50
'''