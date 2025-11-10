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
        self.records = []  
        self.filtered_ids = set()  