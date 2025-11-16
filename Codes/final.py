import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, re, uuid

DATA_FILE = "students.csv"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

FIELDS = [
    ("Name", "name"),
    ("Age", "age"),
    ("Class", "cls"),
    ("Section", "section"),


    ("Roll No", "roll"),
    ("Gender", "gender"),
    ("Phone", "phone"),
    ("Email", "email"),
]

GENDER_OPTIONS = ["Male", "Female", "Other", "Prefer not to say"]
SUBJECT_OPTIONS = ["Maths", "Science", "English", "Social Studies", "Computer", "Art", "PE","Drama/Dance","Other Rotary","History","Extra-Curricular Activities"]

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Info Form")
        self.root.geometry("980x560")
        self.root.minsize(900, 520)

        # ---- Top Title ----
        ttk.Label(root, text="Student Information Manager", font=("Arial", 18, "bold")).pack(pady=10)

        # ---- Main layout frames ----
        main = ttk.Frame(root, padding=10)
        main.pack(fill="both", expand=True)

        form_frame = ttk.LabelFrame(main, text="Student Form", padding=12)
        form_frame.pack(side="left", fill="y")

        right_frame = ttk.Frame(main)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10,0))

        # ---- Form vars ----
        self.vars = {key: tk.StringVar() for _, key in FIELDS}
        self.address_text = tk.Text(form_frame, width=34, height=4)
        self.subjects_list = tk.Listbox(form_frame, selectmode="multiple", height=6, exportselection=False)

        # ---- Form grid ----
        row = 0
        for label, key in FIELDS:
            ttk.Label(form_frame, text=label + ":").grid(row=row, column=0, sticky="w", pady=4, padx=(2,6))
            if key == "gender":
                cb = ttk.Combobox(form_frame, textvariable=self.vars[key], values=GENDER_OPTIONS, state="readonly", width=31)
                cb.grid(row=row, column=1, pady=4)
            else:
                ttk.Entry(form_frame, textvariable=self.vars[key], width=34).grid(row=row, column=1, pady=4)
            row += 1

        ttk.Label(form_frame, text="Address:").grid(row=row, column=0, sticky="nw", pady=(6,2), padx=(2,6))
        self.address_text.grid(row=row, column=1, pady=(6,2))
        row += 1

        ttk.Label(form_frame, text="Subjects:").grid(row=row, column=0, sticky="nw", pady=(6,2), padx=(2,6))
        for s in SUBJECT_OPTIONS:
            self.subjects_list.insert(tk.END, s)
        self.subjects_list.grid(row=row, column=1, pady=(6,2))
        row += 1

        # ---- Buttons ----
        btns = ttk.Frame(form_frame)
        btns.grid(row=row, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Add", command=self.add_record).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Update", command=self.update_record).grid(row=0, column=1, padx=4)
        ttk.Button(btns, text="Delete", command=self.delete_record).grid(row=0, column=2, padx=4)
        ttk.Button(btns, text="Clear Form", command=self.clear_form).grid(row=0, column=3, padx=4)
        ttk.Button(btns, text="Export CSV", command=self.export_csv).grid(row=0, column=4, padx=4)

        # ---- Search bar ----
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill="x", pady=(0,8))
        self.search_var = tk.StringVar()
        ttk.Label(search_frame, text="Search:").pack(side="left")
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(search_frame, text="Go", command=self.apply_search).pack(side="left")
        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side="left", padx=(6,0))

        # ---- Table (Treeview) ----
        columns = ["id", "name", "age", "cls", "section", "roll", "gender", "phone", "email", "subjects", "address"]
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=16)
        headings = {
            "id": "ID",
            "name": "Name",
            "age": "Age",
            "cls": "Class",
            "section": "Section",
            "roll": "Roll",
            "gender": "Gender",
            "phone": "Phone",
            "email": "Email",
            "subjects": "Subjects",
            "address": "Address",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=80 if col not in ("name","email","subjects","address") else 140, anchor="w")
        self.tree.column("id", width=60)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # ---- Status bar ----
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(root, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(4,0), padx=10)

        # ---- Data store ----
        self.records = []  # list of dicts
        self.filtered_ids = set()  # to maintain current filter

        self.load_csv()
        self.refresh_table()

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.clear_form())
        self.root.bind("<Control-s>", lambda e: self.add_record())
        self.root.bind("<Delete>", lambda e: self.delete_record())

    # ----------------- Helpers -----------------
    def get_form_data(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        data["address"] = self.address_text.get("1.0", "end").strip()
        sel = [self.subjects_list.get(i) for i in self.subjects_list.curselection()]
        data["subjects"] = ", ".join(sel)
        return data

    def set_form_data(self, rec):
        for k in self.vars:
            self.vars[k].set(rec.get(k, ""))
        self.address_text.delete("1.0", "end")
        self.address_text.insert("1.0", rec.get("address", ""))
        # subjects
        self.subjects_list.selection_clear(0, tk.END)
        have = set((rec.get("subjects") or "").split(", "))
        for i, s in enumerate(SUBJECT_OPTIONS):
            if s in have:
                self.subjects_list.selection_set(i)

    def clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.address_text.delete("1.0", "end")
        self.subjects_list.selection_clear(0, tk.END)
        self.tree.selection_remove(self.tree.selection())
        self.status("Form cleared.")

    def status(self, msg):
        self.status_var.set(msg)

    def validate(self, data):
        # Required fields
        required = ["name", "age", "cls", "roll"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            messagebox.showwarning("Missing Data", f"Please fill: {', '.join(missing)}")
            return False
        # Age numeric
        if not data["age"].isdigit() or int(data["age"]) <= 0:
            messagebox.showwarning("Invalid Age", "Age must be a positive integer.")
            return False
        # Phone (optional): digits 7–15
        phone = data.get("phone", "")
        if phone and (not phone.isdigit() or not (7 <= len(phone) <= 15)):
            messagebox.showwarning("Invalid Phone", "Phone must be 7–15 digits (numbers only).")
            return False
        # Email (optional)
        email = data.get("email", "")
        if email and not EMAIL_RE.match(email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return False
        return True

    # ----------------- CSV persistence -----------------
    def load_csv(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.records.append(dict(row))
        self.status(f"Loaded {len(self.records)} record(s) from {DATA_FILE}.")

    def write_csv(self):
        fieldnames = ["id","name","age","cls","section","roll","gender","phone","email","subjects","address"]
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in self.records:
                w.writerow({k: r.get(k, "") for k in fieldnames})

    # ----------------- Table ops -----------------
    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        showing = 0
        for rec in self.records:
            if self.filtered_ids and rec["id"] not in self.filtered_ids:
                continue
            self.tree.insert("", "end", iid=rec["id"], values=(
                rec.get("id",""),
                rec.get("name",""),
                rec.get("age",""),
                rec.get("cls",""),
                rec.get("section",""),
                rec.get("roll",""),
                rec.get("gender",""),
                rec.get("phone",""),
                rec.get("email",""),
                rec.get("subjects",""),
                rec.get("address",""),
            ))
            showing += 1
        self.status(f"Showing {showing} record(s).")

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel:
            return
        rid = sel[0]
        rec = next((r for r in self.records if r["id"] == rid), None)
        if rec:
            self.set_form_data(rec)
            self.status(f"Selected ID {rid}")

    # ----------------- CRUD actions -----------------
    def add_record(self):
        data = self.get_form_data()
        if not self.validate(data):
            return
        # prevent duplicate roll in same class/section
        for r in self.records:
            if r["cls"] == data["cls"] and r.get("section","") == data.get("section","") and r["roll"] == data["roll"]:
                if not messagebox.askyesno("Duplicate Roll", "Same Class/Section & Roll exists. Add anyway?"):
                    return
                break
        rec = {"id": str(uuid.uuid4())[:8], **data}
        self.records.append(rec)
        self.write_csv()
        self.refresh_table()
        self.clear_form()
        self.status("Record added.")

    def update_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a record in the table to update.")
            return
        rid = sel[0]
        data = self.get_form_data()
        if not self.validate(data):
            return
        for r in self.records:
            if r["id"] == rid:
                r.update(data)
                break
        self.write_csv()
        self.refresh_table()
        self.status(f"Record {rid} updated.")

    def delete_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a record to delete.")
            return
        rid = sel[0]
        if not messagebox.askyesno("Confirm Delete", f"Delete record {rid}?"):
            return
        self.records = [r for r in self.records if r["id"] != rid]
        self.write_csv()
        self.refresh_table()
        self.clear_form()
        self.status(f"Record {rid} deleted.")

    # ----------------- Search/Export -----------------
    def apply_search(self):
        q = self.search_var.get().strip().lower()
        self.filtered_ids.clear()
        if not q:
            self.refresh_table()
            return
        for r in self.records:
            hay = " ".join([r.get(k, "") for k in ["name","cls","section","roll","gender","phone","email","subjects","address"]]).lower()
            if q in hay:
                self.filtered_ids.add(r["id"])
        self.refresh_table()

    def reset_search(self):
        self.search_var.set("")
        self.filtered_ids.clear()
        self.refresh_table()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")], initialfile="students_export.csv")
        if not path:
            return
        # Export what is currently visible
        visible = [r for r in self.records if not self.filtered_ids or r["id"] in self.filtered_ids]
        fieldnames = ["id","name","age","cls","section","roll","gender","phone","email","subjects","address"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for r in visible:
                    w.writerow({k: r.get(k, "") for k in fieldnames})
            messagebox.showinfo("Exported", f"Saved {len(visible)} record(s) to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    # Nice default theme on Windows/Mac; on *nix fallback to clam
    try:
        style = ttk.Style()
        if style.theme_use() not in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = StudentApp(root)
    root.mainloop()