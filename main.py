import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ttkbootstrap import Style
from test_case_component import AutomatedTestingApp as TestComposApp
import os
import tkinter.filedialog as fd
import shutil
import time
from fpdf import FPDF
import csv
import json
from test_suite_manager import TestSuiteManager

class AutomatedTestingApp:
    def __init__(self, master):
        self.master = master
        master.title("Automated Testing Application")
        master.geometry("900x700")

        self.unsaved_changes = False  # Initialize the unsaved_changes attribute
        self.current_folder = None  # Track the current folder being displayed

        # Ensure the existence of the "projects" folder
        self.project_folder = "projects"
        if not os.path.exists(self.project_folder):
            os.makedirs(self.project_folder)

        # Ensure the existence of the "Test Cases" and "Test Suites" folders
        self.test_cases_folder = os.path.join(self.project_folder, "Test Cases")
        self.test_suites_folder = os.path.join(self.project_folder, "Test Suites")
        os.makedirs(self.test_cases_folder, exist_ok=True)
        os.makedirs(self.test_suites_folder, exist_ok=True)

        # Styling with ttkbootstrap
        style = Style(theme='flatly')  # Use the Flatly theme

        # Menu Bar
        self.menu_bar = tk.Menu(master)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Test Case", command=self.new_project)
        self.file_menu.add_command(label="Open Test Case", command=self.open_project)
        self.file_menu.add_command(label="Save Test Case", command=self.save_project)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_application)

        # Components menu
        self.components_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.components_menu.add_command(label="Launch Web", command=lambda: self.add_block("Launch Web:"))
        self.components_menu.add_command(label="Input field", command=lambda: self.add_block("Input by"))
        self.components_menu.add_command(label="Click action", command=lambda: self.add_block("Click"))
        self.components_menu.add_command(label="Verifying static content", command=lambda: self.add_block("Static content"))
        self.components_menu.add_command(label="Select dropdown menu option", command=lambda: self.add_block("Dropdown option"))
        self.components_menu.add_command(label="Select radio button", command=lambda: self.add_block("Radio button"))
        self.components_menu.add_command(label="Navigation", command=lambda: self.add_block("Navigate"))
        self.components_menu.add_command(label="Connect to Database", command=lambda: self.add_block("Database"))
        self.components_menu.add_command(label="Retrieve data", command=lambda: self.add_block("Retrieve data"))
        self.components_menu.add_command(label="Delay action", command=lambda: self.add_block("Delay:"))

        # Test Suites menu
        self.suites_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.suites_menu.add_command(label="New Suite", command=self.new_suite)
        self.suites_menu.add_command(label="Edit Suite", command=self.edit_suite)
        self.suites_menu.add_command(label="Run Suite", command=self.run_suite)

        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.about)

        # Add menus to menu bar
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Components", menu=self.components_menu)
        self.menu_bar.add_cascade(label="Test Suites", menu=self.suites_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        master.config(menu=self.menu_bar)

        # Toolbar
        self.toolbar = tk.Frame(master, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.webdriver_label = tk.Label(self.toolbar, text="Select WebDriver:")
        self.webdriver_label.pack(side=tk.LEFT, padx=5)

        self.webdriver_options = ["Chrome", "Edge", "Firefox"]
        self.webdriver_var = tk.StringVar(value=self.webdriver_options[0])
        self.webdriver_dropdown = ttk.Combobox(self.toolbar, textvariable=self.webdriver_var, values=self.webdriver_options, state='readonly')
        self.webdriver_dropdown.pack(side=tk.LEFT, padx=2)

        # Bind the event to the combobox
        self.webdriver_dropdown.bind("<<ComboboxSelected>>", self.on_combobox_select)

        # Add separator
        separator = tk.Canvas(self.toolbar, height=20, width=1, bd=0, highlightthickness=0, bg='black')
        separator.pack(side=tk.LEFT, padx=5, pady=2)

        self.button_start = ttk.Button(self.toolbar, text="Start Testing", command=self.start_testing)
        self.button_start.pack(side=tk.LEFT, padx=2)

        self.button_save = ttk.Button(self.toolbar, text="Save Test Case", command=self.save_project)
        self.button_save.pack(side=tk.LEFT, padx=2)

        self.button_suite = ttk.Button(self.toolbar, text="Start Test Suite", command=self.run_suite)
        self.button_suite.pack(side=tk.LEFT, padx=2)

        # Create a PanedWindow for horizontal layout
        self.paned_window_horizontal = ttk.PanedWindow(master, orient=tk.HORIZONTAL)
        self.paned_window_horizontal.pack(fill=tk.BOTH, expand=True)

        # Side Panel
        self.side_panel = tk.Frame(self.paned_window_horizontal, bg='lightgrey', width=200)
        self.label_project = tk.Label(self.side_panel, text="Project:", font=('Helvetica', 12))
        self.label_project.pack(pady=10)
        self.project_listbox = tk.Listbox(self.side_panel)
        self.project_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.paned_window_horizontal.add(self.side_panel)

        # Load existing project files into the listbox
        self.load_existing_projects()

        # Create a PanedWindow for vertical layout
        self.paned_window_vertical = ttk.PanedWindow(self.paned_window_horizontal, orient=tk.VERTICAL)
        self.paned_window_horizontal.add(self.paned_window_vertical)

        # Main Panel
        self.main_panel = tk.Frame(self.paned_window_vertical, bg='white', bd=1, relief=tk.RAISED)
        self.paned_window_vertical.add(self.main_panel)

        # Log and Reports Panel
        self.log_reports_panel = tk.Frame(self.paned_window_vertical, bg='lightgrey', bd=1, relief=tk.RAISED)
        
        # Add a frame for the label, clear button, and print button
        self.label_clear_frame = tk.Frame(self.log_reports_panel, bg='lightgrey')
        self.label_clear_frame.pack(fill=tk.X, pady=10, padx=10)

        self.label_log_reports = tk.Label(self.label_clear_frame, text="Log & Reports", font=('Helvetica', 12), bg='lightgrey')
        self.label_log_reports.pack(side=tk.LEFT, padx=20)

        self.clear_button = ttk.Button(self.label_clear_frame, text="Clear", command=self.clear_log)
        self.clear_button.pack(side=tk.RIGHT, padx=5)

        self.print_button = ttk.Button(self.label_clear_frame, text="Print", command=self.print_log)
        self.print_button.pack(side=tk.RIGHT, padx=5)

        self.csv_button = ttk.Button(self.label_clear_frame, text="Export CSV", command=self.export_csv)
        self.csv_button.pack(side=tk.RIGHT, padx=5)

        self.log_text = tk.Text(self.log_reports_panel, height=8, state=tk.DISABLED)
        self.log_text.pack(padx=10, fill=tk.BOTH, expand=True)
        self.paned_window_vertical.add(self.log_reports_panel)

        # Integrate test case components into main panel
        self.test_app = TestComposApp(master, self.main_panel, self.toolbar, self.log, self.mark_as_unsaved)

        # Configure weight for resizable
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.paned_window_horizontal.columnconfigure(0, weight=1)
        self.paned_window_horizontal.columnconfigure(1, weight=1)
        self.paned_window_vertical.rowconfigure(0, weight=1)
        self.paned_window_vertical.rowconfigure(1, weight=1)

        # Handle the window close event
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize TestSuiteManager
        self.test_suite_manager = TestSuiteManager(self.test_cases_folder, self.test_suites_folder)  # Pass the folders to the manager

    def on_combobox_select(self, event):
        event.widget.selection_clear()

    def start_testing(self):
        webdriver_choice = self.webdriver_var.get()
        self.test_app.start_testing(webdriver_choice)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END,"\n\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def add_block(self, block_type):
        self.test_app.create_draggable_block(50, 50, block_type)
        self.mark_as_unsaved()

    def about(self):
        about_message = "Automated Testing Application\nVersion 1.0\nDeveloped by Shahirah Binti Abdul Aziz"
        messagebox.showinfo("About", about_message)

    def load_existing_projects(self):
        self.project_listbox.delete(0, tk.END)
        self.project_listbox.insert(tk.END, "Test Cases")
        self.project_listbox.insert(tk.END, "Test Suites")
        self.project_listbox.bind('<<ListboxSelect>>', self.on_project_select)

    def new_project(self):
        self.test_app.clear_canvas()
        self.project_listbox.selection_clear(0, tk.END)
        self.clear_log()
        self.mark_as_unsaved()

    def open_project(self):
        file_path = fd.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=self.test_cases_folder)
        if file_path:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(self.test_cases_folder, file_name)
            
            # Copy the file to the "Test Cases" folder
            shutil.copy(file_path, dest_path)
            
            self.test_app.load_test_case(dest_path)
            self.update_project_list(file_name)
            self.clear_log()
            self.unsaved_changes = False

    def save_project(self):
        file_path = fd.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=self.test_cases_folder)
        if file_path:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(self.test_cases_folder, file_name)
            self.test_app.save_test_case(dest_path)
            self.update_project_list(file_name)
            self.unsaved_changes = False

    def update_project_list(self, file_name):
        if file_name not in self.project_listbox.get(0, tk.END):
            self.project_listbox.insert(tk.END, file_name)

    def on_project_select(self, event):
        selected = self.project_listbox.curselection()
        if selected:
            folder_name = self.project_listbox.get(selected[0])
            if folder_name == "Test Cases":
                if self.current_folder == "Test Cases":
                    self.load_existing_projects()
                    self.current_folder = None
                else:
                    self.display_files(self.test_cases_folder, "Test Cases")
                    self.current_folder = "Test Cases"
            elif folder_name == "Test Suites":
                if self.current_folder == "Test Suites":
                    self.load_existing_projects()
                    self.current_folder = None
                else:
                    self.display_files(self.test_suites_folder, "Test Suites")
                    self.current_folder = "Test Suites"
            else:
                self.load_test_case_or_suite(folder_name)

    def display_files(self, folder_path, folder_name):
        self.project_listbox.delete(0, tk.END)  # Clear all items
        self.project_listbox.insert(tk.END, folder_name)  # Insert the folder name
        for file in os.listdir(folder_path):
            self.project_listbox.insert(tk.END, file)

    def load_test_case_or_suite(self, file_name):
        if self.current_folder == "Test Cases":
            file_path = os.path.join(self.test_cases_folder, file_name)
            if os.path.exists(file_path):
                self.test_app.load_test_case(file_path)
                self.clear_log()
                self.unsaved_changes = False
        elif self.current_folder == "Test Suites":
            file_path = os.path.join(self.test_suites_folder, file_name)
            if os.path.exists(file_path):
                self.display_test_suite(file_path)

    def display_test_suite(self, file_path):
        with open(file_path, 'r') as file:
            content = json.load(file)
            content_str = "\n".join(content)
            messagebox.showinfo("Test Suite Content", content_str)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def print_log(self):
        log_content = self.log_text.get(1.0, tk.END).strip()
        current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        project_file_name = None

        selected = self.project_listbox.curselection()
        if selected:
            project_file_name = self.project_listbox.get(selected[0])

        # Ask user where to save the output
        file_path = fd.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf")])
        if file_path:
            if file_path.endswith('.txt'):
                with open(file_path, 'w') as file:
                    file.write(f"Test Results on {current_date}\n")
                    if project_file_name:
                        file.write(f"Project File: {project_file_name}\n\n")
                    file.write(log_content)
            elif file_path.endswith('.pdf'):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Test Results on {current_date}", ln=True, align='C')
                if project_file_name:
                    pdf.cell(200, 10, txt=f"Project File: {project_file_name}", ln=True, align='C')
                pdf.ln(10)  # Add a line break
                pdf.multi_cell(0, 10, log_content)
                pdf.output(file_path)

    def export_csv(self):
        log_content = self.log_text.get(1.0, tk.END).strip().split('\n')
        log_entries = [(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), entry) for entry in log_content]

        file_path = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                log_writer = csv.writer(csvfile)
                log_writer.writerow(['Timestamp', 'Log Entry'])
                log_writer.writerows(log_entries)

    def on_closing(self):
        if self.unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before exiting?"):
                self.save_project()
        self.master.destroy()

    def mark_as_unsaved(self):
        self.unsaved_changes = True

    def exit_application(self):
        self.on_closing()

    def new_suite(self):
        self.test_suite_manager.new_suite(self.master, self.webdriver_var, self.test_app)

    def edit_suite(self):
        self.test_suite_manager.edit_suite(self.master)

    def run_suite(self):
        self.test_suite_manager.run_suite(self.test_app, self.webdriver_var, self.master)

def main():
    root = tk.Tk()
    app = AutomatedTestingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
