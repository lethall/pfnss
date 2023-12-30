from tkinter import Toplevel, Listbox, ttk, StringVar, E, W


class Configure:
    photo_name : StringVar = None
    photo_description : StringVar = None
    chosen_categories : list = None

    def __init__(self, root : Toplevel, categories : list) -> None:
        def dismiss():
            self.chosen_categories = lb_categories.curselection()
            dlg.grab_release()
            dlg.destroy()

        dlg = Toplevel(root)
        dlg.geometry("+10+50")
        dlg.title("Configure")
        ttk.Label(dlg, text="Name for this photo").grid(column=1, row=1, sticky=E)
        self.photo_name = StringVar(root)
        e_photo_name = ttk.Entry(dlg, width=20, textvariable=self.photo_name)
        e_photo_name.grid(column=2, row=1, sticky=W)
        ttk.Label(dlg, text="Description").grid(column=1, row=2, sticky=E)
        self.photo_description = StringVar(root)
        e_description = ttk.Entry(dlg, width=40, textvariable=self.photo_description)
        e_description.grid(column=2, row=2, columnspan=2, sticky=W)
        ttk.Label(dlg, text="Categories:").grid(column=1, row=3, sticky=W)
        category_list = StringVar(value=categories)
        lb_categories = Listbox(dlg, selectmode="extended", listvariable=category_list, height=3)
        lb_categories.grid(column=1, row=4, columnspan=2)

        ttk.Button(dlg, text="Done", command=dismiss).grid(column=3, row=1)

        dlg.protocol("WM_DELETE_WINDOW", dismiss)
        dlg.transient(root)
        dlg.wait_visibility()
        dlg.grab_set()
        e_photo_name.focus()
        dlg.wait_window()
