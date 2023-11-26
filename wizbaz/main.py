from os import path
from time import sleep
import cv2 as cv
import numpy as np
from mss import mss
import pyautogui as pyag

from definitions import IMG_DIR, IMG_SCALE, LINE_THICKNESS, LINE_LEN, CLICK_DELAY


def midpoint(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
    return reset_scale((round((p1[0]+p2[0])/2), round((p1[1]+p2[1])/2)))


# Assumes both are greyscale
def apply_template(img, template) -> np.ndarray:
    if (len(template.shape) > 3):
        raise Exception("Template is not in grayscale")
    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

    return cv.matchTemplate(img, template, cv.TM_CCOEFF_NORMED)


def read_template(tmp: str) -> np.ndarray:
    return scale_img(cv.imread(path.join(IMG_DIR, tmp), cv.IMREAD_GRAYSCALE))


def get_bounding_points(maxLoc, dims):
    # Returns Top left and Bottom Right points.
    return ((maxLoc[0], maxLoc[1]), (maxLoc[0]+dims[1], maxLoc[1]+dims[0]))


# Returns the middlepoint of the found template
def find_template(img: np.ndarray, tmp: str):
    template = read_template(tmp)
    res = apply_template(img, template)
    loc = np.where(res >= 0.8)
    if (loc[0].shape[0] == 0):
        return None
    _, _, _, maxLoc = cv.minMaxLoc(res, None)
    p1, p2 = get_bounding_points(maxLoc, template.shape)
    return (midpoint(p1, p2))


def find_nav_btn(img: np.ndarray, type: str):
    is_active = True

    if (type not in ['left', 'right']):
        raise Exception(f"Invalid type '{type}', must be either 'left' or 'right'")

    template = read_template(f"{type}_active_btn.png")
    res = apply_template(img, template)
    loc = np.where(res >= 0.9)
    if (loc[0].shape[0] == 0):
        is_active = False
        template = read_template(f"{type}_inactive_btn.png")
        res = apply_template(img, template)

    _, _, _, maxLoc = cv.minMaxLoc(res, None)
    p1, p2 = get_bounding_points(maxLoc, template.shape)
    return (is_active, midpoint(p1, p2))


def scale_img(img):
    h, w = img.shape[:2]
    return cv.resize(img, (round(w*IMG_SCALE), round(h*IMG_SCALE)),
                     interpolation=cv.INTER_AREA)


def reset_scale(point: tuple[int, int]):
    return (round(point[0]/IMG_SCALE), round(point[1]/IMG_SCALE))


def draw_x(img, p):
    tl = (p[0]-LINE_LEN, p[1]-LINE_LEN)
    br = (p[0]+LINE_LEN, p[1]+LINE_LEN)
    tr = (p[0]+LINE_LEN, p[1]-LINE_LEN)
    bl = (p[0]-LINE_LEN, p[1]+LINE_LEN)
    img = cv.line(img, tl, br, color=(0,0,255), thickness=LINE_THICKNESS)
    img = cv.line(img, tr, bl, color=(0,0,255), thickness=LINE_THICKNESS)
    return img


def draw_all_xes(img, points):
    for p in points:
        img = draw_x(img, p)
    return img


def dclick(x, y):
    pyag.moveTo(x+1920, y, CLICK_DELAY)
    pyag.click()


def reset_shop(buy_tab, sell_tab):
    bx, by = buy_tab
    sx, sy = sell_tab
    dclick(sx, sy)
    # print(f"Clicked Sell Tab at ({sx+1920}, {sy})")
    dclick(bx, by)
    # print(f"Clicked Buy Tab at ({bx+1920}, {by})")


def take_screenshot(sct):
    return scale_img(np.array(sct.grab(sct.monitors[1])))


def is_btn_active(img, type):
    return find_nav_btn(img, type)[0]


# Returns None if entire shop lacks reagent
def find_reagent(sct, right_btn, reagent: str):
    img = take_screenshot(sct)
    x, y = right_btn
    result = None
    template = read_template(reagent)

    found = False
    while (not found and is_btn_active(img, "right")):
        res = apply_template(img, template)
        loc = np.where(res >= 0.9)
        if (loc[0].shape[0] != 0):
            found = True
            _, _, _, maxLoc = cv.minMaxLoc(res, None)
            p1, p2 = get_bounding_points(maxLoc, template.shape)
            result = midpoint(p1, p2)
            continue
        else:
            dclick(x, y)
            # print(f"clicking pos ({x}, {y})")
            img = take_screenshot(sct)
    return result


def buy_reagent(sct, reagent_pos, buy_more_pos):
    try:
        dclick(*reagent_pos)
        dclick(*buy_more_pos)
        sleep(0.2)
        # Inside of buy more dialog
        img = take_screenshot(sct)
        buy_btn = find_template(img, "buy_btn.png")
        assert buy_btn is not None
        num_entry = find_template(img, "num_entry.png")
        assert num_entry is not None

        dclick(*num_entry)
        pyag.write("999")
        pyag.press("enter")
        sleep(0.1)
        dclick(*buy_btn)

        # In "purchased" dialog
        sleep(0.5)
        img = take_screenshot(sct)
        ok_btn = find_template(img, "ok_btn.png")
        dclick(*ok_btn)
    except AssertionError:
        print("Assuming out of gold, exiting...")


if __name__ == '__main__':
    with mss() as sct:
        monitor = sct.monitors[1]
        img_orig = np.array(sct.grab(monitor))
        img = scale_img(img_orig)

        BUY_TAB_POS = find_template(img, "buy_tab_btn.png")
        SELL_TAB_POS = find_template(img, "sell_tab_btn.png")
        BUY_MORE_POS = find_template(img, "buy_more_btn.png")

        right_btn = find_nav_btn(img, 'right')

        while (True):
            reagent_pos = find_reagent(sct, right_btn[1], "reagent_iron.png")
            if (reagent_pos is None):
                print("Reagent not found, reseting...")
            else:
                print("Reagent found, buying...")
                buy_reagent(sct, reagent_pos, BUY_MORE_POS)
            reset_shop(BUY_TAB_POS, SELL_TAB_POS)
            sleep(2.5)

        # points = [BUY_TAB_POS, SELL_TAB_POS, BUY_MORE_POS, left_btn[1], right_btn[1]]
        # cv.imwrite('tmp.png', draw_all_xes(img_orig, points))
