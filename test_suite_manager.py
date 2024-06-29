import tkinter as tk
from tkinter import messagebox, simpledialog
import tkinter.filedialog as fd
import json
import os

class TestSuiteManager:
    def __init__(self, test_cases_folder, test_suites_folder):
        self.test_cases_folder = test_cases_folder
        self.test_suites_folder = test_suites_folder
        self.test_suites = {}

    def new_suite(self, parent, webdriver_var, test_app):
        suite_name = simpledialog.askstring("Input", "Enter new suite name:", parent=parent)
        if suite_name:
            self.test_suites[suite_name] = []

            # Save the new suite file in the correct folder
            suite_file_path = os.path.join(self.test_suites_folder, f"{suite_name}.json")
            with open(suite_file_path, 'w') as file:
                json.dump(self.test_suites[suite_name], file)
            
            messagebox.showinfo("Edit suite", "Please choose the test cases.")
            file_paths = fd.askopenfilenames(title="Select Test Case Files", filetypes=[("JSON files", "*.json")], initialdir=self.test_cases_folder)
            if file_paths:
                self.test_suites[suite_name].extend(file_paths)

                # Save the updated suite
                with open(suite_file_path, 'w') as file:
                    json.dump(self.test_suites[suite_name], file)

                # Ask to run the suite
                if messagebox.askyesno("Run Suite", "Do you want to run the suite now?", parent=parent):
                    webdriver_choice = webdriver_var.get()
                    if suite_file_path:
                        with open(suite_file_path, 'r') as file:
                            test_cases = json.load(file)
                        webdriver_choice = webdriver_var.get()
                        test_app.run_test_suite(test_cases, webdriver_choice)
                    else:
                        messagebox.showerror("Error", "Suite not found", parent=parent)
    def edit_suite(self, parent):
        suite_name = simpledialog.askstring("Input", "Enter suite name to edit:", parent=parent)
        suite_file_path = os.path.join(self.test_suites_folder, f"{suite_name}.json")
        if os.path.exists(suite_file_path):
            # Clear the current suite
            self.test_suites[suite_name] = []

            file_paths = fd.askopenfilenames(title="Select Test Case Files", filetypes=[("JSON files", "*.json")], initialdir=self.test_cases_folder)
            if file_paths:
                self.test_suites[suite_name].extend(file_paths)
                with open(suite_file_path, 'w') as file:
                    json.dump(self.test_suites[suite_name], file)
        else:
            messagebox.showerror("Error", "Suite not found", parent=parent)

    def run_suite(self, test_app, webdriver_var, parent):
        suite_file_path = fd.askopenfilename(title="Select Test Suite File", filetypes=[("JSON files", "*.json")], initialdir=self.test_suites_folder)
        if suite_file_path:
            with open(suite_file_path, 'r') as file:
                test_cases = json.load(file)
            webdriver_choice = webdriver_var.get()
            test_app.run_test_suite(test_cases, webdriver_choice)
        else:
            messagebox.showerror("Error", "Suite not found", parent=parent)

