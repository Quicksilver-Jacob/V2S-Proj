from tkinter.messagebox import askokcancel
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Radiobutton, StringVar, Tk, Frame, Button, Label, \
                    Checkbutton, Toplevel, Scale, Menu, DoubleVar, IntVar


class V2SUI:
    """
    The GUI for the V2S project.
    """

    def __init__(self) -> None:
        """
        Initialization of the main console
        """
        self.root = Tk()
        self.monitorWin = self.strategyCheck = self.configWin = None
        self.font = "Consolas"
        self.monitorSize = [200, 80]
        self.allowBuffer = IntVar(value=0)
        self.dynamicReso = IntVar(value=1)
        self.pixelSet = IntVar(value=2)
        self.fontScale = DoubleVar(value=1.0)
        self.resolution = DoubleVar(value=1.0)
        self.process = DoubleVar(value=0.0)
        self.videoName = StringVar(value="")
        self.lrcName = StringVar(value="")

        self.root.title("console")
        self.root.geometry("+100+450")

        menubar = Menu(self.root)
        self.systmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="System", menu=self.systmenu)
        self.root.config(menu=menubar)

        div = Frame(self.root)
        div.pack(expand=1, fill="both")
        div1 = Frame(div)
        div1.pack(side="left", expand=1, fill="both")
        self.lrcBt = Button(div1, text="Load New Lyrics")
        self.lrcBt.pack(side="top", expand=1, fill="both")
        self.rawVideoBt = Button(div1, text="Load New Video")
        self.rawVideoBt.pack(side="bottom", expand=1, fill="both")
        div2 = Frame(div)
        div2.pack(side="right", expand=1, fill="both")
        self.videoBt = Button(
            div2,
            text="Load Processed Video",
        )
        self.videoBt.pack(expand=1, fill="both")
        self.monitorBt = Button(self.root, text="Launch Monitor")
        self.monitorBt.pack(expand=1, fill="both")
        infoDiv = Frame(self.root)
        infoDiv.pack(expand=1, fill="both")
        leftInfo = Frame(infoDiv)
        leftInfo.pack(side="left", ipadx="30")
        self.lrcLb = Label(leftInfo, text="Lyrics - X", fg="red")
        self.lrcLb.pack(expand=1, fill="both")
        self.videoLb = Label(leftInfo, text="Video - X", fg="red")
        self.videoLb.pack(expand=1, fill="both")
        rightInfo = Frame(infoDiv)
        rightInfo.pack(side="right", expand=1, fill="both", ipadx="30")
        self.ProcessLb = Label(rightInfo, text="Good to go")
        self.ProcessLb.pack(expand=1, fill="both")

    def showConfig(self) -> None:
        """
        Initialization of the config panel
        """
        self.configWin = Toplevel(self.root)
        self.configWin.geometry("+100+100")
        self.configWin.title("Config")
        div = Frame(self.configWin)
        div.pack(padx=10)
        Radiobutton(
            div,
            text="Pixel Set 1",
            variable=self.pixelSet,
            value=0,
        ).pack()
        Radiobutton(
            div,
            text="Pixel Set 2",
            variable=self.pixelSet,
            value=1,
        ).pack()
        Radiobutton(
            div,
            text="Pixel Set 3",
            variable=self.pixelSet,
            value=2,
        ).pack()
        Checkbutton(
            div,
            text="Allow Buffer",
            variable=self.allowBuffer,
        ).pack()
        self.strategyCheck = Checkbutton(
            div,
            text="Allow dynamic reso change\n(May reduce fps)",
            variable=self.dynamicReso,
            state="disabled" if self.monitorWin else "normal")
        self.strategyCheck.pack()
        Scale(
            div,
            label="Resolution",
            from_=0.1,
            to=2.5,
            resolution=0.05,
            showvalue=1,
            length=150,
            orient="horizontal",
            variable=self.resolution,
        ).pack()
        Scale(
            div,
            label="Screen Scale",
            from_=0.1,
            to=2,
            resolution=0.05,
            showvalue=1,
            length=150,
            orient="horizontal",
            variable=self.fontScale,
        ).pack()

    def showMonitor(self, processReso: float = 1e-6) -> None:
        """
        Initialization of the monitor

        Param
        -----
            - `processReso`: the resolution for the progress bar
        """
        self.monitorWin = Toplevel(self.root, bg="black")
        self.monitorWin.title("Monitor")
        self.monitorWin.geometry("+450+0")
        vpDiv = Frame(self.monitorWin, bg="black")
        vpDiv.pack(padx="40")
        videoDiv = Frame(vpDiv, bg="black", relief="ridge", bd=5)
        videoDiv.pack(side="top", expand=1, fill="both")
        self.videoPane = Label(videoDiv, bg="Black", fg="White", \
                font=[self.font, 1, "bold"])
        self.videoPane.pack(side="left", expand=1, fill="both")
        self.lrcPane = Label(videoDiv, text="", bg="Black", width=2, \
                fg="White", font=[self.font, 15, "bold"])
        self.lrcPane.pack(side="right", expand=1, fill="both")
        controlDiv = Frame(vpDiv, bg="black")
        controlDiv.pack(side="bottom", expand=1, fill="both")
        self.processBar = Scale(
            controlDiv,
            from_=0,
            to=1,
            resolution=processReso,
            showvalue=0,
            orient="horizontal",
            variable=self.process,
            width=10,
            bg="black",
            sliderrelief="flat",
        )
        self.processBar.pack(side="right", expand=1, fill="both", pady="8")
        Btdiv = Frame(controlDiv)
        Btdiv.pack(side="left")
        self.playBt = Button(
            Btdiv,
            text="▶",
            bg="black",
            fg="white",
            justify="center",
            width=7,
        )
        self.playBt.pack(side="left", expand=1, fill="both")
        self.saveBt = Button(
            Btdiv,
            text="Save",
            bg="black",
            fg="white",
            justify="center",
            width=7,
        )
        self.saveBt.pack(side="right", expand=1, fill="both")

    def askSavePath(self, title: str) -> str:
        """
        Pop out a window to ask where the file should be saved

        Param
        -----
            - `title`: The navigator title
        """
        return asksaveasfilename(title=title)

    def askLoadPath(self, title: str) -> str:
        """
        Pop out a window to ask what file should be loaded

        Param
        -----
            - `title`: The navigator title
        """
        return askopenfilename(title=title)

    def okCancel(self, title: str, msg: str) -> str:
        """
        Pop out a window to ask for ok or cancel

        Params
        ------
            - `title`: The windows title
            - `message`: The windows message
        """
        return askokcancel(title=title, message=msg)


if __name__ == "__main__":
    view = V2SUI()
    view.showConfig()
    view.showMonitor()
    view.root.mainloop()