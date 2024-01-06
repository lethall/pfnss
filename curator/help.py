from tkinter import Toplevel, ttk, W, E, RIDGE

class Help:
    key_event = None
    frame = None
    current_row = 0

    def __init__(self) -> None:
        self.key = None

    def dialog(self, root : Toplevel, keysym = None) -> None:
        dlg = Toplevel(root)
        dlg.geometry("+200+200")
        dlg.title("Help")

        def cancel(ev=None):
            self.key_event = ev
            dlg.unbind_all("<Key>")
            dlg.grab_release()
            dlg.destroy()

        self.frame = frame = ttk.Frame(dlg)
        frame.grid(column=1, row=1)
            
        current_row = 1
        ttk.Label(frame, text=f"You pressed {keysym}").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        ttk.Label(frame, text=" ").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        ttk.Label(frame, text="Press any of these keys instead:").grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        ttk.Label(frame, text=" ").grid(column=1, row=current_row, columnspan=2, sticky=W)

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
        ttk.Label(self.frame, text=key_label).grid(column=1, row=self.current_row, padx=5, sticky=E)
        ttk.Label(self.frame, text=f"- {key_desc}").grid(column=2, row=self.current_row, sticky=W)
