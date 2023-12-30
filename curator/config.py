from tkinter import Toplevel, Listbox, ttk, StringVar, N, S, E, W


class Configure:
    photo_name : str = None
    photo_description : str = None
    chosen_categories : list = None

    def __init__(self, root : Toplevel, categories : list) -> None:
        def dismiss():
            self.chosen_categories = lb_categories.curselection()
            self.photo_name = photo_name.get()
            self.photo_description = photo_description.get()
            dlg.grab_release()
            dlg.destroy()

        dlg = Toplevel(root)
        dlg.geometry("+10+50")
        dlg.title("Configure")

        current_row = 1
        ttk.Label(dlg, text="Photo Name:").grid(column=1, row=current_row, sticky=W)
        ttk.Label(dlg, text="Categories:").grid(column=2, row=current_row, sticky=W)

        current_row += 1
        photo_name = StringVar(root)
        e_photo_name = ttk.Entry(dlg, width=20, textvariable=photo_name)
        e_photo_name.grid(column=1, row=current_row, sticky=[N, W])
        category_list = StringVar(value=categories)
        lb_categories = Listbox(dlg, selectmode="extended", listvariable=category_list, height=5)
        lb_categories.grid(column=2, row=current_row, rowspan=2, sticky=[N, S, E, W])

        current_row += 1
        ttk.Label(dlg, text="Description").grid(column=1, row=current_row, sticky=[S, W])

        current_row += 1
        photo_description = StringVar(root)
        e_description = ttk.Entry(dlg, width=40, textvariable=photo_description)
        e_description.grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        ttk.Button(dlg, text="Done", command=dismiss).grid(column=2, row=current_row, sticky=[S, E])

        dlg.protocol("WM_DELETE_WINDOW", dismiss)
        dlg.transient(root)
        dlg.wait_visibility()
        dlg.grab_set()
        e_photo_name.focus()
        dlg.wait_window()
