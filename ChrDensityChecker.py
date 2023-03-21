import numpy as np
from typing import List, Tuple
from functools import cache
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

SAVE = 0

class Checker:
    """
    Check the density of a set of character and produce a sorted weight table 

    TODO:
    - Cut image according to the font size
        (It may significantly affect the performance of the center weighted algorithm)
    """
    def __init__(self, font: str = "Consolas", pixelSet: List[str] = None, fontStyle: str = "bold") -> None:
        self.alphabet = pixelSet if pixelSet else list(map(chr, range(32, 127)))
        self.fontFilePath = font_manager.findfont(font_manager.FontProperties(family=font, weight=fontStyle))
        self.W = 44
        self.H = 77

    def drawChr(self, char: str, w: int | None = None, h: int | None = None) -> Image:
        """
        Draw a character to an image

        Params
        ------
            - `char`: the character to be drawn
            - `w`: image width
            - `h`: image height
        """
        w = w if w else self.W
        h = h if h else self.H
        img = Image.new('RGB', (w, h), 'white')

        draw = ImageDraw.Draw(img)
        draw.text(
            (0, 0),
            char,
            font=ImageFont.truetype(self.fontFilePath, 80),
            fill='#000000',
        )

        if SAVE:
            img.save("imgs/{}.png".format(ord(char)), 'PNG')

        return img


    def cntPxl(self, img: Image, countingAlgo: str) -> float | None:
        """
        Count the black/non-white pixels in the image

        Params
        ------
            - `img`: image that previously drawn with a character
            - `countingAlgo`: the name of the counting algorithm, which should be one of
                            `["Simple", "CenterWeighted"]`.
                - The `Simple` algorithm simply counts non-white
                pixels.
                - The `CenterWeighted` algorithm puts more weights on the pixels lying on
                the center of the image.
        """
        W, H = img.size
        pixels = list(img.getdata())

        match countingAlgo:
            case "CenterWeighted":
                # weight is larger when it gets closer to the center
                @cache
                def getCenterWeight(ci, cj, i, j):
                    return (1 - abs(i - ci) / ci) * (1 - abs(j - cj) / cj)
                
                centerX, centerY = H // 2, W // 2
                ans = 0
                for i in range(len(pixels)):
                    h, w = divmod(i, W)
                    weight = getCenterWeight(centerX, centerY, h, w)
                    ans += weight * sum(1 - x / 255 for x in pixels[i])
                return ans
            case "Simple":
                # simple black pxl count
                return sum(sum(rgb) < 250 * 3 for rgb in pixels)
            case _:
                raise ValueError(f"Unsupported Counting Algorithm: {countingAlgo}")

    def getWeightTable(self, countingAlgo: str) -> List[Tuple[float, str]]:
        """
        Produce a list of items with the second element to be the character and
        the first element to be the relative density associated with that character (scaled to [0, 1]).
        The larger the density is, the more pixels it will take on the screen.

        Param
        -----
            - `countingAlgo`: name of the counting algorithm, which should be one of
                            `["Simple", "CenterWeighted"]`.
                - The `Simple` algorithm simply counts non-white
                pixels.
                - The `CenterWeighted` algorithm puts more weights on the pixels lying on
                the center of the image.
        """
        v = np.array([self.cntPxl(self.drawChr(letter), countingAlgo) for letter in self.alphabet])
        v = (v - min(v)) / (max(v) - min(v))
        return sorted(zip(v, self.alphabet))


if __name__ == '__main__':
    """
    Consolas
    Bold
    Ascii
    CenterWeighted
    """
    SAVE = 1
    model = Checker()
    print(model.getWeightTable("CenterWeighted"))