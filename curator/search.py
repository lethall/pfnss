from tkinter import Toplevel, Frame, Label, Entry, Button, StringVar, IntVar, NW, E, W, NSEW

class Search:
    # start regex with any of ".^\"
    regex_prefix: str = '.^\"'
    file_name_pattern: str = None
    name_pattern: str = None
    descr_pattern: str = None
    cat_pattern: str = None

    id_start: int = 0
    id_end: int = 1
    seq_start: int = 0
    seq_end: int = 1
    
    ts_start: str = None
    ts_end: str = None

    current_row: int = 1

    def dialog(self, root: Toplevel):
        self.dlg = dlg = Toplevel(root)
        dlg.title("Find Photos")
        w, h = 350, 280
        dlg.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 2}")
        dlg.resizable(False, False)

        file_name_var: StringVar = StringVar(dlg, value=self.file_name_pattern)
        name_var: StringVar = StringVar(dlg, value=self.name_pattern)
        descr_var: StringVar = StringVar(dlg, value=self.descr_pattern)
        cat_var: StringVar = StringVar(dlg, value=self.cat_pattern)

        id_start_var: IntVar = IntVar(dlg, value=self.id_start)
        id_end_var: IntVar = IntVar(dlg, value=self.id_end)
        seq_start_var: IntVar = IntVar(dlg, value=self.seq_start)
        seq_end_var: IntVar = IntVar(dlg, value=self.seq_end)
        
        ts_start_var: StringVar = StringVar(dlg, value=self.ts_start)
        ts_end_var: StringVar = StringVar(dlg, value=self.ts_end)

        def int_or_null(var: IntVar):
            try:
                return var.get()
            except:
                return None

        def find(ev = None):
            self.file_name_pattern = file_name_var.get().strip()
            self.name_pattern = name_var.get().strip()
            self.descr_pattern = descr_var.get().strip()
            self.cat_pattern = cat_var.get().strip()
            self.id_start = int_or_null(id_start_var)
            self.id_end = int_or_null(id_end_var)
            self.seq_start = int_or_null(seq_start_var)
            self.seq_end = int_or_null(seq_end_var)
            try:
                self.ts_start = ts_start_var.get().strip()
                self.ts_end = ts_end_var.get().strip()
            except:
                self.ts_start = self.ts_end = None
            dlg.grab_release()
            dlg.destroy()

        def clear(ev = None):
            self.file_name_pattern = None
            self.name_pattern = None
            self.descr_pattern = None
            self.cat_pattern = None
            self.id_start = None
            self.id_end = None
            self.seq_start = None
            self.seq_end = None
            self.ts_start = None
            self.ts_end = None
            dlg.grab_release()
            dlg.destroy()

        def cancel(ev = None):
            dlg.grab_release()
            dlg.destroy()
        
        self.current_row = 1
        fn_entry = self.row("File Name", file_name_var)
        self.row("Name", name_var)
        self.row("Description", descr_var)
        self.row("Categories", cat_var)

        self.range("File ID", id_start_var, id_end_var)
        self.range("Sequence Number", seq_start_var, seq_end_var)
        self.range("When Seen", ts_start_var, ts_end_var, split=True)
        
        btn_panel = Frame(dlg)
        btn_panel.grid(column=1, row=self.current_row, columnspan=3, sticky=E)
        Button(btn_panel, text="Cancel", command=cancel).grid(column=1, row=1)
        Button(btn_panel, text="Clear", command=clear).grid(column=2, row=1)
        Button(btn_panel, text="Find", command=find).grid(column=3, row=1)

        dlg.bind("<Escape>", cancel)
        dlg.bind("<Return>", find)

        dlg.protocol("WM_DELETE_WINDOW", cancel)
        dlg.transient(root)
        dlg.wait_visibility()
        dlg.grab_set()
        fn_entry.focus()
        dlg.wait_window()

    def row(self, label: str, var: StringVar) -> Entry:
        Label(self.dlg, text=label, anchor=W).grid(column=1, row=self.current_row, sticky=W)
        entry = Entry(self.dlg, textvariable=var, width=20)
        entry.grid(column=2, row=self.current_row, sticky=W)
        self.current_row += 1
        return entry

    def range(self, label: str, start_var: IntVar, end_var: IntVar, split=False) -> None:
        Label(self.dlg, text=label).grid(column=1, row=self.current_row, sticky=NSEW)
        frm = Frame(self.dlg)
        frm.grid(column=2, row=self.current_row, sticky=NSEW)
        field_width = 15 if split else 5
        Label(frm, text="From:", anchor=NW).grid(column=1, row=1)
        Entry(frm, textvariable=start_var, width=field_width).grid(column=2, row=1)
        if split:
            Label(frm, text="To:", anchor=NW).grid(column=1, row=2)
            Entry(frm, textvariable=end_var, width=field_width).grid(column=2, row=2)
        else:
            Label(frm, text="To:", anchor=NW).grid(column=3, row=1)
            Entry(frm, textvariable=end_var, width=field_width).grid(column=4, row=1)
        self.current_row += 1


        # file name pattern
        # friendly name pattern
        # description pattern
        # categories
        # all of the above
        # file id
        # sequence number range
        # seen timestamp range
    def compile(self) -> str:
        where_clause = []

        if self.file_name_pattern:
            s = self.file_name_pattern
            if s.startswith(("^", ".", "[")):
                where_clause.append(f"name REGEXP '{s}'")
            else:
                where_clause.append(f"name LIKE '%{s}%'")

        if self.name_pattern:
            s = self.name_pattern
            prefix = "(id in (select file_id from info where info.name"
            if s.startswith(("^", ".", "[")):
                where_clause.append(f"{prefix} REGEXP '{s}'))")
            else:
                where_clause.append(f"{prefix} LIKE '%{s}%'))")

        if self.descr_pattern:
            s = self.descr_pattern
            prefix = "(id in (select file_id from info where info.description"
            if s.startswith(("^", ".", "[")):
                where_clause.append(f"{prefix} REGEXP '{s}'))")
            else:
                where_clause.append(f"{prefix} LIKE '%{s}%'))")

        if self.cat_pattern:
            subselect = [f"(info.categories LIKE '%{part}%')" for part in self.cat_pattern.split(" ")]                
            where_clause.append(f"(id in (select file_id from info where {' AND '.join(subselect)}))")

        if where_clause:
            return "where " + " AND ".join(where_clause)
        return None