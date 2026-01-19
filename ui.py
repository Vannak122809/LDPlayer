import customtkinter as ctk
import os
import ctypes
import sys
from tkinter import filedialog, messagebox, Menu
from ld_controller import LDPlayerController
from automation_manager import AutomationManager
from PIL import Image

# Replicate the dark theme from the image
THEME_COLOR = "#1a1b26" # Deep dark blue background
SIDEBAR_COLOR = "#13141f"
ACCENT_COLOR = "#3b8ed0" # Blue accent
TEXT_COLOR = "#ffffff"
GRID_HEADER_COLOR = "#1f202e"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LDManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Bob Prime Clone - LDPlayer Manager")
        self.geometry("1100x700")
        self.configure(fg_color=THEME_COLOR) # Set main background
        
        self.controller = LDPlayerController()
        self.automation = AutomationManager(self.controller, self.update_timer)
        
        self.setup_ui()
        
        # Initial check
        if not self.controller.console_path:
            self.after(500, self.warn_path)
        else:
            self.refresh_instances()

    def update_timer(self, time_str):
        self.timer_label.configure(text=time_str)

    def warn_path(self):
         messagebox.showwarning("Setup", "Please set LDPlayer dnconsole.exe path via 'Browse' button.")

    def start_automation_click(self):
        # 1. Get Selected Devices from Active Tab
        selected_indices = []
        for child in self.active_device_list.winfo_children():
            try:
                # Structure: Frame -> [Checkbox, Label(Index), Label(Name)]
                checkbox = child.winfo_children()[0]
                if checkbox.get() == 1:
                    index_label = child.winfo_children()[1]
                    selected_indices.append(index_label.cget("text"))
            except:
                pass
        
        if not selected_indices:
            messagebox.showwarning("Warning", "No devices selected in Active tab!")
            return

        # 2. Get Max Active Count & Delays
        max_active = self.active_limit_combo.get()
        
        interval_delay = 40
        if self.chk_interval.get() == 1:
            try: interval_delay = int(self.delay_interval_entry.get())
            except: pass
                
        boot_delay = 60
        try: boot_delay = int(self.delay_boot_entry.get())
        except: pass

        # 3. Gather Active Task Settings
        task_settings = {}
        if hasattr(self, 'active_settings'):
            for key, widget in self.active_settings.items():
                try:
                    # Check if it's a CheckBox or Entry
                    if isinstance(widget, ctk.CTkCheckBox):
                        task_settings[key] = widget.get() == 1
                    elif isinstance(widget, ctk.CTkEntry):
                        task_settings[key] = widget.get()
                except:
                    pass

        # Check if "Enable Active" is allowed (optional logic)
        # enable_active = self.chk_enable_active.get() == 1

        self.automation.start_automation(selected_indices, max_active, interval_delay, boot_delay, task_settings)

    def stop_automation_click(self):
        self.automation.stop_automation()
        self.update_timer("00:00:00")

    def setup_ui(self):
        # ==================== MAIN LAYOUT ====================
        # Grid: Left Sidebar (weight 0), Right Content (weight 1)
        self.grid_columnconfigure(0, weight=0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. LEFT SIDEBAR
        self.left_panel = ctk.CTkFrame(self, fg_color=SIDEBAR_COLOR, corner_radius=0, width=300)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        self.setup_left_panel()
        
        # 2. RIGHT MAIN CONTENT
        self.right_panel = ctk.CTkFrame(self, fg_color=THEME_COLOR, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.setup_right_panel()

    def setup_left_panel(self):
        # 1.1 Header / Timer Area
        self.timer_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.timer_frame.pack(fill="x", padx=10, pady=10)
        
        # Play/Stop Buttons (Simulated with icons/text)
        self.btn_start_script = ctk.CTkButton(self.timer_frame, text="▶", width=40, height=40, font=("Arial", 20), fg_color=ACCENT_COLOR, command=self.start_automation_click)
        self.btn_start_script.pack(side="left", padx=5)
        
        self.btn_stop_script = ctk.CTkButton(self.timer_frame, text="■", width=40, height=40, font=("Arial", 20), fg_color="#c0392b", command=self.stop_automation_click)
        self.btn_stop_script.pack(side="left", padx=5)
        
        # Timer
        self.timer_label = ctk.CTkLabel(self.timer_frame, text="00:00:00", font=("Consolas", 32, "bold"), text_color="#a0a0a0")
        self.timer_label.pack(side="right", padx=10)
        
        # 1.2 "Active Devices" Header
        self.lbl_active = ctk.CTkLabel(self.left_panel, text="Active Devices", font=("Arial", 14), text_color="gray", anchor="w")
        self.lbl_active.pack(fill="x", padx=15, pady=(20, 5))
        
        # 1.3 Active Devices List (Placeholder for now)
        # Headers: No. LD Name ID Activity
        headers_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=30)
        headers_frame.pack(fill="x", padx=10)
        ctk.CTkLabel(headers_frame, text="No.", width=30, anchor="w", font=("Arial", 11)).pack(side="left")
        ctk.CTkLabel(headers_frame, text="LD Name", width=80, anchor="w", font=("Arial", 11)).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="ID", width=30, anchor="w", font=("Arial", 11)).pack(side="left")
        ctk.CTkLabel(headers_frame, text="Activity", width=50, anchor="w", font=("Arial", 11)).pack(side="left", padx=5)
        
        self.active_scroll = ctk.CTkScrollableFrame(self.left_panel, fg_color="#181924")
        self.active_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1.4 Footer Buttons
        footer = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=40)
        footer.pack(fill="x", side="bottom", padx=10, pady=10)
        
        ctk.CTkButton(footer, text="API", width=60, height=25, fg_color="#2b2d3e", border_width=1, border_color="gray").pack(side="left", padx=2)
        ctk.CTkButton(footer, text="LD Group", width=70, height=25, fg_color="#3b8ed0").pack(side="left", padx=2)
        ctk.CTkButton(footer, text="Logs", width=60, height=25, fg_color="#2b2d3e", border_width=1, border_color="gray").pack(side="left", padx=2)

    def setup_right_panel(self):
        # 2.1 Tab View
        self.tabview = ctk.CTkTabview(self.right_panel, width=700, height=500, fg_color=THEME_COLOR, segmented_button_fg_color=SIDEBAR_COLOR, segmented_button_selected_color=ACCENT_COLOR, segmented_button_unselected_color=SIDEBAR_COLOR)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=0)
        
        self.tab_devices = self.tabview.add("Devices")
        self.tab_active = self.tabview.add("Active")
        self.tab_schedule = self.tabview.add("Schedule Post")
        self.tab_manage = self.tabview.add("Manage")
        
        self.tabview.set("Devices")
        
        # Build "Devices" Tab Content
        self.build_devices_tab(self.tab_devices)
        
        # Build "Active" Tab Content
        self.build_active_tab(self.tab_active)

    def build_active_tab(self, parent):
        parent.grid_columnconfigure(0, weight=1) # Settings
        parent.grid_columnconfigure(1, weight=1) # Device List
        parent.grid_rowconfigure(0, weight=1)
        
        # Split into Left (Settings) and Right (Device List)
        # Revert to standard frame for "Old UI" feel, mimicking screenshot exactly
        settings_frame = ctk.CTkFrame(parent, fg_color="transparent")
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        device_select_frame = ctk.CTkFrame(parent, fg_color="transparent")
        device_select_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # ================= LEFT: Active Facebook Account Settings =================
        self.active_settings = {}
        
        ctk.CTkLabel(settings_frame, text="Active Facebook Account", font=("Arial", 14), text_color="gray", anchor="w").pack(fill="x", pady=(0, 10))
        
        # Helper to create rows easily
        def add_setting_row(parent_frame, key, label_text, widget_type="checkbox", val1=None, val2=None, suffix1=None, suffix2=None, extra_widget=None):
            row = ctk.CTkFrame(parent_frame, fg_color="transparent", height=30)
            row.pack(fill="x", pady=2)
            
            # Main Widget (Checkbox or Label)
            if widget_type == "checkbox":
                chk = ctk.CTkCheckBox(row, text=label_text, width=160, font=("Arial", 12))
                chk.pack(side="left")
                self.active_settings[key] = chk
            else:
                ctk.CTkLabel(row, text=label_text, width=160, anchor="w", font=("Arial", 12)).pack(side="left")
            
            # Value 1
            if val1 is not None:
                e1 = ctk.CTkEntry(row, width=50, placeholder_text=str(val1))
                e1.pack(side="left", padx=5)
                self.active_settings[f"{key}_val1"] = e1
                
            # Suffix 1 or Text "To"
            if suffix1:
                 ctk.CTkLabel(row, text=suffix1, font=("Arial", 11)).pack(side="left", padx=2)
            
            # Value 2
            if val2 is not None:
                e2 = ctk.CTkEntry(row, width=50, placeholder_text=str(val2))
                e2.pack(side="left", padx=5)
                self.active_settings[f"{key}_val2"] = e2
                
             # Suffix 2
            if suffix2:
                 ctk.CTkLabel(row, text=suffix2, font=("Arial", 11)).pack(side="left", padx=2)
                 
            # Any extra custom widget passed
            if extra_widget:
                extra_widget(row)
                
            return row

        # Row 1: Check Notification
        row_notif = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row_notif.pack(fill="x", pady=2)
        chk_n = ctk.CTkCheckBox(row_notif, text="Check Notification", width=160)
        chk_n.pack(side="left")
        self.active_settings["check_notification"] = chk_n
        
        ctk.CTkEntry(row_notif, width=50).pack(side="left", padx=5)
        
        chk_l = ctk.CTkCheckBox(row_notif, text="Check Primary Location")
        chk_l.pack(side="right", padx=10)
        self.active_settings["check_location"] = chk_l

        # Scrolling
        add_setting_row(settings_frame, "scroll_news", "Scroll New Feed", val1="2", suffix1="To", val2="3", suffix2="Minutes")
        add_setting_row(settings_frame, "scroll_video", "Scroll Videos", val1="2", suffix1="To", val2="3", suffix2="Minutes")
        add_setting_row(settings_frame, "scroll_reels", "Scroll Reels", val1="1", suffix1="To", val2="2", suffix2="Minutes")
        
        # Friends
        add_setting_row(settings_frame, "confirm_friends", "Confirm Friends", val1="3", suffix1="Friends")
        add_setting_row(settings_frame, "add_friends", "Add Friends", val1="1", suffix1="Friends")
        
        # Posts
        add_setting_row(settings_frame, "react_post", "Reaction on Post", val1="2")
        
        # Post Check-in (Custom row for complexity)
        row_chk = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row_chk.pack(fill="x", pady=2)
        chk_ci = ctk.CTkCheckBox(row_chk, text="Create Post Check-In", width=160)
        chk_ci.pack(side="left")
        self.active_settings["create_post"] = chk_ci
        
        ctk.CTkEntry(row_chk, width=50, placeholder_text="1").pack(side="left", padx=5)
        
        chk_ph = ctk.CTkCheckBox(row_chk, text="Photo")
        chk_ph.pack(side="left", padx=5)
        self.active_settings["post_photo"] = chk_ph
        
        ctk.CTkButton(row_chk, text="...", width=30).pack(side="left", padx=2)
        ctk.CTkEntry(row_chk, width=120, placeholder_text="tures/Saved Pictures").pack(side="left", padx=2)
        
        # Comments
        row_com = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row_com.pack(fill="x", pady=2)
        chk_cm = ctk.CTkCheckBox(row_com, text="Comments on Post", width=160)
        chk_cm.pack(side="left")
        self.active_settings["comments"] = chk_cm
        
        ctk.CTkEntry(row_com, width=50, placeholder_text="1").pack(side="left", padx=5)
        ctk.CTkEntry(row_com, width=200, placeholder_text="😍, Lovely, I love it").pack(side="left", padx=5)
        
        # Loop Settings
        add_setting_row(settings_frame, "loop_delay", "Delay before next loop", val1="20", suffix1="To", val2="25", suffix2="Seconds")
        add_setting_row(settings_frame, "loop_count", "Number of Active Loop", widget_type="label", val1="1", suffix1="Times")
        add_setting_row(settings_frame, "active_time", "Active Between", val1="17:15", suffix1="To", val2="3:00")
        
        # Shutdown / Install
        row_shut = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row_shut.pack(fill="x", pady=2)
        chk_sd = ctk.CTkCheckBox(row_shut, text="Shutdown PC when Finish", width=200)
        chk_sd.pack(side="left")
        self.active_settings["shutdown"] = chk_sd
        
        ctk.CTkCheckBox(row_shut, text="Install APK").pack(side="left", padx=5)
        ctk.CTkEntry(row_shut, width=120, placeholder_text="/Desktop/old.apk").pack(side="left", padx=2)
        ctk.CTkButton(row_shut, text="...", width=30).pack(side="left", padx=2)
        
        # App Number
        row_app = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row_app.pack(fill="x", pady=(10, 2))
        ctk.CTkLabel(row_app, text="Facebook App number").pack(side="left")
        ctk.CTkEntry(row_app, width=40, placeholder_text="1").pack(side="left", padx=5)
        ctk.CTkCheckBox(row_app, text="Auto Switch Profile").pack(side="left", padx=10)
        ctk.CTkLabel(row_app, text="ID-0", text_color="#3b8ed0").pack(side="left", padx=10)
        
        # Headers for Profile Table (Fake table)
        tbl_head = ctk.CTkFrame(settings_frame, fg_color="transparent")
        tbl_head.pack(fill="x", pady=5)
        ctk.CTkLabel(tbl_head, text="Facebook App", width=100, anchor="w").pack(side="left", padx=20)
        ctk.CTkLabel(tbl_head, text="Account Name", width=150, anchor="w").pack(side="left", padx=20)
        
        # Top Controls
        r_top = ctk.CTkFrame(device_select_frame, fg_color="transparent")
        r_top.pack(fill="x", pady=0)
        self.chk_enable_active = ctk.CTkCheckBox(r_top, text="Enable Active")
        self.chk_enable_active.pack(side="left")
        self.chk_active_select_all = ctk.CTkCheckBox(r_top, text="Select All", command=self.toggle_select_active_all)
        self.chk_active_select_all.pack(side="right")
        
        # Headers
        r_head = ctk.CTkFrame(device_select_frame, fg_color="#2b2d3e", height=30)
        r_head.pack(fill="x", pady=5)
        ctk.CTkLabel(r_head, text="ID", width=30).pack(side="left", padx=5)
        ctk.CTkLabel(r_head, text="LD Name", width=150, anchor="w").pack(side="left", padx=5)
        
        # List
        self.active_device_list = ctk.CTkScrollableFrame(device_select_frame)
        self.active_device_list.pack(fill="both", expand=True)
        
        # Footer
        r_foot = ctk.CTkFrame(device_select_frame, fg_color="transparent")
        r_foot.pack(fill="x", pady=5)
        self.lbl_active_selected = ctk.CTkLabel(r_foot, text="0 Selected")
        self.lbl_active_selected.pack(side="left")
        
        # Populate List (Do this LAST so lbl_active_selected exists)
        self.refresh_active_tab_list()

    def toggle_select_active_all(self):
        state = self.chk_active_select_all.get()
        for child in self.active_device_list.winfo_children():
            try:
                chk = child.winfo_children()[0]
                if state == 1:
                    chk.select()
                else:
                    chk.deselect()
            except:
                pass
        self.update_active_selection_count()

    def update_active_selection_count(self):
        count = 0
        for child in self.active_device_list.winfo_children():
             try:
                chk = child.winfo_children()[0]
                if chk.get() == 1: count += 1
             except: pass
        self.lbl_active_selected.configure(text=f"{count} Selected")

    def refresh_active_tab_list(self):
        # Save current selections? (Optional, skipping for simplicity)
        for widget in self.active_device_list.winfo_children():
            widget.destroy()
            
        try:
            instances = self.controller.list_instances()
            for inst in instances:
                row = ctk.CTkFrame(self.active_device_list, fg_color="transparent")
                row.pack(fill="x", pady=1)
                
                chk = ctk.CTkCheckBox(row, text="", width=20, command=self.update_active_selection_count)
                chk.pack(side="left", padx=5)
                
                ctk.CTkLabel(row, text=inst['index'], width=30).pack(side="left")
                ctk.CTkLabel(row, text=inst['name'], anchor="w").pack(side="left", padx=10)
                
        except:
             pass
        self.update_active_selection_count()
    def build_devices_tab(self, parent):
        # Need a grid layout inside: Main list on left, Settings sidebar on right
        parent.grid_columnconfigure(0, weight=1) # Main list
        parent.grid_columnconfigure(1, weight=0, minsize=250) # Settings Sidebar
        parent.grid_rowconfigure(1, weight=1) # List area matches expansion
        
        # --- Top Control Rows ---
        top_ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        top_ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Paths
        path_frame = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        path_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(path_frame, text="LDPlayer Location", width=100, anchor="w").grid(row=0, column=0, padx=5)
        self.path_entry = ctk.CTkEntry(path_frame, width=400)
        self.path_entry.insert(0, self.controller.console_path or "")
        self.path_entry.grid(row=0, column=1, padx=5)
        ctk.CTkButton(path_frame, text="Browse", width=60, command=self.browse_ld).grid(row=0, column=2, padx=5)
        
        ctk.CTkLabel(path_frame, text="System Location", width=100, anchor="w").grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkEntry(path_frame, width=400).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(path_frame, text="Browse", width=60).grid(row=1, column=2, padx=5, pady=5)
        
        # LD Setup Row
        setup_frame = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        setup_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(setup_frame, text="Number of active LD").pack(side="left", padx=5)
        self.active_limit_combo = ctk.CTkComboBox(setup_frame, values=["1", "2", "3", "4", "5"], width=60)
        self.active_limit_combo.pack(side="left")
        
        ctk.CTkLabel(setup_frame, text="Wait after LD Boot").pack(side="left", padx=(15,5))
        self.delay_boot_entry = ctk.CTkEntry(setup_frame, width=50, placeholder_text="60")
        self.delay_boot_entry.pack(side="left")
        
        self.chk_interval = ctk.CTkCheckBox(setup_frame, text="Between LD Start")
        self.chk_interval.pack(side="left", padx=(15,5))
        self.delay_interval_entry = ctk.CTkEntry(setup_frame, width=50, placeholder_text="40")
        self.delay_interval_entry.pack(side="left")
        
        # --- Left: Devices List ---
        list_container = ctk.CTkFrame(parent, fg_color="transparent")
        list_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # List Header
        lh = ctk.CTkFrame(list_container, height=30, fg_color="#2b2d3e")
        lh.pack(fill="x")
        ctk.CTkLabel(lh, text="ID", width=40).pack(side="left", padx=5)
        ctk.CTkLabel(lh, text="LD Name", width=150).pack(side="left", padx=5)
        ctk.CTkLabel(lh, text="Status", width=60).pack(side="left", padx=5)
        ctk.CTkLabel(lh, text="Actions", width=100).pack(side="left", padx=5)
        
        # Scrollable List
        self.device_list_scroll = ctk.CTkScrollableFrame(list_container)
        self.device_list_scroll.pack(fill="both", expand=True)

        # --- Right: LDPlayer Setting Sidebar ---
        settings_bar = ctk.CTkFrame(parent, fg_color="#181924", width=250)
        settings_bar.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(settings_bar, text="LDplayer Setting ⚙", font=("Arial", 12, "bold")).pack(pady=10, anchor="w", padx=10)
        
        self.chk_internet = ctk.CTkCheckBox(settings_bar, text="Check Internet")
        self.chk_internet.pack(pady=5, anchor="w", padx=10)
        
        self.chk_auto_config = ctk.CTkCheckBox(settings_bar, text="Auto Apply Configuration")
        self.chk_auto_config.select()
        self.chk_auto_config.pack(pady=5, anchor="w", padx=10)
        
        # CPU/RAM
        prop_frame = ctk.CTkFrame(settings_bar, fg_color="transparent")
        prop_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(prop_frame, text="CPU").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_cpu = ctk.CTkComboBox(prop_frame, values=["1 cores", "2 cores", "4 cores"], width=120)
        self.combo_cpu.grid(row=0, column=1, padx=5, pady=2)
        self.combo_cpu.set("2 cores")
        
        ctk.CTkLabel(prop_frame, text="RAM").grid(row=1, column=0, padx=5, sticky="w")
        self.combo_ram = ctk.CTkComboBox(prop_frame, values=["1024M", "2048M", "4096M", "8192M"], width=120)
        self.combo_ram.grid(row=1, column=1, padx=5, pady=2)
        self.combo_ram.set("2048M")
        
        ctk.CTkLabel(prop_frame, text="Res").grid(row=2, column=0, padx=5, sticky="w")
        self.combo_res = ctk.CTkComboBox(prop_frame, values=["540,960,240", "720,1280,320", "1080,1920,480"], width=120)
        self.combo_res.grid(row=2, column=1, padx=5, pady=2)
        self.combo_res.set("720,1280,320")
        
        # Apply Button
        ctk.CTkButton(settings_bar, text="Apply Config to All", height=25, command=self.apply_config).pack(pady=10,padx=10)
        
        # --- Batch Actions ---
        ctk.CTkLabel(settings_bar, text="Actions", font=("Arial", 12, "bold")).pack(pady=(10,5), anchor="w", padx=10)
        
        act_frame = ctk.CTkFrame(settings_bar, fg_color="transparent")
        act_frame.pack(fill="x", padx=5)
        
        self.btn_batch_start = ctk.CTkButton(act_frame, text="Start Sel", width=100, fg_color="#27ae60", height=25, command=lambda: self.batch_action("start"))
        self.btn_batch_start.grid(row=0, column=0, padx=2, pady=2)
        
        self.btn_batch_stop = ctk.CTkButton(act_frame, text="Stop Sel", width=100, fg_color="#c0392b", height=25, command=lambda: self.batch_action("stop"))
        self.btn_batch_stop.grid(row=0, column=1, padx=2, pady=2)
        
        self.btn_add_new = ctk.CTkButton(act_frame, text="+ New", width=100, fg_color="#3b8ed0", height=25, command=self.add_instance_dialog)
        self.btn_add_new.grid(row=1, column=0, padx=2, pady=2)
        
        self.btn_batch_del = ctk.CTkButton(act_frame, text="Delete Sel", width=100, fg_color="#555", height=25, command=lambda: self.batch_action("delete"))
        self.btn_batch_del.grid(row=1, column=1, padx=2, pady=2)
        
        # Auto Arrange has a command now
        self.chk_arrange = ctk.CTkCheckBox(settings_bar, text="Auto Arrange LDPlayer", command=self.auto_arrange_click)
        self.chk_arrange.pack(pady=10, anchor="w", padx=10)
        
        ctk.CTkCheckBox(settings_bar, text="Auto fit Screen").pack(pady=5, anchor="w", padx=10)
        
        # Refresh Button
        ctk.CTkButton(settings_bar, text="Refresh List", fg_color="green", command=self.refresh_instances).pack(pady=20, padx=10, side="bottom")


    def browse_ld(self):
        path = filedialog.askopenfilename(filetypes=[("dnconsole.exe", "dnconsole.exe")])
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            self.controller.console_path = path
            self.refresh_instances()
            
    def refresh_instances(self):
        # Clear main list
        for widget in self.device_list_scroll.winfo_children():
            widget.destroy()
        
        # Clear active list
        for widget in self.active_scroll.winfo_children():
            widget.destroy()
            
        try:
            instances = self.controller.list_instances()
            for inst in instances:
                # Add to main list
                self.create_device_row(inst)
                
                # Add to active list if running
                if inst['running']:
                    self.create_active_row(inst)
            
            # Also refresh the Active Tab list (right side)
            self.refresh_active_tab_list()

        except Exception as e:
            print(e)
            
    def create_active_row(self, inst):
        row = ctk.CTkFrame(self.active_scroll, fg_color="transparent", height=30)
        row.pack(fill="x", pady=2)
        
        # No. (just using index for now, or could be a counter)
        ctk.CTkLabel(row, text=inst['index'], width=30, anchor="w", font=("Arial", 11)).pack(side="left", padx=0)
        # LD Name
        # Truncate if too long
        name = inst['name']
        if len(name) > 12: name = name[:10] + ".."
        ctk.CTkLabel(row, text=name, width=80, anchor="w", font=("Arial", 11)).pack(side="left", padx=5)
        # ID
        ctk.CTkLabel(row, text=inst['index'], width=30, anchor="w", font=("Arial", 11)).pack(side="left", padx=0)
        # Activity
        ctk.CTkLabel(row, text="Running", width=50, anchor="w", text_color="#2ecc71", font=("Arial", 11)).pack(side="left", padx=5)

    def create_device_row(self, inst):
        row = ctk.CTkFrame(self.device_list_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # Checkbox for selection
        chk = ctk.CTkCheckBox(row, text="", width=20)
        chk.pack(side="left", padx=5)
        
        ctk.CTkLabel(row, text=inst['index'], width=40).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=inst['name'], width=150, anchor="w").pack(side="left", padx=5)
        
        status_col = "#2ecc71" if inst['running'] else "#e74c3c"
        ctk.CTkLabel(row, text="●", text_color=status_col, width=20).pack(side="left")
        ctk.CTkLabel(row, text="Running" if inst['running'] else "Stopped", width=50, font=("Arial", 10)).pack(side="left")
        
        # Actions
        if inst['running']:
            ctk.CTkButton(row, text="Stop", width=50, height=20, fg_color="#c0392b", command=lambda i=inst['index']: self.toggle_instance(i, False)).pack(side="left", padx=5)
        else:
            ctk.CTkButton(row, text="Start", width=50, height=20, fg_color="#27ae60", command=lambda i=inst['index']: self.toggle_instance(i, True)).pack(side="left", padx=5)

    def toggle_instance(self, index, start):
        if start:
            self.controller.start_instance(index)
        else:
            self.controller.stop_instance(index)
        self.after(500, self.refresh_instances)

    def apply_config(self):
        # 1. Gather Selected Instances
        selected_indices = []
        for child in self.device_list_scroll.winfo_children():
            # Structure: Frame -> [Checkbox, Label(Index), ...]
            try:
                chk = child.winfo_children()[0]
                if isinstance(chk, ctk.CTkCheckBox) and chk.get() == 1:
                    idx_lbl = child.winfo_children()[1]
                    selected_indices.append(idx_lbl.cget("text"))
            except:
                pass
        
        target_indices = selected_indices
        confirm_msg = f"Apply config (CPU/RAM/Res) to {len(target_indices)} selected instances?"
        
        if not target_indices:
            if not messagebox.askyesno("Confirm", "No devices selected. Apply to ALL devices?"):
                return
            # Get all
            target_indices = [inst['index'] for inst in self.controller.list_instances()]
            confirm_msg = "Apply config to ALL instances?"
        
        cpu_str = self.combo_cpu.get().split()[0]
        ram_str = self.combo_ram.get().replace("M", "")
        res_str = self.combo_res.get()
        
        if messagebox.askyesno("Apply Config", f"{confirm_msg}\nCPU: {cpu_str}, RAM: {ram_str}M, Res: {res_str}"):
            for idx in target_indices:
                self.controller.modify_instance(idx, int(cpu_str), int(ram_str), res_str)
            messagebox.showinfo("Done", "Configuration applied.")
            
    def batch_action(self, action):
        selected_indices = []
        for child in self.device_list_scroll.winfo_children():
            try:
                chk = child.winfo_children()[0]
                if isinstance(chk, ctk.CTkCheckBox) and chk.get() == 1:
                    idx_lbl = child.winfo_children()[1]
                    selected_indices.append(idx_lbl.cget("text"))
            except:
                pass
                
        if not selected_indices:
            messagebox.showwarning("Batch Action", "No devices selected.")
            return

        if action == "start":
            for idx in selected_indices:
                self.controller.start_instance(idx)
        elif action == "stop":
            for idx in selected_indices:
                self.controller.stop_instance(idx)
        elif action == "delete":
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_indices)} instances?"):
                 for idx in selected_indices:
                    self.controller.remove_instance(idx)
        
        self.after(500, self.refresh_instances)
        self.after(2000, self.refresh_instances)

    def add_instance_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter name for new instance:", title="New Instance")
        name = dialog.get_input()
        if name:
            self.controller.create_instance(name)
            self.after(500, self.refresh_instances)

    def auto_arrange_click(self):
        self.controller.sort_windows()

if __name__ == "__main__":
    app = LDManagerApp()
    app.mainloop()
