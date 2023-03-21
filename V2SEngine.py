from itertools import starmap
from os import environ
from time import sleep
from typing import List, Tuple
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from bisect import bisect_left
from transitions import Machine, EventData
from V2SConverter import V2SConverter

class V2SEngine:
    """
    Play the converted video from the passed-in V2SConverter module

    Params
    ------
    - `converter`: Initialized V2SConverter
    - `strategy`: playing strategy. `0`: render before playing; `1`: render when playing (int)

    TODO:
        - Optimize the memory usage while ensuring the 2 strategies compatible

    """
    __states = ["onPlay", "onPause", "onPlayingDrag", "onPausingDrag", "destroyed"]
    __trans = [
        {"trigger": "playPauseSwitch", "source": "onPlay",         "dest": "onPause"},
        {"trigger": "playPauseSwitch", "source": "onPause",        "dest": "onPlay"},
        {"trigger": "dragAtPlay",      "source": "onPlay",         "dest": "onPlayingDrag"},
        {"trigger": "dragAtPause",     "source": "onPause",        "dest": "onPausingDrag"},
        {"trigger": "releasePlay",     "source": "onPlayingDrag",  "dest": "onPlay"},
        {"trigger": "releasePause",    "source": "onPausingDrag",  "dest": "onPause"},
        {"trigger": "destroy",         "source": "*",              "dest": "destroyed"},
    ]
    def __init__(self, converter: V2SConverter, strategy: int) -> None:
        pygame.init()
        self.strategy = strategy
        self.converter = converter
        self.player = pygame.mixer.music
        self.totalSec = len(self.converter.imgBook) / self.converter.fps
        self.machine = Machine(self, states=V2SEngine.__states, transitions=V2SEngine.__trans, initial="onPause", send_event=True)
        self.base = 0  # disgusting pygame arg
        self.curLrcIdx = 0
        self.__now = 0  # 0-1
        self.bufferedImgs = []
        if not self.strategy:
            self.bufferImages()
        self.player.load("buffer.mp3")
        self.player.play()
        self.player.pause()

    def loop(self) -> None:   # should NOT be called by the main thread
        while 1:
            match self.state:
                case "destroyed":
                    self.player.unload()
                    return
                case "onPlay":
                    self.__now = (self.player.get_pos() / 1000) / self.totalSec + self.base
                    if (newIdx := self.curLrcIdx + 1) != len(self.converter.lrcList) and self.__now * self.totalSec >= self.converter.lrcList[newIdx][0]:
                        self.curLrcIdx = newIdx
                    if self.__now >= 0.999:  # Completed playing
                        if "Drag" in self.state:
                            self.release()
                        self.switch(None)
                        self.setPerc(0)
                case _:
                    ...
            sleep(1 / self.converter.fps)  # CRUCIAL to performance, avoid redundant updates
    
    def switch(self, e: EventData | None = None) -> None:
        """
        Switch the state between playing and pausing
        """
        self.playPauseSwitch()
        match self.state:
            case "onPlay":
                self.player.unpause()
            case "onPause":
                self.player.pause()
            case _:
                ...
    
    def getCurState(self) -> str:
        """
        Return the current engine state
        """
        return self.state
    
    def getPerc(self) -> float:
        """
        Return the playing process (as percentage from 0 to 1)
        """
        return self.__now
    
    def getCurInfo(self) -> Tuple[str, str]:
        """
        Return the current view of the engine, containing the current frame and lyrics
        """
        match self.strategy:
            case 1:
                img = self.converter.getFrame(self.__now)
            case 0:
                img = self.bufferedImgs[round(self.__now * (len(self.bufferedImgs) - 1))]
            case _:
                img = ""
        lrc = self.converter.lrcList[self.curLrcIdx][1]
        return img, lrc
    
    def setPerc(self, t: float) -> None:
        """
        Set the current engine process

        Param
        -----
        - `t`: process denoted as percentage (from 0 to 1)
        """
        if not 0 <= t <= 1:
            raise ValueError(f"Expected time to be in [0, 1], while given {t}")
        
        match self.state:
            case "onPlay":
                self.player.pause()
                self.dragAtPlay()
            case "onPause":
                self.dragAtPause()
            case _:
                ...
        
        self.base = self.__now = t
        t = self.__now * self.totalSec
                
        self.curLrcIdx = max(0, bisect_left(self.converter.lrcList, t + 1e-6, key=lambda x: x[0]) - 1)

        self.player.play(start=t)
        self.player.pause()
        if self.state in ["onPlayingDrag", "onPausingDrag"]:
            self.release()
    
    def bufferImages(self) -> List[str]:
        """
        Render and return the list of rendered images from loaded video
        """
        self.bufferedImgs = [
            self.converter.render(x, self.converter.pixelSet)
            for x in self.converter.imgBook
        ]

    def release(self) -> None:
        """
        Cancel the drag state and restore to the state where the engine at before dragged
        """
        match self.state:
            case "onPlayingDrag":
                self.releasePlay()
                self.player.unpause()
            case "onPausingDrag":
                self.releasePause()
            case _:
                ...

    def on_enter_destroy(self) -> None:
        self = V2SEngine(self.converter, self.strategy)