from tkinter import Toplevel, Listbox, Scrollbar, ttk, StringVar, N, S, E, W, VERTICAL

from . import CATEGORIES


class PhotoInfo:
    file_name : str = None
    photo_name : str = None
    description : str = None
    categories : str = None
    chosen_categories : list = None

    def __init__(self, values : tuple):
        self.file_name, self.photo_name, self.description, self.categories = values
        self.chosen_categories = self.categories.split(", ") if self.categories else None
    
    def dialog(self, root : Toplevel) -> None:
        dlg = Toplevel(root)
        dlg.geometry("+10+50")
        dlg.title("Photo Information")

        def save():
            self.chosen_categories = lb_categories.curselection()
            self.categories = ", ".join([CATEGORIES[selected] for selected in self.chosen_categories])
            self.photo_name = name.get()
            self.description = description.get()
            dlg.grab_release()
            dlg.destroy()

        def cancel():
            dlg.grab_release()
            dlg.destroy()

        current_row = 1
        ttk.Label(dlg, text="Name:").grid(column=1, row=current_row, sticky=W)
        ttk.Label(dlg, text="Categories (CTRL+click multiple):").grid(column=2, row=current_row, sticky=W)

        current_row += 1
        name = StringVar(root, value=self.photo_name)
        e_photo_name = ttk.Entry(dlg, width=20, textvariable=name)
        e_photo_name.grid(column=1, row=current_row, sticky=[N, W])

        category_list = StringVar(value=CATEGORIES)
        lb_categories = Listbox(dlg, selectmode="extended", listvariable=category_list, height=4)
        if self.chosen_categories:
            for ii in [CATEGORIES.index(cat) for cat in self.chosen_categories]:
                lb_categories.selection_set(ii)
        lb_categories.grid(column=2, row=current_row, rowspan=2, sticky=[N, S, E, W])
        sb = Scrollbar(dlg, orient=VERTICAL, command=lb_categories.yview)
        lb_categories.configure(yscrollcommand=sb.set)
        sb.grid(column=3, row=2, rowspan=2, sticky=[N, S])

        current_row += 1
        ttk.Label(dlg, text="Description:").grid(column=1, row=current_row, sticky=[S, W])

        current_row += 1
        description = StringVar(root, value=self.description)
        e_description = ttk.Entry(dlg, width=40, textvariable=description)
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
