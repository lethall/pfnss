from tkinter import Toplevel, ttk

def config_dialog(root):
    def dismiss ():
        dlg.grab_release()
        dlg.destroy()

    dlg = Toplevel(root)
    e = ttk.Entry(dlg)
    e.grid()   # something to interact with
    e.focus()
    ttk.Button(dlg, text="Done", command=dismiss).grid()
    dlg.protocol("WM_DELETE_WINDOW", dismiss) # intercept close button
    dlg.transient(root)   # dialog window is related to main
    dlg.wait_visibility() # can't grab until window appears, so we wait
    dlg.grab_set()        # ensure all input goes to our window
    dlg.wait_window()     # block until window is destroyed
