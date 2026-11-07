import csv
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

# ------------------------------------------------------------------
# GLOBAL DATA STORE
# ------------------------------------------------------------------
students = []          # list of student dictionaries (the "database")
next_student_id = 1    # simple auto-increment counter for unique IDs


# ------------------------------------------------------------------
# CORE LOGIC FUNCTIONS
# (kept separate from GUI code so they can be explained/tested
#  independently during the viva)
# ------------------------------------------------------------------

def calculate_grade(marks):
    """Takes marks (0-100) and returns the grade as per grading rules."""
    if marks >= 90:
        return "A+"
    elif marks >= 80:
        return "A"
    elif marks >= 70:
        return "B"
    elif marks >= 60:
        return "C"
    elif marks >= 50:
        return "D"
    else:
        return "F"


def check_result(marks):
    """Returns PASS if marks >= 50, otherwise FAIL."""
    return "PASS" if marks >= 50 else "FAIL"


def marks_needed(marks):
    """
    Calculates how many more marks a student needs to reach the next
    grade boundary, or to simply pass if they are currently failing.
    """
    boundaries = [
        (50, "D (Pass)"),
        (60, "C"),
        (70, "B"),
        (80, "A"),
        (90, "A+"),
    ]

    if marks < 50:
        needed = 50 - marks
        return f"You need {needed} more marks to pass."

    if marks >= 90:
        return "You already have the highest grade (A+)."

    for boundary_marks, grade_name in boundaries:
        if marks < boundary_marks:
            needed = boundary_marks - marks
            return f"You need {needed} more marks to reach Grade {grade_name}."

    return "No further grade improvement possible."


def find_topper():
    """Returns the student dictionary with the highest marks, or None."""
    if not students:
        return None
    return max(students, key=lambda s: s["marks"])


def class_statistics():
    """Returns a dictionary of overall class statistics, or None if empty."""
    if not students:
        return None

    total_students = len(students)
    all_marks = [s["marks"] for s in students]

    average_marks = sum(all_marks) / total_students
    highest_marks = max(all_marks)
    lowest_marks = min(all_marks)

    passed_count = len([s for s in students if s["result"] == "PASS"])
    failed_count = total_students - passed_count

    return {
        "total_students": total_students,
        "average": round(average_marks, 2),
        "highest": highest_marks,
        "lowest": lowest_marks,
        "passed": passed_count,
        "failed": failed_count,
    }


def grade_distribution():
    """
    Returns a dictionary counting how many students fall into each
    grade category. Used to draw the Grade Distribution bar chart.
    """
    counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for s in students:
        counts[s["grade"]] += 1
    return counts


def display_result(student):
    """Formats a single student's details into a readable string."""
    return (
        f"Name   : {student['name']}\n"
        f"Marks  : {student['marks']}\n"
        f"Grade  : {student['grade']}\n"
        f"Result : {student['result']}"
    )


def get_ranked_students():
    """
    Returns a NEW list of students sorted by marks (highest first),
    with a 'rank' key added to each entry. Students with equal marks
    receive the same rank (standard competition ranking).
    Does not modify the original `students` list order.
    """
    sorted_list = sorted(students, key=lambda s: s["marks"], reverse=True)
    ranked = []
    current_rank = 0
    previous_marks = None
    for position, student in enumerate(sorted_list, start=1):
        if student["marks"] != previous_marks:
            current_rank = position
            previous_marks = student["marks"]
        entry = dict(student)
        entry["rank"] = current_rank
        ranked.append(entry)
    return ranked


# ------------------------------------------------------------------
# GUI APPLICATION CLASS
# ------------------------------------------------------------------

class StudentResultApp:
    """Main GUI application class - builds the layout and wires up events."""

    # ---- Color palette (professional academic dashboard style) ----
    COLOR_BG = "#f4f6fa"
    COLOR_NAVY = "#1b2a4a"
    COLOR_NAVY_LIGHT = "#2f4577"
    COLOR_CARD = "#ffffff"
    COLOR_TEXT = "#1b2a4a"
    COLOR_MUTED = "#6b7280"
    COLOR_PASS = "#1e8e5a"
    COLOR_FAIL = "#c0392b"
    COLOR_ACCENT = "#3b5bdb"
    COLOR_GOLD = "#fff3cd"

    GRADE_COLORS = {
        "A+": "#1e8e5a",
        "A": "#3b5bdb",
        "B": "#2f7fbf",
        "C": "#d99a2b",
        "D": "#e07b39",
        "F": "#c0392b",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Student Result Management System")
        self.root.geometry("1250x720")
        self.root.configure(bg=self.COLOR_BG)
        self.root.minsize(1080, 650)

        # Editing state: None means "add mode", otherwise holds the id
        # of the student currently being edited.
        self.editing_id = None

        # Sorting state for the table
        self.sort_column = None
        self.sort_reverse = False

        self._build_styles()
        self._build_menu_bar()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        self.set_status("Ready. Add your first student to get started.")

    # ----------------------------------------------------------------
    # STYLE SETUP
    # ----------------------------------------------------------------
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Custom.Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.COLOR_TEXT,
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=self.COLOR_NAVY,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Custom.Treeview.Heading", background=[("active", self.COLOR_NAVY_LIGHT)])
        style.map("Custom.Treeview", background=[("selected", "#dbe4ff")])

        style.configure("TNotebook", background=self.COLOR_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab", font=("Segoe UI", 9, "bold"),
            padding=(12, 8), background="#e5e9f2", foreground=self.COLOR_TEXT,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLOR_CARD)],
            foreground=[("selected", self.COLOR_NAVY)],
        )

    # ----------------------------------------------------------------
    # MENU BAR
    # ----------------------------------------------------------------
    def _build_menu_bar(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save Records to CSV...", command=self.handle_save_csv)
        file_menu.add_command(label="Load Records from CSV...", command=self.handle_load_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Export Full Report (.txt)...", command=self.handle_export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Edit Selected Student", command=self.handle_edit_selected)
        edit_menu.add_command(label="Delete Selected Student", command=self.handle_delete_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear All Records", command=self.handle_clear_all)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Student Result Management System\n\n"
            "A Python + Tkinter college mini-project for entering student "
            "marks and analyzing class performance.\n\n"
            "Grading: A+ (90-100), A (80-89), B (70-79), C (60-69), "
            "D (50-59), F (below 50). Pass mark is 50.",
        )

    # ----------------------------------------------------------------
    # HEADER SECTION
    # ----------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=self.COLOR_NAVY, height=90)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header, text="🎓 STUDENT RESULT MANAGEMENT SYSTEM",
            font=("Segoe UI", 20, "bold"), bg=self.COLOR_NAVY, fg="white",
        )
        title.pack(pady=(14, 0))

        subtitle = tk.Label(
            header, text="Student Grade & Performance Analyzer",
            font=("Segoe UI", 11), bg=self.COLOR_NAVY, fg="#c7d1ef",
        )
        subtitle.pack()

    # ----------------------------------------------------------------
    # STATUS BAR
    # ----------------------------------------------------------------
    def _build_status_bar(self):
        self.status_bar = tk.Label(
            self.root, text="", font=("Segoe UI", 9), bg="#e5e9f2",
            fg=self.COLOR_MUTED, anchor="w", padx=14, pady=5,
        )
        self.status_bar.pack(side="bottom", fill="x")

    def set_status(self, message):
        """Updates the status bar text with a live record count."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.config(
            text=f"Total Students: {len(students)}   |   {message}   |   {timestamp}"
        )

    # ----------------------------------------------------------------
    # MAIN LAYOUT (Left | Center | Right)
    # ----------------------------------------------------------------
    def _build_main_layout(self):
        container = tk.Frame(self.root, bg=self.COLOR_BG)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=0)
        container.rowconfigure(0, weight=1)

        self._build_left_panel(container)
        self._build_center_panel(container)
        self._build_right_panel(container)

    # ----------------------------------------------------------------
    # LEFT PANEL: Add / Edit Student Form
    # ----------------------------------------------------------------
    def _build_left_panel(self, parent):
        card = tk.Frame(parent, bg=self.COLOR_CARD, bd=0, highlightthickness=1,
                         highlightbackground="#e2e6ef")
        card.grid(row=0, column=0, sticky="nsw", padx=(0, 12))

        inner = tk.Frame(card, bg=self.COLOR_CARD)
        inner.pack(fill="both", padx=18, pady=18)

        self.form_heading = tk.Label(
            inner, text="➕ Add Student", font=("Segoe UI", 13, "bold"),
            bg=self.COLOR_CARD, fg=self.COLOR_NAVY,
        )
        self.form_heading.pack(anchor="w", pady=(0, 12))

        tk.Label(inner, text="Student Name", font=("Segoe UI", 10),
                 bg=self.COLOR_CARD, fg=self.COLOR_MUTED).pack(anchor="w")
        self.name_entry = tk.Entry(inner, font=("Segoe UI", 11), width=24, relief="solid", bd=1)
        self.name_entry.pack(pady=(2, 12), ipady=4)

        tk.Label(inner, text="Marks (0-100)", font=("Segoe UI", 10),
                 bg=self.COLOR_CARD, fg=self.COLOR_MUTED).pack(anchor="w")
        self.marks_entry = tk.Entry(inner, font=("Segoe UI", 11), width=24, relief="solid", bd=1)
        self.marks_entry.pack(pady=(2, 6), ipady=4)

        # Live preview of grade/result as marks are typed (nice usability touch)
        self.live_preview_label = tk.Label(
            inner, text="", font=("Segoe UI", 9, "italic"),
            bg=self.COLOR_CARD, fg=self.COLOR_MUTED,
        )
        self.live_preview_label.pack(anchor="w", pady=(0, 10))
        self.marks_entry.bind("<KeyRelease>", self.update_live_preview)

        # Enter key submits the form (quick data entry)
        self.name_entry.bind("<Return>", lambda e: self.handle_submit_form())
        self.marks_entry.bind("<Return>", lambda e: self.handle_submit_form())

        # Primary submit button - text changes between Add / Update
        self.submit_btn = tk.Button(
            inner, text="Add Student", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_ACCENT, fg="white", activebackground=self.COLOR_NAVY_LIGHT,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_submit_form,
        )
        self.submit_btn.pack(fill="x", ipady=8, pady=(0, 8))

        # Cancel edit button (only meaningful while editing)
        self.cancel_edit_btn = tk.Button(
            inner, text="Cancel Edit", font=("Segoe UI", 10, "bold"),
            bg="#fde2e2", fg=self.COLOR_FAIL, activebackground="#f8c9c9",
            relief="flat", cursor="hand2", command=self.handle_cancel_edit,
        )
        # not packed initially - only shown while editing

        clear_btn = tk.Button(
            inner, text="Clear Form", font=("Segoe UI", 10, "bold"),
            bg="#e5e7eb", fg=self.COLOR_TEXT, activebackground="#d1d5db",
            relief="flat", cursor="hand2", command=self.handle_clear_form,
        )
        clear_btn.pack(fill="x", ipady=8, pady=(0, 4))

        tk.Frame(inner, bg="#e2e6ef", height=1).pack(fill="x", pady=16)

        tk.Label(inner, text="🛠️ Record Actions", font=("Segoe UI", 13, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 10))

        edit_sel_btn = tk.Button(
            inner, text="Edit Selected", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_NAVY, fg="white", activebackground=self.COLOR_NAVY_LIGHT,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_edit_selected,
        )
        edit_sel_btn.pack(fill="x", ipady=8, pady=4)

        delete_sel_btn = tk.Button(
            inner, text="Delete Selected", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_FAIL, fg="white", activebackground="#a93226",
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_delete_selected,
        )
        delete_sel_btn.pack(fill="x", ipady=8, pady=4)

        tk.Frame(inner, bg="#e2e6ef", height=1).pack(fill="x", pady=16)

        tk.Label(inner, text="📊 Quick Actions", font=("Segoe UI", 13, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 10))

        stats_btn = tk.Button(
            inner, text="Refresh Statistics", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_NAVY, fg="white", activebackground=self.COLOR_NAVY_LIGHT,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_view_statistics,
        )
        stats_btn.pack(fill="x", ipady=8, pady=4)

        topper_btn = tk.Button(
            inner, text="Find Class Topper", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_NAVY, fg="white", activebackground=self.COLOR_NAVY_LIGHT,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_find_topper,
        )
        topper_btn.pack(fill="x", ipady=8, pady=4)

    def update_live_preview(self, event=None):
        """Shows a live grade/result preview as the user types marks."""
        text = self.marks_entry.get().strip()
        if text == "":
            self.live_preview_label.config(text="")
            return
        try:
            marks = float(text)
            if 0 <= marks <= 100:
                grade = calculate_grade(marks)
                result = check_result(marks)
                color = self.COLOR_PASS if result == "PASS" else self.COLOR_FAIL
                self.live_preview_label.config(
                    text=f"Preview -> Grade: {grade}   Result: {result}", fg=color
                )
            else:
                self.live_preview_label.config(text="Marks must be 0-100", fg=self.COLOR_FAIL)
        except ValueError:
            self.live_preview_label.config(text="Marks must be numeric", fg=self.COLOR_FAIL)

    # ----------------------------------------------------------------
    # CENTER PANEL: Search + Student Table
    # ----------------------------------------------------------------
    def _build_center_panel(self, parent):
        card = tk.Frame(parent, bg=self.COLOR_CARD, bd=0, highlightthickness=1,
                         highlightbackground="#e2e6ef")
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 12))

        inner = tk.Frame(card, bg=self.COLOR_CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=18)

        top_row = tk.Frame(inner, bg=self.COLOR_CARD)
        top_row.pack(fill="x", pady=(0, 12))

        tk.Label(top_row, text="📋 Student Records", font=("Segoe UI", 13, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(side="left")

        search_frame = tk.Frame(top_row, bg=self.COLOR_CARD)
        search_frame.pack(side="right")

        tk.Label(search_frame, text="Search:", font=("Segoe UI", 10),
                 bg=self.COLOR_CARD, fg=self.COLOR_MUTED).pack(side="left")
        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 10), width=20,
                                      relief="solid", bd=1)
        self.search_entry.pack(side="left", ipady=3, padx=(4, 0))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        table_frame = tk.Frame(inner, bg=self.COLOR_CARD)
        table_frame.pack(fill="both", expand=True)

        columns = ("rank", "name", "marks", "grade", "result")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Custom.Treeview", height=16, selectmode="browse",
        )

        headings = {
            "rank": "Rank", "name": "Name", "marks": "Marks",
            "grade": "Grade", "result": "Result",
        }
        for col, text in headings.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.handle_sort_column(c))

        self.tree.column("rank", width=60, anchor="center")
        self.tree.column("name", width=190, anchor="w")
        self.tree.column("marks", width=80, anchor="center")
        self.tree.column("grade", width=80, anchor="center")
        self.tree.column("result", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("pass_row", foreground=self.COLOR_PASS)
        self.tree.tag_configure("fail_row", foreground=self.COLOR_FAIL)
        self.tree.tag_configure("topper_row", background=self.COLOR_GOLD)

        # Double-click a row to edit it quickly
        self.tree.bind("<Double-1>", lambda e: self.handle_edit_selected())
        # Delete key removes the selected row
        self.tree.bind("<Delete>", lambda e: self.handle_delete_selected())

        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.handle_edit_selected)
        self.context_menu.add_command(label="Delete", command=self.handle_delete_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        hint = tk.Label(
            inner, text="Tip: click a column header to sort - double-click a row to edit - "
                        "select a row and press Delete to remove it",
            font=("Segoe UI", 8, "italic"), bg=self.COLOR_CARD, fg=self.COLOR_MUTED,
        )
        hint.pack(anchor="w", pady=(8, 0))

    def show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.context_menu.post(event.x_root, event.y_root)

    def handle_sort_column(self, column):
        """Sorts the table by the clicked column (toggles ascending/descending)."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_table()

    # ----------------------------------------------------------------
    # RIGHT PANEL: Tabs for Overview / Distribution / Calculator
    # ----------------------------------------------------------------
    def _build_right_panel(self, parent):
        card = tk.Frame(parent, bg=self.COLOR_CARD, bd=0, highlightthickness=1,
                         highlightbackground="#e2e6ef")
        card.grid(row=0, column=2, sticky="nse")

        inner = tk.Frame(card, bg=self.COLOR_CARD, width=320)
        inner.pack(fill="both", expand=True, padx=14, pady=14)
        inner.pack_propagate(False)

        notebook = ttk.Notebook(inner)
        notebook.pack(fill="both", expand=True)

        overview_tab = tk.Frame(notebook, bg=self.COLOR_CARD)
        distribution_tab = tk.Frame(notebook, bg=self.COLOR_CARD)
        calculator_tab = tk.Frame(notebook, bg=self.COLOR_CARD)

        notebook.add(overview_tab, text="Overview")
        notebook.add(distribution_tab, text="Distribution")
        notebook.add(calculator_tab, text="Calculator")

        self._build_overview_tab(overview_tab)
        self._build_distribution_tab(distribution_tab)
        self._build_calculator_tab(calculator_tab)

    def _build_overview_tab(self, parent):
        pad = tk.Frame(parent, bg=self.COLOR_CARD)
        pad.pack(fill="both", expand=True, padx=6, pady=12)

        tk.Label(pad, text="🏆 Class Topper", font=("Segoe UI", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 8))

        self.topper_card = tk.Frame(pad, bg="#fff8e6", highlightthickness=1,
                                     highlightbackground="#f0d787")
        self.topper_card.pack(fill="x", pady=(0, 18))
        self.topper_label = tk.Label(
            self.topper_card, text="No students added yet.",
            font=("Segoe UI", 10), bg="#fff8e6", fg=self.COLOR_TEXT,
            justify="left", anchor="w", padx=12, pady=10,
        )
        self.topper_label.pack(fill="x")

        tk.Label(pad, text="📈 Class Statistics", font=("Segoe UI", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 8))

        self.stats_card = tk.Frame(pad, bg="#eef2ff", highlightthickness=1,
                                    highlightbackground="#c6d0f5")
        self.stats_card.pack(fill="x")
        self.stats_label = tk.Label(
            self.stats_card, text="No data available yet.",
            font=("Segoe UI", 10), bg="#eef2ff", fg=self.COLOR_TEXT,
            justify="left", anchor="w", padx=12, pady=10,
        )
        self.stats_label.pack(fill="x")

    def _build_distribution_tab(self, parent):
        pad = tk.Frame(parent, bg=self.COLOR_CARD)
        pad.pack(fill="both", expand=True, padx=6, pady=12)

        tk.Label(pad, text="📊 Grade Distribution", font=("Segoe UI", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 10))

        self.chart_canvas = tk.Canvas(pad, width=280, height=320, bg="white",
                                       highlightthickness=1, highlightbackground="#e2e6ef")
        self.chart_canvas.pack(fill="both", expand=True)

    def _build_calculator_tab(self, parent):
        pad = tk.Frame(parent, bg=self.COLOR_CARD)
        pad.pack(fill="both", expand=True, padx=6, pady=12)

        tk.Label(pad, text="🎯 Marks Needed", font=("Segoe UI", 12, "bold"),
                 bg=self.COLOR_CARD, fg=self.COLOR_NAVY).pack(anchor="w", pady=(0, 10))

        tk.Label(pad, text="Select Student:", font=("Segoe UI", 10),
                 bg=self.COLOR_CARD, fg=self.COLOR_MUTED).pack(anchor="w")

        self.student_dropdown = ttk.Combobox(pad, state="readonly", width=26, font=("Segoe UI", 10))
        self.student_dropdown.pack(anchor="w", pady=(4, 10))

        calc_btn = tk.Button(
            pad, text="Calculate", font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_ACCENT, fg="white", activebackground=self.COLOR_NAVY_LIGHT,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self.handle_marks_needed,
        )
        calc_btn.pack(fill="x", ipady=8)

        self.marks_needed_label = tk.Label(
            pad, text="Select a student and click Calculate.",
            font=("Segoe UI", 10, "italic"), bg=self.COLOR_CARD, fg=self.COLOR_MUTED,
            wraplength=270, justify="left",
        )
        self.marks_needed_label.pack(anchor="w", pady=(14, 0))

    # ==================================================================
    # EVENT HANDLERS
    # ==================================================================

    def handle_submit_form(self):
        """Routes to Add or Update depending on current editing state."""
        if self.editing_id is None:
            self.handle_add_student()
        else:
            self.handle_update_student()

    def _validate_form(self):
        """
        Shared validation for Add and Update.
        Returns (name, marks) on success, or (None, None) after showing
        an error message on failure.
        """
        name = self.name_entry.get().strip()
        marks_text = self.marks_entry.get().strip()

        if name == "":
            messagebox.showerror("Invalid Input", "Student name cannot be empty.")
            return None, None

        try:
            marks = float(marks_text)
        except ValueError:
            messagebox.showerror("Invalid Input", "Marks must be a numeric value.")
            return None, None

        if marks < 0 or marks > 100:
            messagebox.showerror("Invalid Input", "Marks must be between 0 and 100.")
            return None, None

        if marks.is_integer():
            marks = int(marks)

        return name, marks

    def handle_add_student(self):
        """Validates input and adds a new student record."""
        global next_student_id

        name, marks = self._validate_form()
        if name is None:
            return

        grade = calculate_grade(marks)
        result = check_result(marks)

        student = {
            "id": next_student_id, "name": name, "marks": marks,
            "grade": grade, "result": result,
        }
        students.append(student)
        next_student_id += 1

        self.refresh_all()
        self.handle_clear_form()
        self.set_status(f"Added student '{name}'.")

    def handle_update_student(self):
        """Validates input and updates the student currently being edited."""
        name, marks = self._validate_form()
        if name is None:
            return

        for s in students:
            if s["id"] == self.editing_id:
                s["name"] = name
                s["marks"] = marks
                s["grade"] = calculate_grade(marks)
                s["result"] = check_result(marks)
                break

        self.refresh_all()
        self.handle_cancel_edit()
        self.set_status(f"Updated student '{name}'.")

    def handle_edit_selected(self):
        """Loads the selected table row into the form for editing."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student in the table first.")
            return

        student_id = int(selection[0])
        student = next((s for s in students if s["id"] == student_id), None)
        if student is None:
            return

        self.editing_id = student_id

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, student["name"])
        self.marks_entry.delete(0, tk.END)
        self.marks_entry.insert(0, str(student["marks"]))
        self.update_live_preview()

        self.form_heading.config(text="✏️ Edit Student")
        self.submit_btn.config(text="Update Student")
        self.cancel_edit_btn.pack(fill="x", ipady=8, pady=(0, 8))
        self.set_status(f"Editing student '{student['name']}'.")

    def handle_cancel_edit(self):
        """Exits edit mode and resets the form back to 'Add' mode."""
        self.editing_id = None
        self.form_heading.config(text="➕ Add Student")
        self.submit_btn.config(text="Add Student")
        self.cancel_edit_btn.pack_forget()
        self.handle_clear_form()

    def handle_delete_selected(self):
        """Deletes the selected student after confirmation."""
        global students
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a student in the table first.")
            return

        student_id = int(selection[0])
        student = next((s for s in students if s["id"] == student_id), None)
        if student is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete", f"Delete student '{student['name']}'? This cannot be undone."
        )
        if not confirmed:
            return

        students = [s for s in students if s["id"] != student_id]

        # If the deleted student was being edited, cancel edit mode
        if self.editing_id == student_id:
            self.handle_cancel_edit()

        self.refresh_all()
        self.set_status(f"Deleted student '{student['name']}'.")

    def handle_clear_form(self):
        """Clears just the input fields (does not affect editing state)."""
        self.name_entry.delete(0, tk.END)
        self.marks_entry.delete(0, tk.END)
        self.live_preview_label.config(text="")

    def handle_clear_all(self):
        """Removes ALL student records after confirmation."""
        global students
        if not students:
            messagebox.showinfo("Nothing to Clear", "There are no records to clear.")
            return

        confirmed = messagebox.askyesno(
            "Confirm Clear All", "This will permanently delete ALL student records. Continue?"
        )
        if not confirmed:
            return

        students = []
        self.handle_cancel_edit()
        self.refresh_all()
        self.set_status("Cleared all records.")

    def handle_view_statistics(self):
        """Refreshes the statistics card, topper card, and distribution chart."""
        self.refresh_overview()
        self.refresh_distribution_chart()
        self.set_status("Statistics refreshed.")

    def handle_find_topper(self):
        """Finds and displays the class topper, and highlights their table row."""
        self.refresh_overview()
        self.refresh_table()  # re-applies the topper highlight tag
        self.set_status("Class topper located.")

    def handle_marks_needed(self):
        """Displays how many marks the selected student needs for the next grade."""
        selected_name = self.student_dropdown.get()
        if not selected_name:
            messagebox.showwarning("No Selection", "Please select a student first.")
            return

        matched_student = next((s for s in students if s["name"] == selected_name), None)
        if matched_student is None:
            messagebox.showerror("Error", "Selected student not found.")
            return

        message = marks_needed(matched_student["marks"])
        self.marks_needed_label.config(
            text=f"{selected_name} (Marks: {matched_student['marks']}): {message}"
        )

    # ---- File I/O handlers ----

    def handle_save_csv(self):
        """Saves all student records to a CSV file chosen by the user."""
        if not students:
            messagebox.showinfo("Nothing to Save", "There are no records to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save Student Records",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Marks", "Grade", "Result"])
                for s in students:
                    writer.writerow([s["name"], s["marks"], s["grade"], s["result"]])
            self.set_status(f"Saved {len(students)} records to {file_path}.")
            messagebox.showinfo("Saved", f"Records saved successfully to:\n{file_path}")
        except OSError as error:
            messagebox.showerror("Save Failed", f"Could not save the file.\n{error}")

    def handle_load_csv(self):
        """Loads student records from a CSV file chosen by the user."""
        global next_student_id

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")], title="Load Student Records"
        )
        if not file_path:
            return

        loaded_count = 0
        skipped_count = 0

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        name = row["Name"].strip()
                        marks = float(row["Marks"])
                        if name == "" or marks < 0 or marks > 100:
                            skipped_count += 1
                            continue
                        if marks.is_integer():
                            marks = int(marks)

                        student = {
                            "id": next_student_id, "name": name, "marks": marks,
                            "grade": calculate_grade(marks), "result": check_result(marks),
                        }
                        students.append(student)
                        next_student_id += 1
                        loaded_count += 1
                    except (KeyError, ValueError):
                        skipped_count += 1
        except OSError as error:
            messagebox.showerror("Load Failed", f"Could not read the file.\n{error}")
            return

        self.refresh_all()
        self.set_status(f"Loaded {loaded_count} records ({skipped_count} skipped).")
        messagebox.showinfo(
            "Load Complete",
            f"Loaded {loaded_count} student(s).\nSkipped {skipped_count} invalid row(s).",
        )

    def handle_export_report(self):
        """Exports a full text report: statistics + topper + student list."""
        if not students:
            messagebox.showinfo("Nothing to Export", "There are no records to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            title="Export Report",
        )
        if not file_path:
            return

        stats = class_statistics()
        topper = find_topper()
        ranked = get_ranked_students()

        lines = []
        lines.append("STUDENT RESULT MANAGEMENT SYSTEM - CLASS REPORT")
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 55)
        lines.append("")
        lines.append("CLASS STATISTICS")
        lines.append(f"  Total Students : {stats['total_students']}")
        lines.append(f"  Class Average  : {stats['average']}")
        lines.append(f"  Highest Marks  : {stats['highest']}")
        lines.append(f"  Lowest Marks   : {stats['lowest']}")
        lines.append(f"  Passed         : {stats['passed']}")
        lines.append(f"  Failed         : {stats['failed']}")
        lines.append("")
        lines.append("CLASS TOPPER")
        lines.append(f"  {display_result(topper).replace(chr(10), chr(10) + '  ')}")
        lines.append("")
        lines.append("FULL STUDENT LIST (ranked by marks)")
        lines.append(f"  {'Rank':<6}{'Name':<22}{'Marks':<8}{'Grade':<8}{'Result':<8}")
        lines.append("  " + "-" * 50)
        for s in ranked:
            lines.append(f"  {s['rank']:<6}{s['name']:<22}{s['marks']:<8}{s['grade']:<8}{s['result']:<8}")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.set_status(f"Report exported to {file_path}.")
            messagebox.showinfo("Exported", f"Report saved successfully to:\n{file_path}")
        except OSError as error:
            messagebox.showerror("Export Failed", f"Could not save the report.\n{error}")

    # ==================================================================
    # REFRESH / HELPER FUNCTIONS
    # ==================================================================

    def refresh_all(self):
        """Refreshes every dynamic part of the GUI at once."""
        self.refresh_table()
        self.refresh_dropdown()
        self.refresh_overview()
        self.refresh_distribution_chart()

    def refresh_table(self):
        """
        Clears and repopulates the Treeview table, applying the current
        search filter and sort order. Also highlights the class topper.
        """
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_term = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""

        ranked = get_ranked_students()

        # Apply search filter (matches on name, case-insensitive)
        if search_term:
            visible = [s for s in ranked if search_term in s["name"].lower()]
        else:
            visible = ranked

        # Apply column sorting if a column has been chosen
        if self.sort_column:
            visible = sorted(
                visible, key=lambda s: s[self.sort_column], reverse=self.sort_reverse
            )

        topper = find_topper()
        topper_id = topper["id"] if topper else None

        for s in visible:
            tag = "pass_row" if s["result"] == "PASS" else "fail_row"
            tags = [tag]
            if s["id"] == topper_id:
                tags.append("topper_row")
            self.tree.insert(
                "", "end", iid=str(s["id"]),
                values=(s["rank"], s["name"], s["marks"], s["grade"], s["result"]),
                tags=tuple(tags),
            )

    def refresh_dropdown(self):
        """Updates the student selection dropdown used in the Calculator tab."""
        names = [s["name"] for s in students]
        self.student_dropdown["values"] = names
        if self.student_dropdown.get() not in names:
            self.student_dropdown.set("")
            self.marks_needed_label.config(text="Select a student and click Calculate.")

    def refresh_overview(self):
        """Updates the Topper card and Statistics card text."""
        topper = find_topper()
        if topper is None:
            self.topper_label.config(text="No students added yet.")
        else:
            self.topper_label.config(text=display_result(topper))

        stats = class_statistics()
        if stats is None:
            self.stats_label.config(text="No data available yet.\nAdd students to see statistics.")
        else:
            stats_text = (
                f"Total Students : {stats['total_students']}\n"
                f"Class Average  : {stats['average']}\n"
                f"Highest Marks  : {stats['highest']}\n"
                f"Lowest Marks   : {stats['lowest']}\n"
                f"Passed         : {stats['passed']}\n"
                f"Failed         : {stats['failed']}"
            )
            self.stats_label.config(text=stats_text)

    def refresh_distribution_chart(self):
        """Draws a simple bar chart of grade distribution on the Canvas."""
        canvas = self.chart_canvas
        canvas.delete("all")

        counts = grade_distribution()
        grades_order = ["A+", "A", "B", "C", "D", "F"]
        max_count = max(counts.values()) if any(counts.values()) else 1

        canvas_width = int(canvas.cget("width"))
        canvas_height = int(canvas.cget("height"))

        chart_top = 20
        chart_bottom = canvas_height - 40
        chart_height = chart_bottom - chart_top

        bar_area_width = canvas_width - 40
        bar_width = bar_area_width // len(grades_order) - 14
        x = 30

        if not students:
            canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="No data to display.\nAdd students first.",
                fill=self.COLOR_MUTED, font=("Segoe UI", 10), justify="center",
            )
            return

        for grade in grades_order:
            count = counts[grade]
            bar_height = int((count / max_count) * chart_height) if max_count else 0
            y_top = chart_bottom - bar_height
            color = self.GRADE_COLORS[grade]

            canvas.create_rectangle(
                x, y_top, x + bar_width, chart_bottom, fill=color, outline=""
            )
            # Count label above the bar
            canvas.create_text(
                x + bar_width / 2, y_top - 10, text=str(count),
                font=("Segoe UI", 9, "bold"), fill=self.COLOR_TEXT,
            )
            # Grade label below the bar
            canvas.create_text(
                x + bar_width / 2, chart_bottom + 15, text=grade,
                font=("Segoe UI", 9, "bold"), fill=self.COLOR_TEXT,
            )
            x += bar_width + 14

        # Baseline
        canvas.create_line(20, chart_bottom, canvas_width - 20, chart_bottom, fill="#d1d5db")


# ------------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------------
def main():
    root = tk.Tk()
    app = StudentResultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()