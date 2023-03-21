import os
from threading import Thread
from V2SUI import V2SUI
from V2SEngine import V2SEngine
from V2SConverter import V2SConverter


class V2SController:
    """
    Bridge between V2SEngine, V2SUI, and V2SConverter. Main entrance of the project.

    One controller should be used to control one and only one ui/converter/engine.

    Param
    -----
    - `ui`: initialized V2SUI
    
    TODO: None
    """
    def __init__(self, ui: V2SUI) -> None:
        self.ui = ui
        self.engine = None
        self.converter = V2SConverter(self.ui.monitorSize, self.ui.dynamicReso.get())

    def run(self) -> None:
        """
        Activate the controller.
        """
        self.bindMainUICommand()
        self.ui.root.mainloop()

    def bindMainUICommand(self) -> None:
        """
        Bind functions and commands to the ui
        """
        self.ui.systmenu.add_command(command=self.initConfig, label="Config")
        self.ui.systmenu.add_command(command=self.ui.root.destroy, label="Exit")
        self.ui.root.protocol("WM_DELETE_WINDOW", self.destroyMain)

        # Vars (Config)
        self.ui.pixelSet.trace_add("write", self.onChangePixelSet)
        self.ui.resolution.trace_add("write", self.onChangeResolution)
        self.ui.fontScale.trace_add("write", self.onChangeFontScale)

        # Console
        widgetCommandPairs = [
            [self.ui.lrcBt, self.loadLrc],
            [self.ui.rawVideoBt, self.loadRawVideo],
            [self.ui.videoBt, self.loadProcessedVideo],
            [self.ui.monitorBt, self.initMonitor],
        ]
        for ele, com in widgetCommandPairs:
            ele["command"] = com

    def initConfig(self) -> None:
        """
        Initialization process of the config panel.
        """
        self.ui.showConfig()
        self.ui.configWin.protocol("WM_DELETE_WINDOW", self.destroyConfig)

    def destroyConfig(self) -> None:
        """
        Destroy process of the config panel.
        """
        self.ui.configWin.destroy()
        self.ui.strategyCheck = self.ui.configWin = None

    def destroyMain(self) -> None:
        """
        Destroy process of the main console.
        """
        if self.engine:
            self.engine.destroy()
        if self.ui.monitorWin:
            self.destroyMonitor()
        self.ui.root.destroy()

    def onChangePixelSet(self, *args) -> None:
        """
        The callback function called when the `self.ui.pixelSet` is changed.
        """
        self.converter.setVideoAttr(pixelMode=self.ui.pixelSet.get())
        if self.engine and not self.engine.strategy:
            self.engine.switch(None)
            self.engine.bufferedImgs = self.engine.bufferImages()
            self.engine.switch(None)

    def onChangeResolution(self, *args) -> None:
        """
        The callback function called when the `self.ui.resolution` is changed.
        """
        self.ui.monitorSize = [
            int(200 * self.ui.resolution.get()),
            int(80 * self.ui.resolution.get())
        ]
        if not self.engine or not self.engine.strategy:
            return
        if self.engine.getCurState() == "onPlay":
            self.handlePlayBtn()
            self.converter.setVideoAttr(reso=self.ui.monitorSize)
            self.handlePlayBtn()
        else:
            self.converter.setVideoAttr(reso=self.ui.monitorSize)
        if self.ui.monitorWin:
            self.ui.videoPane.config(font=[
                self.ui.font,
                self.resoToFontSize(self.ui.resolution.get(), self.ui.fontScale.get()),
                "bold",
            ])

    def onChangeFontScale(self, *args) -> None:
        if self.ui.monitorWin:
            self.ui.videoPane.config(font=[
                self.ui.font,
                self.resoToFontSize(self.ui.resolution.get(), self.ui.fontScale.get()),
                "bold",
            ])

    def resoToFontSize(self, reso: float, scale: float) -> int:
        """
        Map the resolution to the font size in the screen.
        """
        return max(int((11 - 4 * reso) * scale), 1)

    def loadLrc(self) -> None:
        """
        Load lrc file to the converter.
        """
        self.updateStatus("Loading Lyrics...")
        path = self.ui.askLoadPath("Choose Lyrics File")
        if not path:
            self.updateStatus("Lyrics Loading Cancelled")
            return

        try:
            self.converter.loadLrc(path)
            self.updateStatus("Lyrics Loading Completed")
        except Exception as e:
            self.updateStatus("Lyrics Loading Failed")
            print(e)

    def loadRawVideo(self) -> None:
        """
        Load video & lyrics file to the converter.

        If beffer is allowed, then buffer the video file.

        If completed, lauch monitor.
        """
        self.updateStatus("Loading New Video...")
        path = self.ui.askLoadPath("Choose Video File")
        if not path:
            self.updateStatus("Video Loading Cancelled")
            return

        try:
            self.destroyMonitor()
            self.converter.loadRawVideo(path)
            self.loadLrc()
            if self.ui.allowBuffer.get():
                self.saveProcessedVideo("buffer")
            self.updateStatus("Video Loading Completed")
            self.initMonitor()
        except Exception as e:
            self.updateStatus("Video Loading Failed")
            print(e)

    def loadProcessedVideo(self, filePath: str | None = None) -> None:
        """
        The procedure to load processed video (state of the converter).
        """
        self.updateStatus("Loading Processed Video...")
        if not filePath:
            filePath = self.ui.askLoadPath("Choose Video File")
            if not filePath:
                self.updateStatus("Video Loading Cancelled")
                return

        try:
            self.converter.loadProcessed(filePath)
            self.updateStatus("Video Loading Completed")
        except Exception as e:
            self.updateStatus("Video Loading Failed")
            print(e)

    def saveProcessedVideo(self, filePath: str | None = None) -> None:
        """
        The procedure to save processed video (state of the converter).
        """
        self.updateStatus("Saving Processed Video...")
        if not filePath:
            filePath = self.ui.askSavePath("Choose Video File")
            if not filePath:
                self.updateStatus("Video Saving Cancelled")
                return

        try:
            self.converter.saveProcessed(filePath)
            self.updateStatus("Video Saving Completed")
        except Exception as e:
            self.updateStatus("Video Saving Failed")
            print(e)

    def bindMonitorCommand(self) -> None:
        """
        Bind functions and commands to the monitor.
        """
        self.ui.monitorWin.protocol("WM_DELETE_WINDOW", self.destroyMonitor)
        widgetCommandPairs = [
            [self.ui.playBt, self.handlePlayBtn],
            [self.ui.saveBt, self.saveProcessedVideo],
            [self.ui.processBar, self.handleProcess],
        ]
        for ele, com in widgetCommandPairs:
            ele["command"] = com

    def handlePlayBtn(self) -> None:
        """
        Callback function when the play button is clicked.
        
        Switch the engine state between play and pause.
        """
        self.engine.switch(None)

    def handleProcess(self, event=None) -> None:
        """
        Callback function when the progrss bar is dragged.
        
        Change the engine progress.
        """
        self.engine.setPerc(self.ui.process.get())

    def checkLoaded(self) -> int:
        """
        Check whether the converter has loaded a video before lauching the monitor.
        """
        if self.converter.imgBook:
            return 1
        if os.path.exists("buffer"):
            self.loadProcessedVideo("buffer")
            return 1
        if not self.ui.okCancel("Load Video",
                                "No buffer file found\nLoad a new video?"):
            return 0
        try:
            self.loadRawVideo()
            return 1
        except:
            return 0

    def initMonitor(self) -> None:
        """
        Procedures before lauching the monitor
        """
        if not self.checkLoaded() or self.engine:  # Loaded and no multi window
            return

        self.updateStatus("Rendering...")
        self.engine = V2SEngine(self.converter, self.ui.dynamicReso.get())
        self.updateStatus("Render Completed")
        if self.ui.strategyCheck:
            self.ui.strategyCheck["state"] = "disabled"
        self.ui.showMonitor(processReso=1 / len(self.converter.imgBook))
        self.ui.videoPane.config(font=[
            self.ui.font,
            self.resoToFontSize(self.ui.resolution.get(), self.ui.fontScale.get()),
            "bold",
        ])
        self.bindMonitorCommand()
        Thread(target=self.engine.loop, daemon=True).start()
        Thread(target=self.updateScreen, daemon=True).start()

    def destroyMonitor(self) -> None:
        """
        Procedures to destroy the monitor
        """
        if self.engine:
            self.engine.destroy()
        if self.ui.monitorWin:
            self.ui.monitorWin.destroy()
        if self.ui.strategyCheck:
            self.ui.strategyCheck["state"] = "normal"
        if os.path.exists("buffer.mp3"):
            os.remove("buffer.mp3")
        self.ui.monitorWin = self.engine = None


    def updateScreen(self) -> None:
        """
        Update the monitor screen once the monitor is opened.

        It should never be called by the main thread.
        """
        prev = -1
        n = len(self.converter.imgBook) - 1
        while self.ui.monitorWin and self.engine and self.engine.state != "destroyed":
            match self.engine.state:  # This should actually be laze updated
                case "onPause":
                    self.ui.playBt.config(text="▶")
                case "onPlay":
                    self.ui.playBt.config(text="┃┃")
                case _: ...
            
            if (now := int(self.engine.getPerc() * n)) != prev:
                frame, lrc = self.engine.getCurInfo()
                self.ui.videoPane.config(text=frame)
                self.ui.lrcPane.config(text=lrc)
                prev = now
            self.ui.process.set(self.engine.getPerc())
            if self.ui.monitorWin:
                self.ui.monitorWin.update()

    def updateStatus(self, message: str) -> None:
        """
        Update the status indicator in the console.

        Param
        -----
            - `message`: The info to be displayed in the indicator.
        """
        self.ui.ProcessLb.config(text=message)
        if self.converter.vDir:
            self.ui.videoLb.config(text=f"Video - {self.converter.vDir.split('/')[-1]}", fg="green")
        else:
            self.ui.videoLb.config(text="Video - X", fg="red")
        if self.converter.lDir:
            self.ui.lrcLb.config(text=f"Lyrics - {self.converter.lDir.split('/')[-1]}", fg="green")
        else:
            self.ui.lrcLb.config(text="Lyrics - X", fg="red")
        self.ui.root.update()


if __name__ == "__main__":
    myUI = V2SUI()
    model = V2SController(myUI)
    model.run()