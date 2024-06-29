import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time
import json

# Import database connector libraries
import pymysql
import psycopg2
import pyodbc

class AutomatedTestingApp:
    def __init__(self, master, main_panel, toolbar, logger, change_callback):
        self.master = master
        self.main_panel = main_panel
        self.toolbar = toolbar
        self.logger = logger
        self.change_callback = change_callback  # This callback is to mark unsaved changes

        # Canvas for visual test case
        self.canvas = tk.Canvas(self.main_panel, bg='white', bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # List to maintain draggable block objects
        self.blocks = []

        # Bind mouse events for creating and moving blocks
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Right-click context menu for duplicating blocks
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.context_menu.add_command(label="Duplicate", command=self.duplicate_block)
        self.context_menu.add_command(label="Delete", command=self.delete_block)

        # Bind right-click to open the context menu
        self.canvas.bind("<Button-3>", self.show_context_menu)

        # Bind keyboard shortcuts
        self.master.bind("<Control-v>", self.duplicate_block)
        self.master.bind("<Delete>", self.delete_block)

    def create_draggable_block(self, x, y, text):
        tag = f"block_{len(self.blocks)}"
        block = None
        element_dropdown_window = None
        content_type_dropdown_window = None
        element_identifier_window = None
        input_query_window = None
        seconds_label = None

        if text in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
            block_width = {
                "Input by": 560,
                "Dropdown option": 660,
                "Click": 530,
                "Radio button": 530,
                "Static content": 700
            }[text]
            block = self.canvas.create_rectangle(x, y, x + block_width, y + 50, fill="lightblue", outline="black", tags=("block", tag))

            element_options = ["NAME", "ID", "CLASS_NAME", "CSS_SELECTOR", "LINK_TEXT", "PARTIAL_LINK_TEXT", "TAG_NAME", "XPATH"]
            selected_element = tk.StringVar(value=element_options[0])
            element_dropdown = ttk.Combobox(self.canvas, textvariable=selected_element, values=element_options, width=15)
            element_dropdown.bind("<FocusIn>", self.on_entry_focus)
            element_dropdown_window = self.canvas.create_window(x + (130 if text in ["Input by", "Click"] else 260 if text == "Static content" else 180), y + 25, window=element_dropdown, tags=("dropdown", tag))

            entry_width = 50 if text == "Click" else 35 if text in ["Radio button", "Dropdown option"] else 30

            element_identifier_entry = tk.Entry(self.canvas, width=entry_width)
            element_identifier_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, element_identifier_entry))
            element_identifier_entry.insert(0, "element identifier")
            element_identifier_window = self.canvas.create_window(x + (285 if text == "Input by" else 360 if text in ["Dropdown option", "Radio button"] else 420 if text == "Static content" else 347), y + 25, window=element_identifier_entry, tags=("entry", tag))

            if text == "Static content":
                content_type_options = ["Text", "Image", "Icon"]
                selected_content_type = tk.StringVar(value=content_type_options[0])
                content_type_dropdown = ttk.Combobox(self.canvas, textvariable=selected_content_type, values=content_type_options, width=10)
                content_type_dropdown.bind("<FocusIn>", self.on_entry_focus)
                content_type_dropdown_window = self.canvas.create_window(x + 152, y + 25, window=content_type_dropdown, tags=("dropdown", tag))

            if text in ["Input by", "Dropdown option", "Static content"]:
                input_query_entry = tk.Entry(self.canvas, width=25)
                input_query_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, input_query_entry))
                input_query_entry.insert(0, "input")
                input_query_window = self.canvas.create_window(x + (460 if text == "Input by" else 600 if text == "Static content" else 560), y + 25, window=input_query_entry, tags=("entry", tag))
            
            text_tag = self.canvas.create_text(x + (40 if text in ["Input by", "Click"] else 65), y + 25, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, content_type_dropdown if text == "Static content" else None, content_type_dropdown_window if text == "Static content" else None, element_dropdown, element_dropdown_window, element_identifier_entry, element_identifier_window, input_query_entry if text in ["Input by", "Dropdown option", "Static content"] else None, input_query_window if text in ["Input by", "Dropdown option", "Static content"] else None))

        elif text == "Launch Web:":
            block = self.canvas.create_rectangle(x, y, x + 400, y + 50, fill="lightblue", outline="black", tags=("block", tag))
            url_entry = tk.Entry(self.canvas, width=45)
            url_entry.bind("<FocusIn>", self.on_entry_focus)
            input_window = self.canvas.create_window(x + 250, y + 25, window=url_entry, tags=("entry", tag))
            text_tag = self.canvas.create_text(x + 60, y + 25, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, url_entry, input_window))

        elif text == "Delay:":
            block = self.canvas.create_rectangle(x, y, x + 200, y + 50, fill="lightblue", outline="black", tags=("block", tag))
            delay_entry = tk.Entry(self.canvas, width=10)
            delay_entry.bind("<FocusIn>", self.on_entry_focus)
            input_window = self.canvas.create_window(x + 97, y + 25, window=delay_entry, tags=("entry", tag))
            seconds_label = self.canvas.create_text(x + 160, y + 25, text="second(s)", fill="black", tags=("text", tag))
            text_tag = self.canvas.create_text(x + 40, y + 25, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, delay_entry, input_window, seconds_label))

        elif text == "Navigate":
            block = self.canvas.create_rectangle(x, y, x + 200, y + 50, fill="lightblue", outline="black", tags=("block", tag))
            navigation_options = ["Backward", "Forward", "Refresh"]
            selected_navigation = tk.StringVar(value=navigation_options[0])
            navigation_dropdown = ttk.Combobox(self.canvas, textvariable=selected_navigation, values=navigation_options, width=10)
            navigation_dropdown.bind("<FocusIn>", self.on_entry_focus)
            navigation_dropdown_window = self.canvas.create_window(x + 140, y + 25, window=navigation_dropdown, tags=("dropdown", tag))
            text_tag = self.canvas.create_text(x + 50, y + 25, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, navigation_dropdown, navigation_dropdown_window))

        elif text == "Database":
            block = self.canvas.create_rectangle(x, y, x + 500, y + 80, fill="lightblue", outline="black", tags=("block", tag))

            db_options = ["MySQL", "PostgreSQL", "Microsoft SQL Server"]
            selected_db = tk.StringVar(value=db_options[0])
            db_dropdown = ttk.Combobox(self.canvas, textvariable=selected_db, values=db_options, width=19)
            db_dropdown.bind("<FocusIn>", self.on_entry_focus)
            db_dropdown_window = self.canvas.create_window(x + 150, y + 29, window=db_dropdown, tags=("dropdown", tag))

            host_entry = tk.Entry(self.canvas, width=17)
            host_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, host_entry))
            host_entry.insert(0, "Host/Server")
            host_window = self.canvas.create_window(x + 280, y + 25, window=host_entry, tags=("entry", tag))

            dbname_entry = tk.Entry(self.canvas, width=17)
            dbname_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, dbname_entry))
            dbname_entry.insert(0, "Database Name")
            dbname_window = self.canvas.create_window(x + 410, y + 25, window=dbname_entry, tags=("entry", tag))

            username_entry = tk.Entry(self.canvas, width=17)
            username_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, username_entry))
            username_entry.insert(0, "Username")
            username_window = self.canvas.create_window(x + 280, y + 55, window=username_entry, tags=("entry", tag))

            password_entry = tk.Entry(self.canvas, width=17, show="*")
            password_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, password_entry))
            password_entry.insert(0, "Password")
            password_window = self.canvas.create_window(x + 410, y + 55, window=password_entry, tags=("entry", tag))

            text_tag = self.canvas.create_text(x + 50, y + 25, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, db_dropdown, db_dropdown_window, host_entry, host_window, dbname_entry, dbname_window, username_entry, username_window, password_entry, password_window))

        elif text == "Retrieve data":
            block = self.canvas.create_rectangle(x, y, x + 620, y + 100, fill="lightblue", outline="black", tags=("block", tag))

            select_entry = tk.Entry(self.canvas, width=15)
            select_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, select_entry))
            select_entry.insert(0, "SELECT data")
            select_window = self.canvas.create_window(x + 148, y + 35, window=select_entry, tags=("entry", tag))

            from_entry = tk.Entry(self.canvas, width=15)
            from_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, from_entry))
            from_entry.insert(0, "FROM table")
            from_window = self.canvas.create_window(x + 250, y + 35, window=from_entry, tags=("entry", tag))

            value1_entry = tk.Entry(self.canvas, width=15)
            value1_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, value1_entry))
            value1_entry.insert(0, "WHERE column1")
            value1_window = self.canvas.create_window(x + 350, y + 35, window=value1_entry, tags=("entry", tag))

            value2_entry = tk.Entry(self.canvas, width=15)
            value2_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, value2_entry))
            value2_entry.insert(0, "WHERE column2")
            value2_window = self.canvas.create_window(x + 450, y + 35, window=value2_entry, tags=("entry", tag))

            value3_entry = tk.Entry(self.canvas, width=15)
            value3_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, value3_entry))
            value3_entry.insert(0, "WHERE column3")
            value3_window = self.canvas.create_window(x + 550, y + 35, window=value3_entry, tags=("entry", tag))

            param1_entry = tk.Entry(self.canvas, width=15)
            param1_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, param1_entry))
            param1_entry.insert(0, "Value 1")
            param1_window = self.canvas.create_window(x + 350, y + 65, window=param1_entry, tags=("entry", tag))

            param2_entry = tk.Entry(self.canvas, width=15)
            param2_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, param2_entry))
            param2_entry.insert(0, "Value 2")
            param2_window = self.canvas.create_window(x + 450, y + 65, window=param2_entry, tags=("entry", tag))

            param3_entry = tk.Entry(self.canvas, width=15)
            param3_entry.bind("<FocusIn>", lambda event: self.on_input_focus(event, param3_entry))
            param3_entry.insert(0, "Value 3")
            param3_window = self.canvas.create_window(x + 550, y + 65, window=param3_entry, tags=("entry", tag))

            text_tag = self.canvas.create_text(x + 60, y + 35, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text, select_entry, select_window, from_entry, from_window, value1_entry, value1_window, value2_entry, value2_window, value3_entry, value3_window, param1_entry, param1_window, param2_entry, param2_window, param3_entry, param3_window))

        else:
            block = self.canvas.create_rectangle(x, y, x + 120, y + 40, fill="lightblue", outline="black", tags=("block", tag))
            text_tag = self.canvas.create_text(x + 60, y + 20, text=text, fill="black", tags=("text", tag))
            self.blocks.append((block, text_tag, text))

        # Mark changes
        self.change_callback()

    def on_input_focus(self, event, entry):
        self.deselect_block()
        entry.select_range(0, tk.END)

    def on_canvas_click(self, event):
        self.select_block(event)

    def on_canvas_drag(self, event):
        if hasattr(self, 'selected_block') and self.selected_block is not None:
            delta_x = event.x - self.canvas.coords(self.selected_block)[0]
            delta_y = event.y - self.canvas.coords(self.selected_block)[1]
            self.canvas.move(self.selected_block, delta_x, delta_y)

            if self.selected_text_tag:
                self.canvas.move(self.selected_text_tag, delta_x, delta_y)

            if self.selected_block_data[2] in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if self.selected_block_data[2] == "Static content":
                    self.canvas.move(self.selected_block_data[4], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[6], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[8], delta_x, delta_y)
                if self.selected_block_data[2] in ["Input by", "Dropdown option", "Static content"]:
                    self.canvas.move(self.selected_block_data[10], delta_x, delta_y)

            if self.selected_block_data[2] == "Launch Web:":
                self.canvas.move(self.selected_block_data[4], delta_x, delta_y)

            if self.selected_block_data[2] == "Delay:":
                self.canvas.move(self.selected_block_data[4], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[5], delta_x, delta_y)

            if self.selected_block_data[2] == "Navigate":
                self.canvas.move(self.selected_block_data[4], delta_x, delta_y)

            if self.selected_block_data[2] == "Database":
                self.canvas.move(self.selected_block_data[4], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[6], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[8], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[10], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[12], delta_x, delta_y)

            if self.selected_block_data[2] == "Retrieve data":
                self.canvas.move(self.selected_block_data[4], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[6], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[8], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[10], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[12], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[14], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[16], delta_x, delta_y)
                self.canvas.move(self.selected_block_data[18], delta_x, delta_y)

            self.canvas.tag_raise(self.selected_block)
            if self.selected_text_tag:
                self.canvas.tag_raise(self.selected_text_tag)

            for tag in self.canvas.gettags(self.selected_block):
                if tag.startswith("entry") or tag.startswith("dropdown"):
                    self.canvas.tag_raise(tag)
                if tag.startswith("text") and len(tag.split("_")) > 1:
                    self.canvas.tag_raise(tag)

            if self.selected_block_data[2] == "Delay:":
                self.canvas.tag_raise(self.selected_block_data[5])

            # Mark changes
            self.change_callback()

    def on_canvas_release(self, event):
        if hasattr(self, 'selected_block') and self.selected_block is not None:
            x1, y1, x2, y2 = self.canvas.coords(self.selected_block)
            closest_block = None
            closest_distance = float('inf')

            for block in self.blocks:
                if block[0] == self.selected_block:
                    continue
                bx1, by1, bx2, by2 = self.canvas.coords(block[0])
                distance = abs(y1 - by2)
                if distance < closest_distance and distance < 50:
                    closest_distance = distance
                    closest_block = block

            if closest_block:
                bx1, by1, bx2, by2 = self.canvas.coords(closest_block[0])
                self.snap_to_block(y1, by2)

            # Mark changes
            self.change_callback()

    def snap_to_block(self, current_pos, target_pos):
        offset = target_pos - current_pos
        self.canvas.move(self.selected_block, 0, offset)
        if self.selected_text_tag:
            self.canvas.move(self.selected_text_tag, 0, offset)

        if self.selected_block_data[2] in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if self.selected_block_data[2] == "Static content":
                    self.canvas.move(self.selected_block_data[4], 0, offset)
                self.canvas.move(self.selected_block_data[6], 0, offset)
                self.canvas.move(self.selected_block_data[8], 0, offset)
                if self.selected_block_data[2] in ["Input by", "Dropdown option", "Static content"]:
                    self.canvas.move(self.selected_block_data[10], 0, offset)

        if self.selected_block_data[2] == "Launch Web:":
            self.canvas.move(self.selected_block_data[4], 0, offset)

        if self.selected_block_data[2] == "Delay:":
            self.canvas.move(self.selected_block_data[4], 0, offset)
            self.canvas.move(self.selected_block_data[5], 0, offset)

        if self.selected_block_data[2] == "Navigate":
            self.canvas.move(self.selected_block_data[4], 0, offset)

        if self.selected_block_data[2] == "Database":
            self.canvas.move(self.selected_block_data[4], 0, offset)
            self.canvas.move(self.selected_block_data[6], 0, offset)
            self.canvas.move(self.selected_block_data[8], 0, offset)
            self.canvas.move(self.selected_block_data[10], 0, offset)
            self.canvas.move(self.selected_block_data[12], 0, offset)
        
        if self.selected_block_data[2] == "Retrieve data":
            self.canvas.move(self.selected_block_data[4], 0, offset)
            self.canvas.move(self.selected_block_data[6], 0, offset)
            self.canvas.move(self.selected_block_data[8], 0, offset)
            self.canvas.move(self.selected_block_data[10], 0, offset)
            self.canvas.move(self.selected_block_data[12], 0, offset)
            self.canvas.move(self.selected_block_data[14], 0, offset)
            self.canvas.move(self.selected_block_data[16], 0, offset)
            self.canvas.move(self.selected_block_data[18], 0, offset)

    def show_context_menu(self, event):
        self.deselect_block()
        self.select_block(event)
        if hasattr(self, 'selected_block') and self.selected_block:
            self.context_menu.post(event.x_root, event.y_root)

    def select_block(self, event):
        block_tags = self.canvas.find_withtag("block")
        block_tags = sorted(block_tags, key=lambda b: self.canvas.coords(b)[1], reverse=True)

        block_found = False

        for block in block_tags:
            x1, y1, x2, y2 = self.canvas.coords(block)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if hasattr(self, 'selected_block') and self.selected_block == block:
                    self.deselect_block()
                    return

                self.deselect_block(reset_data=False)
                self.selected_block = block
                self.selected_text_tag = None
                for b in self.blocks:
                    if b[0] == block:
                        self.selected_text_tag = b[1]
                        self.selected_block_data = b
                        block_found = True
                        break
                self.canvas.tag_raise(block)
                if self.selected_text_tag:
                    self.canvas.tag_raise(self.selected_text_tag)
                self.canvas.itemconfig(block, fill="yellow")

                for tag in self.canvas.gettags(block):
                    if tag.startswith("entry") or tag.startswith("dropdown"):
                        self.canvas.tag_raise(tag)
                    if tag.startswith("text") and len(tag.split("_")) > 1:
                        self.canvas.tag_raise(tag)

                self.master.focus()
                break

        if not block_found:
            self.deselect_block(reset_data=True)

    def deselect_block(self, reset_data=True):
        if hasattr(self, 'selected_block_data') and self.selected_block_data is not None:
            block_data = self.selected_block_data
            self.canvas.itemconfig(block_data[0], fill="lightblue")
        self.selected_block = None
        self.selected_text_tag = None
        if reset_data:
            self.selected_block_data = None

    def duplicate_block(self, event=None):
        if hasattr(self, 'selected_block_data') and self.selected_block_data:
            block_data = self.selected_block_data
            x1, y1, x2, y2 = self.canvas.coords(block_data[0])
            new_x = x1 + 20
            new_y = y1 + 20
            text = block_data[2]
            self.create_draggable_block(new_x, new_y, text)
            new_block_data = self.blocks[-1]

            if text in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if text == "Static content":
                    new_block_data[3].set(block_data[3].get())
                    new_block_data[5].set(block_data[5].get())
                    new_block_data[7].delete(0, tk.END)
                    new_block_data[7].insert(0, block_data[7].get())
                    new_block_data[9].delete(0, tk.END)
                    new_block_data[9].insert(0, block_data[9].get())
                else:
                    new_block_data[5].set(block_data[5].get())
                    new_block_data[7].delete(0, tk.END)
                    new_block_data[7].insert(0, block_data[7].get())
                    if text in ["Input by", "Dropdown option"]:
                        new_block_data[9].delete(0, tk.END)
                        new_block_data[9].insert(0, block_data[9].get())
            elif text == "Launch Web:":
                new_block_data[3].delete(0, tk.END)
                new_block_data[3].insert(0, block_data[3].get())
            elif text == "Delay:":
                new_block_data[3].delete(0, tk.END)
                new_block_data[3].insert(0, block_data[3].get())
            elif text == "Navigate":
                new_block_data[3].set(block_data[3].get())
            elif text == "Database":
                new_block_data[3].set(block_data[3].get())  # db_dropdown
                new_block_data[5].delete(0, tk.END)  # host_entry
                new_block_data[5].insert(0, block_data[5].get())
                new_block_data[7].delete(0, tk.END)  # dbname_entry
                new_block_data[7].insert(0, block_data[7].get())
                new_block_data[9].delete(0, tk.END)  # username_entry
                new_block_data[9].insert(0, block_data[9].get())
                new_block_data[11].delete(0, tk.END)  # password_entry
                new_block_data[11].insert(0, block_data[11].get())
            elif text == "Retrieve data":
                new_block_data[3].delete(0, tk.END)  
                new_block_data[3].insert(0, block_data[3].get())
                new_block_data[5].delete(0, tk.END)  
                new_block_data[5].insert(0, block_data[5].get())
                new_block_data[7].delete(0, tk.END)  
                new_block_data[7].insert(0, block_data[7].get())
                new_block_data[9].delete(0, tk.END)  
                new_block_data[9].insert(0, block_data[9].get())
                new_block_data[11].delete(0, tk.END)  
                new_block_data[11].insert(0, block_data[11].get())
                new_block_data[13].delete(0, tk.END)  
                new_block_data[13].insert(0, block_data[13].get())
                new_block_data[15].delete(0, tk.END)  
                new_block_data[15].insert(0, block_data[15].get())
                new_block_data[17].delete(0, tk.END)  
                new_block_data[17].insert(0, block_data[17].get())
            # Mark changes
            self.change_callback()

    def delete_block(self, event=None):
        if hasattr(self, 'selected_block_data') and self.selected_block_data:
            block_data = self.selected_block_data
            self.canvas.delete(block_data[0])
            self.canvas.delete(block_data[1])
            if block_data[2] in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                self.canvas.delete(block_data[6])
                self.canvas.delete(block_data[8])
                if block_data[2] == "Static content":
                    self.canvas.delete(block_data[4])
                if block_data[2] in ["Input by", "Dropdown option", "Static content"]:
                    self.canvas.delete(block_data[10])
            elif block_data[2] == "Launch Web:":
                self.canvas.delete(block_data[4])
            elif block_data[2] == "Delay:":
                self.canvas.delete(block_data[4])
                self.canvas.delete(block_data[5])
            elif block_data[2] == "Navigate":
                self.canvas.delete(block_data[4])
            elif block_data[2] == "Database":
                self.canvas.delete(block_data[4])
                self.canvas.delete(block_data[6])
                self.canvas.delete(block_data[8])
                self.canvas.delete(block_data[10])
                self.canvas.delete(block_data[12])
            elif block_data[2] == "Retrieve data":
                self.canvas.delete(block_data[4])
                self.canvas.delete(block_data[6])
                self.canvas.delete(block_data[8])
                self.canvas.delete(block_data[10])
                self.canvas.delete(block_data[12])
                self.canvas.delete(block_data[14])
                self.canvas.delete(block_data[16])
                self.canvas.delete(block_data[18])
            self.blocks.remove(block_data)
            self.selected_block_data = None

            # Mark changes
            self.change_callback()

    def on_entry_focus(self, event):
        self.deselect_block()

    def start_testing(self, webdriver_choice, driver=None):
        try:
            sorted_blocks = sorted(self.blocks, key=lambda block: self.canvas.coords(block[0])[1])

            if driver is None:
                if webdriver_choice == "Chrome":
                    driver = webdriver.Chrome()
                elif webdriver_choice == "Edge":
                    driver = webdriver.Edge()
                elif webdriver_choice == "Firefox":
                    driver = webdriver.Firefox()
                else:
                    raise ValueError(f"Unsupported WebDriver choice: {webdriver_choice}")

            self.driver = driver

            element_finders = {
                "NAME": By.NAME,
                "ID": By.ID,
                "CLASS_NAME": By.CLASS_NAME,
                "CSS_SELECTOR": By.CSS_SELECTOR,
                "LINK_TEXT": By.LINK_TEXT,
                "PARTIAL_LINK_TEXT": By.PARTIAL_LINK_TEXT,
                "TAG_NAME": By.TAG_NAME,
                "XPATH": By.XPATH,
            }

            for block in sorted_blocks:
                action_text = block[2]
                if action_text in ["Input by", "Dropdown option"]:
                    element_type = block[5].get()
                    element_identifier = block[7].get()
                    query = block[9].get()
                    if element_type and element_identifier and query:
                        by_type = element_finders.get(element_type)
                        if by_type:
                            if action_text == "Input by":
                                element = self.driver.find_element(by_type, element_identifier)
                                element.clear()
                                element.send_keys(query)
                                self.log_with_timestamp(f"Input '{query}' into element found by {element_type} with identifier '{element_identifier}'.")
                            else:
                                element = Select(self.driver.find_element(by_type, element_identifier))
                                element.select_by_visible_text(query)
                                self.log_with_timestamp(f"Input '{query}' into element found by {element_type} with identifier '{element_identifier}'.")
                elif action_text in ["Click", "Radio button"]:
                    element_type = block[5].get()
                    element_identifier = block[7].get()
                    if element_type and element_identifier:
                        by_type = element_finders.get(element_type)
                        if by_type:
                            element = self.driver.find_element(by_type, element_identifier)
                            element.click()
                            if action_text == "Click":
                                self.log_with_timestamp(f"Clicked on element found by {element_type} with identifier '{element_identifier}'.")
                            else:
                                self.log_with_timestamp(f"Clicked radio button found by {element_type} with identifier '{element_identifier}'.")
                elif action_text == "Static content":
                    content_type = block[3].get()
                    element_type = block[5].get()
                    element_identifier = block[7].get()
                    query = block[9].get()

                    by_type = element_finders.get(element_type)
                    if by_type:
                        element = self.driver.find_element(by_type, element_identifier)
                        if content_type == "Text":
                            if element.text == query:
                                self.log_with_timestamp(f"Verified text '{query}' in element found by {element_type} with identifier '{element_identifier}'.")
                            else:
                                self.log_with_timestamp(f"Text mismatch: expected '{query}', found '{element.text}' in element found by {element_type} with identifier '{element_identifier}'.")
                        elif content_type in ["Image", "Icon"]:
                            if element.get_attribute('src') == query:
                                self.log_with_timestamp(f"Verified {content_type.lower()} '{query}' in element found by {element_type} with identifier '{element_identifier}'.")
                            else:
                                self.log_with_timestamp(f"Source mismatch: expected '{query}', found '{element.get_attribute('src')}' in element found by {element_type} with identifier '{element_identifier}'.")
                elif action_text == "Launch Web:":
                    url = block[3].get()
                    if url:
                        self.driver.get(url)
                        self.log_with_timestamp(f"Launched {url}.")
                elif action_text == "Navigate":
                    navigation_action = block[3].get()
                    if navigation_action == "Backward":
                        self.driver.back()
                        self.log_with_timestamp("Navigated backward.")
                    elif navigation_action == "Forward":
                        self.driver.forward()
                        self.log_with_timestamp("Navigated forward.")
                    elif navigation_action == "Refresh":
                        self.driver.refresh()
                        self.log_with_timestamp("Page refreshed.")
                elif action_text == "Delay:":
                    delay = block[3].get()
                    if delay:
                        time.sleep(int(delay))
                        self.log_with_timestamp(f"Delay for {delay} seconds.")
                elif action_text == "Database":
                    db_type = block[3].get()
                    host = block[5].get()
                    dbname = block[7].get()
                    username = block[9].get()
                    password = block[11].get()
                    connection_details = {
                        "host": host,
                        "dbname": dbname,
                        "username": username,
                        "password": password
                    }
                    self.connect_to_database(db_type, connection_details)
                elif action_text == "Retrieve data":
                    # Check conditions for optional parameters
                    col3_needed = not (block[17].get() == "" or block[17].get() == "Value 3" or block[11].get() == "" or block[11].get() == "WHERE column3")
                    col2_needed = not (block[15].get() == "" or block[15].get() == "Value 2" or block[9].get() == "" or block[9].get() == "WHERE column2")
                    
                    # Construct SQL query based on needed columns
                    if col3_needed and col2_needed:
                        sql_query = f"SELECT {block[3].get()} FROM {block[5].get()} WHERE {block[7].get()} = %s AND {block[9].get()} = %s AND {block[11].get()} = %s"
                        parameters = (block[13].get(), block[15].get(), block[17].get())
                    elif col2_needed:
                        sql_query = f"SELECT {block[3].get()} FROM {block[5].get()} WHERE {block[7].get()} = %s AND {block[9].get()} = %s"
                        parameters = (block[13].get(), block[15].get())
                    else:
                        sql_query = f"SELECT {block[3].get()} FROM {block[5].get()} WHERE {block[7].get()} = %s"
                        parameters = (block[13].get(),)
                    
                    self.retrieve_data(sql_query, parameters)
        except Exception as e:
            self.log_with_timestamp(f"Error during testing: {e}")

    def connect_to_database(self, db_type, connection_details):
        self.log_with_timestamp(f"Connecting to {db_type} with details: {connection_details}")
        try:
            if db_type == "MySQL":
                self.connection = pymysql.connect(
                    host=connection_details['host'],
                    user=connection_details['username'],
                    password=connection_details['password'],
                    database=connection_details['dbname']
                )
            elif db_type == "PostgreSQL":
                self.connection = psycopg2.connect(
                    host=connection_details['host'],
                    user=connection_details['username'],
                    password=connection_details['password'],
                    dbname=connection_details['dbname']
                )
            elif db_type == "Microsoft SQL Server":
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={connection_details['host']};"
                    f"DATABASE={connection_details['dbname']};"
                    f"UID={connection_details['username']};"
                    f"PWD={connection_details['password']}"
                )
                self.connection = pyodbc.connect(connection_string)
            self.log_with_timestamp(f"Connected to {db_type} database.")
        except Exception as e:
            self.log_with_timestamp(f"Failed to connect to {db_type} database: {e}")

    def retrieve_data(self, sql_query, parameters):
        try:
            print(f"Executing SQL Query: {sql_query} with parameters: {parameters}")  # Debug print statement
            with self.connection.cursor() as cursor:
                cursor.execute(sql_query, parameters)
                result = cursor.fetchone()  # or use cursor.fetchall() if you expect multiple rows
                if result:
                    self.log_with_timestamp("Data retrieved successfully.")
                else:
                    self.log_with_timestamp("No data found.")
        except Exception as e:
            self.log_with_timestamp(f"Failed to retrieve data: {e}")
            print(f"Error: {e}")  # Debug print statement

    def log_with_timestamp(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.logger(f"[{timestamp}] {message}")

    def save_test_case(self, filename):
        test_case_data = []
        for block in self.blocks:
            block_data = {
                'type': block[2],
                'coords': self.canvas.coords(block[0]),
                'values': []
            }
            if block[2] in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if block[2] == "Static content":
                    block_data['values'] = [block[3].get(), block[5].get(), block[7].get(), block[9].get()]
                else:
                    block_data['values'] = [block[5].get(), block[7].get()]
                    if block[2] in ["Input by", "Dropdown option"]:
                        block_data['values'].append(block[9].get())
            elif block[2] == "Launch Web:":
                block_data['values'] = [block[3].get()]
            elif block[2] == "Delay:":
                block_data['values'] = [block[3].get()]
            elif block[2] == "Navigate":
                block_data['values'] = [block[3].get()]
            elif block[2] == "Database":
                block_data['values'] = [
                    block[3].get(),  # Database type
                    block[5].get(),  # Host
                    block[7].get(),  # Database Name
                    block[9].get(),  # Username
                    block[11].get()  # Password
                ]
            elif block[2] == "Retrieve data":
                block_data['values'] = [
                    block[3].get(), 
                    block[5].get(), 
                    block[7].get(),
                    block[9].get(),
                    block[11].get(),
                    block[13].get(),
                    block[15].get(),
                    block[17].get()  
                ]
            test_case_data.append(block_data)

        with open(filename, 'w') as file:
            json.dump(test_case_data, file)

        # Mark changes
        self.change_callback()

    def load_test_case(self, filename):
        self.clear_canvas()
        with open(filename, 'r') as file:
            test_case_data = json.load(file)

        for block_data in test_case_data:
            x, y, _, _ = block_data['coords']
            text = block_data['type']
            self.create_draggable_block(x, y, text)
            new_block = self.blocks[-1]

            if text in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if text == "Static content":
                    new_block[3].set(block_data['values'][0])
                    new_block[5].set(block_data['values'][1])
                    new_block[7].delete(0, tk.END)
                    new_block[7].insert(0, block_data['values'][2])
                    new_block[9].delete(0, tk.END)
                    new_block[9].insert(0, block_data['values'][3])
                else:
                    new_block[5].set(block_data['values'][0])
                    new_block[7].delete(0, tk.END)
                    new_block[7].insert(0, block_data['values'][1])
                    if text in ["Input by", "Dropdown option"]:
                        new_block[9].delete(0, tk.END)
                        new_block[9].insert(0, block_data['values'][2])
            elif text == "Launch Web:":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0])
            elif text == "Delay:":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0])
            elif text == "Navigate":
                new_block[3].set(block_data['values'][0])
            elif text == "Database":
                new_block[3].set(block_data['values'][0])  # Database type
                new_block[5].delete(0, tk.END)  # Host
                new_block[5].insert(0, block_data['values'][1])
                new_block[7].delete(0, tk.END)  # Database Name
                new_block[7].insert(0, block_data['values'][2])
                new_block[9].delete(0, tk.END)  # Username
                new_block[9].insert(0, block_data['values'][3])
                new_block[11].delete(0, tk.END)  # Password
                new_block[11].insert(0, block_data['values'][4])
            elif text == "Retrieve data":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0]) 
                new_block[5].delete(0, tk.END)  # Host
                new_block[5].insert(0, block_data['values'][1])
                new_block[7].delete(0, tk.END)  # Database Name
                new_block[7].insert(0, block_data['values'][2])
                new_block[9].delete(0, tk.END)  # Username
                new_block[9].insert(0, block_data['values'][3])
                new_block[11].delete(0, tk.END)  # Password
                new_block[11].insert(0, block_data['values'][4])
                new_block[13].delete(0, tk.END)  # Database Name
                new_block[13].insert(0, block_data['values'][5])
                new_block[15].delete(0, tk.END)  # Username
                new_block[15].insert(0, block_data['values'][6])
                new_block[17].delete(0, tk.END)  # Password
                new_block[17].insert(0, block_data['values'][7])
        # Mark changes
        self.change_callback()

    def load_combined_test_cases(self, combined_test_cases):
        self.clear_canvas()
        for block_data in combined_test_cases:
            x, y, _, _ = block_data['coords']
            text = block_data['type']
            self.create_draggable_block(x, y, text)
            new_block = self.blocks[-1]

            if text in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if text == "Static content":
                    new_block[3].set(block_data['values'][0])
                    new_block[5].set(block_data['values'][1])
                    new_block[7].delete(0, tk.END)
                    new_block[7].insert(0, block_data['values'][2])
                    new_block[9].delete(0, tk.END)
                    new_block[9].insert(0, block_data['values'][3])
                else:
                    new_block[5].set(block_data['values'][0])
                    new_block[7].delete(0, tk.END)
                    new_block[7].insert(0, block_data['values'][1])
                    if text in ["Input by", "Dropdown option"]:
                        new_block[9].delete(0, tk.END)
                        new_block[9].insert(0, block_data['values'][2])
            elif text == "Launch Web:":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0])
            elif text == "Delay:":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0])
            elif text == "Navigate":
                new_block[3].set(block_data['values'][0])
            elif text == "Database":
                new_block[3].set(block_data['values'][0])  # Database type
                new_block[5].delete(0, tk.END)  # Host
                new_block[5].insert(0, block_data['values'][1])
                new_block[7].delete(0, tk.END)  # Database Name
                new_block[7].insert(0, block_data['values'][2])
                new_block[9].delete(0, tk.END)  # Username
                new_block[9].insert(0, block_data['values'][3])
                new_block[11].delete(0, tk.END)  # Password
                new_block[11].insert(0, block_data['values'][4])
            elif text == "Retrieve data":
                new_block[3].delete(0, tk.END)
                new_block[3].insert(0, block_data['values'][0]) 
                new_block[5].delete(0, tk.END)  # Host
                new_block[5].insert(0, block_data['values'][1])
                new_block[7].delete(0, tk.END)  # Database Name
                new_block[7].insert(0, block_data['values'][2])
                new_block[9].delete(0, tk.END)  # Username
                new_block[9].insert(0, block_data['values'][3])
                new_block[11].delete(0, tk.END)  # Password
                new_block[11].insert(0, block_data['values'][4])
                new_block[13].delete(0, tk.END)  # Database Name
                new_block[13].insert(0, block_data['values'][5])
                new_block[15].delete(0, tk.END)  # Username
                new_block[15].insert(0, block_data['values'][6])
                new_block[17].delete(0, tk.END)  # Password
                new_block[17].insert(0, block_data['values'][7])
        # Mark changes
        self.change_callback()

    def run_test_case(self, test_case_file, webdriver_choice, driver=None):
        self.load_test_case(test_case_file)
        self.start_testing(webdriver_choice, driver)

    def run_test_suite(self, test_cases, webdriver_choice):
        if not test_cases:
            return

        driver = None
        if webdriver_choice == "Chrome":
            driver = webdriver.Chrome()
        elif webdriver_choice == "Edge":
            driver = webdriver.Edge()
        elif webdriver_choice == "Firefox":
            driver = webdriver.Firefox()
        else:
            raise ValueError(f"Unsupported WebDriver choice: {webdriver_choice}")

        for test_case in test_cases:
            self.run_test_case(test_case, webdriver_choice, driver)

        driver.quit()

    def clear_canvas(self):
        for block in self.blocks:
            self.canvas.delete(block[0])
            self.canvas.delete(block[1])
            if block[2] in ["Input by", "Click", "Dropdown option", "Radio button", "Static content"]:
                if block[2] == "Static content":
                    self.canvas.delete(block[4])
                self.canvas.delete(block[6])
                self.canvas.delete(block[8])
                if block[2] in ["Input by", "Dropdown option", "Static content"]:
                    self.canvas.delete(block[10])
            elif block[2] == "Launch Web:":
                self.canvas.delete(block[4])
            elif block[2] == "Delay:":
                self.canvas.delete(block[4])
                self.canvas.delete(block[5])
            elif block[2] == "Navigate":
                self.canvas.delete(block[4])
            elif block[2] == "Database":
                self.canvas.delete(block[4])
                self.canvas.delete(block[6])
                self.canvas.delete(block[8])
                self.canvas.delete(block[10])
                self.canvas.delete(block[12])
            elif block[2] == "Retrieve data":
                self.canvas.delete(block[4])
                self.canvas.delete(block[6])
                self.canvas.delete(block[8])
                self.canvas.delete(block[10])
                self.canvas.delete(block[12])
                self.canvas.delete(block[14])
                self.canvas.delete(block[16])
                self.canvas.delete(block[18])
        self.blocks.clear()

        # Mark changes
        self.change_callback()
