import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(ROOT_DIR, 'resources')
IMG_DIR = os.path.join(RESOURCE_DIR, 'imgs')

IMG_SCALE = 1/4
LINE_THICKNESS = round(3 / IMG_SCALE)
LINE_LEN = round(8 / IMG_SCALE)
CLICK_DELAY = 0.1
