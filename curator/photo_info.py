from tkinter import Toplevel, Listbox, Scrollbar, ttk, StringVar, N, S, E, W, VERTICAL

from . import CATEGORIES


class PhotoInfo:
    photo_name : str = None
    photo_description : str = None
    chosen_categories : list = None

    def __init__(self, root : Toplevel) -> None:
        def save():
            self.chosen_categories = lb_categories.curselection()
            self.photo_name = photo_name.get()
            self.photo_description = photo_description.get()
            dlg.grab_release()
            dlg.destroy()

        def cancel():
            dlg.grab_release()
            dlg.destroy()

        dlg = Toplevel(root)
        dlg.geometry("+10+50")
        dlg.title("Photo Information")

        current_row = 1
        ttk.Label(dlg, text="Name:").grid(column=1, row=current_row, sticky=W)
        ttk.Label(dlg, text="Categories:").grid(column=2, row=current_row, sticky=W)

        current_row += 1
        photo_name = StringVar(root)
        e_photo_name = ttk.Entry(dlg, width=20, textvariable=photo_name)
        e_photo_name.grid(column=1, row=current_row, sticky=[N, W])
        category_list = StringVar(value=CATEGORIES)
        lb_categories = Listbox(dlg, selectmode="extended", listvariable=category_list, height=4)
        lb_categories.grid(column=2, row=current_row, rowspan=2, sticky=[N, S, E, W])
        sb = Scrollbar(dlg, orient=VERTICAL, command=lb_categories.yview)
        lb_categories.configure(yscrollcommand=sb.set)
        sb.grid(column=3, row=2, rowspan=2, sticky=[N, S])

        current_row += 1
        ttk.Label(dlg, text="Description:").grid(column=1, row=current_row, sticky=[S, W])

        current_row += 1
        photo_description = StringVar(root)
        e_description = ttk.Entry(dlg, width=40, textvariable=photo_description)
        e_description.grid(column=1, row=current_row, columnspan=2, sticky=W)

        current_row += 1
        ttk.Button(dlg, text="Cancel", command=cancel).grid(column=1, row=current_row, sticky=[S, W])
        ttk.Button(dlg, text="Save", command=save).grid(column=2, row=current_row, sticky=[S, E])

        dlg.protocol("WM_DELETE_WINDOW", cancel)
        dlg.transient(root)
        dlg.wait_visibility()
        dlg.grab_set()
        e_photo_name.focus()
        dlg.wait_window()
