import re
import cv2
import numpy as np
from typing import Any
from functools import cache

# PxlToChrConsolas = [(0.0, ' '), (0.0338256817950028, '`'), (0.06038400256465478, '_'), (0.1031548341232787, "'"), (0.14023629970635199, '"'), (0.19635218230015475, '.'), (0.22601551259737007, '^'), (0.25891135929878006, ','), (0.2735762462995739, '-'), (0.3445939809589873, ':'), (0.3774437364649546, '~'), (0.41085416064945796, '*'), (0.4323972714254259, ';'), (0.45845451342385996, '='), (0.46881434969863267, 'r'), (0.47530120492049516, 'L'), (0.479260689294568, '!'), (0.481913796090146, '/'), (0.4923376277517668, '\\'), (0.5121580280119277, '['), (0.5139450800354002, '<'), (0.5200041366478282, '>'), (0.5248836437583435, 'C'), (0.5383723147703382, 'c'), (0.5402922301421171, '?'), (0.5440060762685631, '('), (0.5636446958916976, ')'), (0.5761369690804913, 'J'), (0.5819986427359428, 'F'), (0.5877564331006455, 'U'), (0.5882627238464987, ']'), (0.590060670274725, '|'), (0.6023798259281136, '7'), (0.6095596251074707, '{'), (0.6105722133199729, 'j'), (0.6106637337127919, 'n'), (0.6157497203730258, 'u'), (0.6160997258084664, 'T'), (0.6276263555208564, '+'), (0.6312958074519822, 'v'), (0.6324782200115308, '}'), (0.6463269910894083, 'O'), (0.6490122232734695, 'h'), (0.6537678325729626, 'o'), (0.6569075617149418, 'P'), (0.6608656649661401, 'H'), (0.6646286098427036, 'D'), (0.6725079763206332, 'Y'), (0.673600780552851, 't'), (0.6781875164974477, 'f'), (0.6806166461598506, 'l'), (0.6810801153758481, 'i'), (0.6817768296979745, '3'), (0.6930214683957272, '5'), (0.6996269556876324, 's'), (0.7059324805655696, '2'), (0.7149349788521866, 'y'), (0.7157369710295225, 'E'), (0.7162526070374449, 'I'), (0.7176051934252519, 'z'), (0.7207869476831692, 'G'), (0.7210831262909205, 'b'), (0.72134874209446, 'p'), (0.7229038965307116, 'Z'), (0.7242675755866551, 'M'), (0.7252316766411642, 'x'), (0.7268772727830275, 'd'), (0.7269886161535278, '1'), (0.7298606359650802, 'Q'), (0.7323440662710492, '%'), (0.7327817881307134, 'q'), (0.7333136078071439, 'w'), (0.7418663069698506, 'S'), (0.742039989051831, 'V'), (0.7531816551262294, 'e'), (0.7613307740555255, 'k'), (0.7718015370116589, 'm'), (0.7723422012511125, 'a'), (0.7800802429028889, '9'), (0.7832353727410407, '6'), (0.796812687646632, 'K'), (0.800469743075864, 'W'), (0.8075584284703562, 'R'), (0.8076400793792844, 'X'), (0.8151893675717421, 'A'), (0.8233377203306864, '4'), (0.8356712013534359, 'N'), (0.8378120325373746, 'g'), (0.8564806536105232, '0'), (0.8614395736060404, '8'), (0.8630910638829851, 'B'), (0.8651030238694034, '#'), (0.9436950480696324, '&'), (0.9642596887365757, '$'), (1.0, '@')]
DEFAULT_PIXEL_KWARGS = {'SetLen': 70}

class PixelFactory:
    """
    Pixel tiles collection
    """
    def __init__(self):
        ...

    @staticmethod
    @cache
    def getPxls(mode: int, **kwargs) -> str:
        match mode:
            case 0:
                return " `'-·,‘”^*:;!\|[+=><?1IiljUQTY234980M#$§%&@"
            case 1:
                return " `'-·,‘”^*:;!\|[+=><?1IiljUQTY234980▲■▌░▒▓█"
            case 2:
                from bisect import bisect_left
                from ChrDensityChecker import Checker

                font = kwargs.get("Font", "Consolas")
                pxls = kwargs.get("PxlSet", None)
                model = Checker(font, pxls)
                pxls = model.getWeightTable("CenterWeighted")
                l = kwargs.get("SetLen", len(pxls))

                ans = ""
                for w in np.linspace(0, 1, l):
                    i2 = (i1 := bisect_left(pxls, w, key=lambda x: x[0])) - 1
                    i = i1 if abs(pxls[i1][0] - w) <= abs(pxls[i2][0] - w) else i2
                    ans += pxls[i][1]
                return ans
            case _:
                return " "
            

class V2SConverter:
    """
    Load original video file (image & music) and convert it into char pictures.
    
    Load, parse, and keep lyrics file.
    
    This module is the data structure which does not involve any dynamics from time.

    Params
    ------
    - reso: resolution (tuple)
    - pixelMode: the pixel set to choose (int, start from 0)
    - pixelArgs: args used in pixel factory (PxlSet, SetLen, Font)
    - font: the font of the chrs (str)

    TODO: None
    """
    def __init__(self, reso: tuple, strategy: int, pixelMode: int = 2, pixelArgs: dict = DEFAULT_PIXEL_KWARGS, font: str = "Consolas") -> None:
        self.font = font
        self.reso = reso
        self.strategy = strategy  # 0: average
        self.pixelMode = pixelMode
        self.pixelSet = np.array(list(PixelFactory.getPxls(self.pixelMode, **pixelArgs)))
        
        # (resolution, pixelMode, font)
        # if info is changed, the mismatched picture will be lazily and dynamically re-rendered
        self.currentVideoInfo = (self.reso, self.pixelMode, self.font)

        self.vDir = self.lDir = ""
        self.imgBook = self.fps = self.renderedImgs = self.imgInfoList = None
        self.lrcList = [[np.Inf, '\n'.join("No Lyrics")]]

    def loadRawVideo(self, filePath: str) -> bool:
        """
        Load the raw video into the class (imgBook & fps & music)

        Param
        -----
            - `filePath`: path of file to be loaded
        """
        # Video
        imgs = []
        cap = cv2.VideoCapture(filePath)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            imgs.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) / 255)
        self.imgBook = imgs
        self.imgInfoList = [None] * len(self.imgBook)
        self.renderedImgs = [None] * len(self.imgBook)
        self.fps = cap.get(5)
        cap.release()

        # Music
        from moviepy.editor import VideoFileClip
        VideoFileClip(filePath).audio.write_audiofile("buffer.mp3")

        self.vDir = filePath
        return True
    
    def loadLrc(self, filePath: str) -> None:
        """
        Load lyrics file

        Param
        -----
            - `filePath`: path of file to be loaded
        """
        try:
            lrc = []
            with open(filePath, "r", encoding='utf-8') as f:
                lst = f.read().split("\n")

            for line in lst:
                obj = re.search(r"^\[(\d+):(\d+)\.(\d+)\](.*)$", line)
                if not obj: break
                time = int(obj.group(1)) * 60 + \
                    int(obj.group(2)) + \
                    int(obj.group(3)) / 10**(len(obj.group(3)))
                word = obj.group(4)
                lrc.append([time, "\n".join(word)])

            if not lrc:
                raise Exception("Parsed Empty Lyrics")
            self.lrcList = lrc + [[np.Inf, '\n'.join("No Lyrics")]]
            self.lDir = filePath
        except Exception as e:
            raise e

    def render(self, originalImg: np.ndarray[Any, np.ndarray[Any, float]], pxlSet: np.ndarray[Any, str]) -> str:
        """
        Resize & Convert a grey image to an ascii string image

        Params
        ------
            - `originalImg`: a 1-channel grey picture, stored as `numpy.ndarray`
            - `pxlSet`: the set of pixels to replace the pixels in `originalImg`
        """
        originalImg = cv2.resize(
            originalImg,
            self.reso,
            interpolation=cv2.INTER_AREA,
        )
        frame = pxlSet[(originalImg * (len(pxlSet) - 1)).astype(np.int)]
        return "\n".join(map(''.join, frame))
    
    def setVideoAttr(self, **kwargs) -> bool:
        """
        Update the current video attribute, which may result in re-rendering.

        Params
        ------
            - `reso`: tuple
            - `pixelMode`: int
            - `pixelArgs`: dict
            - `font`: str
        """
        self.reso = kwargs.get("reso", self.reso)
        pixelMode = kwargs.get("pixelMode", self.pixelMode)
        self.font = kwargs.get("font", self.font)
        if self.pixelMode != pixelMode:
            self.pixelMode = pixelMode
            self.pixelSet = np.array(list(PixelFactory.getPxls(pixelMode, **kwargs.get("pixelArgs", DEFAULT_PIXEL_KWARGS))))
        self.currentVideoInfo = (self.reso, self.pixelMode, self.font)
        return True
    
    def getFrame(self, perc: float) -> str:
        """
        Get the image with index `round(perc * len(self.renderedImgs))`

        Param
        -----
            - `perc`: progress percentage (from `0` to `1`, inclusive)
        """
        i = round(perc * (len(self.renderedImgs) - 1))
        if self.currentVideoInfo == self.imgInfoList[i]:
            return self.renderedImgs[i]
        self.imgInfoList[i] = self.currentVideoInfo
        self.renderedImgs[i] = self.render(self.imgBook[i], self.pixelSet)
        return self.renderedImgs[i]
    
    def saveProcessed(self, filePath: str) -> bool:
        """
        Save processed video (equivalent to saving the class status)

        Param
        -----
            - `filePath`: path of file to be saved
        """
        import pickle
        with open(filePath, "bw") as f:
            pickle.dump([
                self.currentVideoInfo,
                self.fps,
                self.imgBook,
                self.pixelSet,
                self.lrcList,
                self.vDir,
                self.lDir,
            ], f)
        return True
    
    def loadProcessed(self, filePath: str) -> bool:
        """
        Load processed video (equivalent to loading the class status)

        Param
        -----
            - `filePath`: path of file to be loaded
        """
        import pickle
        from moviepy.editor import VideoFileClip
        with open(filePath, "br") as f:
            self.currentVideoInfo, self.fps, self.imgBook, \
                self.pixelSet, self.lrcList, self.vDir, self.lDir = pickle.load(f)
        self.reso, self.pixelMode, self.font = self.currentVideoInfo
        self.renderedImgs = [None] * len(self.imgBook)
        self.imgInfoList = [None] * len(self.imgBook)
        VideoFileClip(self.vDir).audio.write_audiofile("buffer.mp3")
        return True
