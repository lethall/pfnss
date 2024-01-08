from tkinter import Toplevel, Frame, Label, W, E

class Help:
    key_event = None
    frame = None
    current_row = 0

    def __init__(self) -> None:
        self.key = None

    def dialog(self, root : Toplevel, keysym = None) -> None:
        dlg = Toplevel(root)
        dlg.title("Help")
        w, h = 350, 350
        dlg.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 2}")

        def cancel(ev=None):
            self.key_event = ev
            dlg.unbind_all("<Key>")
            dlg.grab_release()
            dlg.destroy()

        dlg.columnconfigure(0, weight=1)
        dlg.rowconfigure(0, weight=1)
        self.frame = frame = Frame(dlg)
        frame.grid(column=0, row=0)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=3)
            
        current_row = 1
        Label(frame, text=f"You pressed {keysym}").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        Label(frame, text=" ").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        Label(frame, text="Press any of these keys instead:").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        Label(frame, text=" ").grid(column=1, row=current_row, columnspan=2, sticky=W)

        self.current_row = current_row
        self.keydef("s", "marks photo to be saved")
        self.keydef("d", "marks photo to be deleted")
        self.keydef("r", "resets mark from photo")
        self.keydef("i", "info for photo")
        self.keydef("f", "find photos")
        self.keydef("/", "clear search")
        self.keydef("SPACE or ENTER", "pause/resume on current photo")
        self.keydef("n or Right or Down", "Skip to next photo")
        self.keydef("p or Left or Up", "Skip to prior photo")
        self.keydef("q or Escape", "quit")

        dlg.protocol("WM_DELETE_WINDOW", cancel)
        dlg.transient(root)
        dlg.bind_all("<Key>", cancel)
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.wait_window()
    
    def keydef(self, key_label, key_desc) -> None:
        self.current_row  += 1
        Label(self.frame, text=key_label).grid(column=1, row=self.current_row, padx=5, sticky=E)
        Label(self.frame, text=f"- {key_desc}").grid(column=2, row=self.current_row, sticky=W)
