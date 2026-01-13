import flet as ft
import datetime
import logging
import random
import time
import threading

# Set up logging to catch and print errors
logging.basicConfig(level=logging.INFO)

# --- Color Palette ---
BG_COLOR = "#121212"
CARD_COLOR = "#1E1E1E"
ACCENT_MOVEMENT = "#00E676"  # Neon Green for Movement
ACCENT_SLEEP = "#651FFF"     # Deep Purple for Sleep
ACCENT_NAP = "#FF9100"       # Orange for Naps
ACCENT_WARNING = "#FF5252"   # Red for Schedule Warning
TEXT_COLOR = "#FFFFFF"

# --- Utility Colors ---
C_TRANSPARENT = "#00000000"
C_WHITE10 = "#1AFFFFFF"      
C_GREY_400 = "#BDBDBD"
C_GREY_700 = "#616161"
C_RED_400 = "#EF5350"
C_WARNING = "#FF8A80"        # Light Red for warnings

# --- Sleep Gradient (Calm/Dark Purple-Blue) ---
SLEEP_GRADIENT_COLORS = ["#0f0c29",  "#302b63", "#24243e"]

# --- Movement Gradient (Pastel Turquoise/Blue-Greenish) for enegrising mood ---
MOVEMENT_GRADIENT_COLORS = ["#FF00AA69", "#FF006970"] 

# --- Dashboard Gradient (Dark Sea Blue) for calming opening colors ---
DASHBOARD_GRADIENT_COLORS = ["#191186B9", "#1F21AD86", "#090F7AA7"]

GLASS_COLOR = "#25252550"

class HabitApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.timer_running = False  # ADD THIS LINE HERE
        # ... the rest of your init variables ...
        # ... your existing state variables ...

        # FIX: Define these here so they exist as soon as the app starts
        self.meditation_timer_text = ft.Text("10:00", size=40, weight="bold", color=ACCENT_MOVEMENT)
        self.breath_status = ft.Text("Ready to breathe?", size=20, weight="bold")
        self.breathing_line = ft.Container(
            width=20, height=20, bgcolor=ACCENT_MOVEMENT, border_radius=20,
            alignment=ft.alignment.bottom_center
        )
      
      
        self.setup_page()
        
        # --- State ---
        self.sleep_hours = 7.0
        self.sleep_quality = 3
        self.nap_hours = 0.0  
        
        # Sleep Schedule State
        self.bedtime = None   
        self.wakeup = None    
        
        # Sleep History UI State
        self.show_sleep_history = False
        
        self.categories = [
            "Socialising", "Exercise", "Mental Exercise", 
            "Hygiene", "Nutrition", "Chores", "Others"
        ]
        
        self.movement_tasks = [
            {"label": "Morning Stretch", "done": False, "category": "Exercise"},
            {"label": "30 Min Walk", "done": False, "category": "Exercise"},
            {"label": "Gym Workout", "done": False, "category": "Exercise"},
            {"label": "Drink 2L Water", "done": False, "category": "Nutrition"},
            {"label": "Read 10 Pages", "done": False, "category": "Mental Exercise"},
            {"label": "Lunch with a Friend", "done": False, "category": "Socialising"},
        ]
        self.quote = "Small steps every day lead to giant leaps over time."

        # --- UI Components ---
        self.content_area = ft.Container(
            expand=True,
            padding=30,
        )
        
        # Movement Inputs
        self.new_task_input = ft.TextField(
            hint_text="e.g., Yoga Session", 
            border_color=ACCENT_MOVEMENT,
            cursor_color=ACCENT_MOVEMENT,
            text_style=ft.TextStyle(color=TEXT_COLOR)
        )
        
        # Category dropdown
        self.new_task_category = ft.Dropdown(
            options=[ft.dropdown.Option(c) for c in self.categories],
            width=200,
            hint_text="Category",
            border_color=C_GREY_700,
            text_style=ft.TextStyle(color=TEXT_COLOR)
        )

        # Time Pickers for Sleep
        self.bedtime_picker = ft.TimePicker(
            confirm_text="Set Bedtime",
            error_invalid_text="Time invalid",
            help_text="Select your bedtime",
            on_change=self.handle_bedtime_change
        )
        self.wakeup_picker = ft.TimePicker(
            confirm_text="Set Wake Up",
            error_invalid_text="Time invalid",
            help_text="Select wake up time",
            on_change=self.handle_wakeup_change
        )

        self.rail = self.create_navigation()
        self.initialize_ui()

    def setup_page(self):
        self.page.title = "Zenith | Habit Tracker"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BG_COLOR
        self.page.padding = 0
        self.page.update()

    def create_navigation(self):
        return ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon="dashboard_outlined", 
                    selected_icon="dashboard", 
                    label="Dashboard"
                ),
                ft.NavigationRailDestination(
                    icon="directions_run_outlined", 
                    selected_icon="directions_run", 
                    label="Movement"
                ),
                ft.NavigationRailDestination(
                    icon="bedtime_outlined", 
                    selected_icon="bedtime", 
                    label="Sleep"
                ),
                ft.NavigationRailDestination(
                   icon="self_improvement", 
                   selected_icon="self_improvement", 
                   label="Mindfulness"
                ),
            ],
            on_change=self.navigate,
            bgcolor=CARD_COLOR,
        )

    def initialize_ui(self):
        self.add_task_dialog = ft.AlertDialog(
            title=ft.Text("Add New Habit"),
            content=ft.Column([
                self.new_task_input,
                ft.Container(height=10),
                self.new_task_category
            ], height=120),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog, style=ft.ButtonStyle(color=C_GREY_400)),
                ft.TextButton("Add", on_click=self.add_task, style=ft.ButtonStyle(color=ACCENT_MOVEMENT)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=CARD_COLOR,
        )
        
        # Overlay components
        self.page.overlay.append(self.add_task_dialog)
        self.page.overlay.append(self.bedtime_picker)
        self.page.overlay.append(self.wakeup_picker)

        self.content_area.content = self.view_dashboard()
        
        self.page.add(
            ft.Row(
                [
                    self.rail,
                    ft.VerticalDivider(width=1, color=C_WHITE10),
                    self.content_area,
                ],
                expand=True,
                spacing=0
            )
        )
        self.page.update()

    # --- LOGIC ---

    def calculate_sleep_duration(self):
        """Calculates sleep hours based on bedtime and wakeup time."""
        if self.bedtime and self.wakeup:
            # Combine with dummy date to perform arithmetic
            today = datetime.date.today()
            b_dt = datetime.datetime.combine(today, self.bedtime)
            w_dt = datetime.datetime.combine(today, self.wakeup)
            
            # If wakeup is earlier than bedtime, assume it's the next day
            if w_dt <= b_dt:
                w_dt += datetime.timedelta(days=1)
                
            diff = w_dt - b_dt
            total_hours = diff.total_seconds() / 3600
            
            # Update state, clamped to slider range (0-14h)
            self.sleep_hours = min(max(total_hours, 0), 14)

    def handle_bedtime_change(self, e):
        self.bedtime = self.bedtime_picker.value
        self.calculate_sleep_duration()
        self.refresh_current_view()

    def handle_wakeup_change(self, e):
        self.wakeup = self.wakeup_picker.value
        self.calculate_sleep_duration()
        self.refresh_current_view()

    def open_bedtime_picker(self, e):
        self.bedtime_picker.open = True
        self.page.update()

    def open_wakeup_picker(self, e):
        self.wakeup_picker.open = True
        self.page.update()

    def open_add_task_dialog(self, e):
        self.new_task_input.value = "" 
        self.new_task_category.value = None
        self.add_task_dialog.open = True
        self.page.update()

    def close_dialog(self, e):
        self.add_task_dialog.open = False
        self.page.update()

    def add_task(self, e):
        if self.new_task_input.value:
            cat = self.new_task_category.value if self.new_task_category.value else "Others"
            self.movement_tasks.append({
                "label": self.new_task_input.value, 
                "done": False,
                "category": cat
            })
            self.refresh_current_view()
            self.add_task_dialog.open = False
            self.page.update()

    def delete_task(self, task_label):
        self.movement_tasks = [t for t in self.movement_tasks if t["label"] != task_label]
        self.refresh_current_view()

    def toggle_task(self, task_label, value):
        for task in self.movement_tasks:
            if task["label"] == task_label:
                task["done"] = value
        
        self.page.update()
        if self.rail.selected_index == 1:
            self.refresh_current_view()

    def toggle_sleep_history(self, e):
        self.show_sleep_history = not self.show_sleep_history
        self.refresh_current_view()

    def navigate(self, e):
        try:
            idx = e.control.selected_index
            
            # --- Background Switching ---
            if idx == 0: # Dashboard (Deep Slate Blue --> general calming and focused colours)
                self.content_area.gradient = ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=DASHBOARD_GRADIENT_COLORS
                )
                self.content_area.bgcolor = None

            elif idx == 1: # Movement Tab (Pastel/Blue-Green Gradient --> energizing)
                self.content_area.gradient = ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=MOVEMENT_GRADIENT_COLORS
                )
                self.content_area.bgcolor = None
            
            elif idx == 2: # Sleep Tab (Calm/Dark Gradient)
                self.content_area.gradient = ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=SLEEP_GRADIENT_COLORS
                )
                self.content_area.bgcolor = None
            
            else: # Mindfulness (Standard Dark Background)
                self.content_area.gradient = None
                self.content_area.bgcolor = BG_COLOR

            # Reset history view when navigating to other tabs
            if idx != 2:
                self.show_sleep_history = False

            # Switch Content
            self.refresh_current_view()
            
        except Exception as ex:
            print(f"Error navigating: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Navigation Error: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def refresh_current_view(self):
        idx = self.rail.selected_index
        self.content_area.content = ft.Container() 
        self.page.update()
        
        try:
            if idx == 0:
                self.content_area.content = self.view_dashboard()
            elif idx == 1:
                self.content_area.content = self.view_movement()
            elif idx == 2:
                self.content_area.content = self.view_sleep()
            elif idx == 3:
                self.content_area.content = self.view_mindfulness()
        except Exception as e:
            print(f"Error loading view: {e}")
            self.content_area.content = ft.Text(f"Error: {e}", color="red")
        
        self.page.update()

    # --- VIEWS ---

    def view_dashboard(self):
        done_tasks = sum(1 for t in self.movement_tasks if t["done"])
        total_tasks = len(self.movement_tasks)
        progress = done_tasks / total_tasks if total_tasks > 0 else 0
        
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %d %B")

        # Different greetings depending on time of day
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon"
        elif 17 <= hour < 21:
            greeting = "Good Evening"
        else:
            greeting = "Good Night"

        bed_str = self.bedtime.strftime("%H:%M") if self.bedtime else "..."
        wake_str = self.wakeup.strftime("%H:%M") if self.wakeup else "..."
        sleep_subtitle = None
        if self.bedtime or self.wakeup:
            sleep_subtitle = f"({bed_str} - {wake_str})"

        priorities = [t for t in self.movement_tasks if not t["done"]][:3]
        priority_list = ft.Column(spacing=5)
        
        if not priorities:
             priority_list.controls.append(ft.Text("All caught up!", color=ACCENT_MOVEMENT, italic=True, size=12))
        else:
            for task in priorities:
                priority_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon("radio_button_unchecked", size=12, color=ACCENT_MOVEMENT),
                            ft.Text(task["label"], size=13)
                        ]),
                        padding=8,
                        bgcolor=C_WHITE10,
                        border_radius=8
                    )
                )

        # Structure inside the glass box
        dashboard_content = ft.Column([
            ft.Row([
                self.create_stat_card("Sleep", f"{int(self.sleep_hours)}h", "bedtime", ACCENT_SLEEP, subtitle=sleep_subtitle),
                self.create_stat_card("Focus", f"{int(progress*100)}%", "check_circle", ACCENT_MOVEMENT),
            ], alignment=ft.MainAxisAlignment.START, spacing=20),
            
            ft.Divider(height=20, color=C_TRANSPARENT),

            ft.Row(
                [
                    ft.Column([
                        ft.Text("Daily Progress", size=20, weight="bold"),
                        ft.ProgressBar(
                            value=progress, color=ACCENT_MOVEMENT, bgcolor=CARD_COLOR, height=10, border_radius=5
                        ),
                        ft.Text(f"{done_tasks} of {total_tasks} habits completed", size=12, color=C_GREY_400),
                        ft.Container(height=20),
                        ft.Container(
                            bgcolor=CARD_COLOR,
                            padding=20,
                            border_radius=15,
                            content=ft.Column([
                                ft.Icon("format_quote", color=C_GREY_700, size=30),
                                ft.Text(self.quote, size=16, italic=True, text_align=ft.TextAlign.CENTER),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=400
                        )
                    ], expand=2),
                    ft.Container(width=40),
                    ft.Column([
                        ft.Text("Up Next", size=18, weight="bold"),
                        ft.Container(
                            bgcolor=CARD_COLOR, padding=15, border_radius=15, content=priority_list, width=280
                        ),
                    ], expand=1)
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # Main glass container wrapping the dashboard content
        main_card = ft.Container(
            bgcolor=GLASS_COLOR,
            padding=30,
            border_radius=20,
            border=ft.border.all(1, C_WHITE10),
            content=dashboard_content,
            expand=True
        )

        return ft.Column(
            [
                ft.Text(f"{greeting}!", size=16, color=C_GREY_400),
                ft.Text(f"{date_str}", size=36, weight="bold", color=TEXT_COLOR),
                ft.Divider(color=C_TRANSPARENT, height=10),
                main_card
            ],
            expand=True
        )

    def view_movement(self):
        # Header Row
        header_row = ft.Row([
            ft.Row([
                ft.Icon("directions_run", size=32, color="white"),
                ft.Text("Habits & Movement", size=32, weight="bold"),
            ]),
            # Elevated Button for text + icon and custom blending color
            ft.ElevatedButton(
                text="Add Exercise",
                icon="add",
                bgcolor="#4DFFFFFF", #somewhat transparent for glass box effect
                color="white", # Text and Icon color
                on_click=self.open_add_task_dialog,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(horizontal=15, vertical=10)
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        unfinished = [t for t in self.movement_tasks if not t['done']]
        finished = [t for t in self.movement_tasks if t['done']]

        # contrast so writing can be seen in the glass box
        def create_task_container(task):
            label = task["label"]
            cat = task.get("category", "General")
            return ft.Container(
                # Use white to create a distinct layer on top of the main glass card
                bgcolor=C_WHITE10, 
                padding=10, 
                border_radius=10,
                border=ft.border.all(1, C_WHITE10),
                content=ft.Row([
                    ft.Row([
                        ft.Checkbox(
                            value=task["done"], 
                            active_color=ACCENT_MOVEMENT, 
                            check_color=BG_COLOR,
                            on_change=lambda e, l=label: self.toggle_task(l, e.control.value)
                        ),
                        ft.Column([
                            ft.Text(label, size=16, weight="w500"),
                            ft.Text(cat, size=12, color=C_GREY_400)
                        ], spacing=0)
                    ]),
                    ft.IconButton(icon="delete_outline", icon_color=C_RED_400, 
                                on_click=lambda e, l=label: self.delete_task(l))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        # lists for To do and Done tasks
        left_controls = [create_task_container(t) for t in unfinished]
        right_controls = [create_task_container(t) for t in finished]

        split_layout = ft.Row(
            controls=[
                # Left Side: To Do
                ft.Column(
                    controls=[ft.Text("To Do", weight="bold", color="white")] + left_controls, 
                    expand=True, 
                    spacing=10
                ),
                # Right Side: Done
                ft.Column(
                    controls=[ft.Text("Done", weight="bold", color="white")] + right_controls, 
                    expand=True, 
                    spacing=10
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            expand=True # Make the row inside expand
        )
        
        # Wrapped in a Glass Box, similar to the Sleep View
        # Added expand=True to main_card to ensure it fills the available vertical space
        main_card = ft.Container(
            bgcolor=GLASS_COLOR, 
            padding=25,
            border_radius=20,
            border=ft.border.all(1, C_WHITE10),
            content=split_layout,
            expand=True # EXPAND THIS CONTAINER
        )

        return ft.Column(
            [
                header_row,
                ft.Text("Customize your daily tracking here.", color="white70"),
                ft.Divider(height=20, color=C_TRANSPARENT),
                main_card
            ],
            
            expand=True 
        )

    def view_sleep_history(self):
        # Example Data for History
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        week_data = [6.5, 7.0, 5.5, 8.0, 7.5, 9.0, 6.0] 
        
        view_2days = ft.Column([
            ft.Text("Yesterday", weight="bold", size=16),
            ft.Container(
                bgcolor=C_WHITE10, padding=15, border_radius=10,
                content=ft.Row([
                    ft.Column([
                        ft.Text("7.5h Sleep", color="white", weight="bold"),
                        ft.Text("Quality: 4/5 (Good)", color=C_GREY_400, size=12),
                    ]),
                    ft.Column([
                        ft.Text("23:00 - 06:30", color=C_GREY_400, size=12),
                        ft.Text("Nap: 20m", color=ACCENT_NAP, size=12),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ),
            ft.Container(height=10),
            ft.Text("2 Days Ago", weight="bold", size=16),
            ft.Container(
                bgcolor=C_WHITE10, padding=15, border_radius=10,
                content=ft.Row([
                    ft.Column([
                        ft.Text("6.0h Sleep", color="white", weight="bold"),
                        ft.Text("Quality: 2/5 (Poor)", color=C_GREY_400, size=12),
                    ]),
                    ft.Column([
                        ft.Text("01:00 - 07:00", color=C_GREY_400, size=12),
                        ft.Text("No Nap", color=C_GREY_700, size=12),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ),
        ])

        chart_bars = []
        for day, hours in zip(days_of_week, week_data):
            bar_height = (hours / 10) * 100
            bar_color = ACCENT_SLEEP if hours >= 7 else C_WARNING if hours < 6 else "#90CAF9"
            
            chart_bars.append(
                ft.Column([
                    ft.Container(height=100-bar_height), 
                    ft.Container(
                        width=20, 
                        height=bar_height, 
                        bgcolor=bar_color, 
                        border_radius=ft.border_radius.only(top_left=5, top_right=5),
                        tooltip=f"{hours} hours"
                    ),
                    ft.Text(day, size=10, color=C_GREY_400)
                ], alignment=ft.MainAxisAlignment.END, spacing=5)
            )
        
        view_week = ft.Container(
            padding=20, bgcolor=C_WHITE10, border_radius=15,
            content=ft.Column([
                ft.Text("Last 7 Days (Hours)", weight="bold"),
                ft.Container(height=10),
                ft.Row(chart_bars, alignment=ft.MainAxisAlignment.SPACE_EVENLY, height=150)
            ])
        )

        view_month = ft.Row([
            ft.Container(
                bgcolor=C_WHITE10, padding=20, border_radius=15, expand=1,
                content=ft.Column([
                    ft.Icon("bedtime", color=ACCENT_SLEEP, size=30),
                    ft.Text("Avg Sleep", size=12, color=C_GREY_400),
                    ft.Text("7.2h", size=24, weight="bold")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            ft.Container(width=10),
            ft.Container(
                bgcolor=C_WHITE10, padding=20, border_radius=15, expand=1,
                content=ft.Column([
                    ft.Icon("star", color="#B39DDB", size=30),
                    ft.Text("Avg Quality", size=12, color=C_GREY_400),
                    ft.Text("3.8/5", size=24, weight="bold")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ])

        return ft.Column([
            ft.Container(height=5),
            ft.Row([
                ft.Icon("history", size=30, color="#B39DDB"),
                ft.Text("Sleep History", size=28, weight="bold", color="white"),
                ft.IconButton(
                    icon="close", 
                    icon_color=C_RED_400, 
                    tooltip="Back to Tracker",
                    on_click=self.toggle_sleep_history
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color=C_TRANSPARENT, height=10),
            
            ft.Tabs( # different History Views
                selected_index=0,
                animation_duration=300,
                indicator_color=ACCENT_SLEEP,
                label_color=TEXT_COLOR,
                unselected_label_color=C_GREY_400,
                divider_color=C_TRANSPARENT,
                tabs=[
                    ft.Tab(
                        text="Past 2 Days",
                        content=ft.Container(content=view_2days, padding=ft.padding.only(top=20))
                    ),
                    ft.Tab(
                        text="Week",
                        content=ft.Container(content=view_week, padding=ft.padding.only(top=20))
                    ),
                    ft.Tab(
                        text="Month",
                        content=ft.Container(content=view_month, padding=ft.padding.only(top=20))
                    ),
                ],
                expand=1,
            )
        ])

    def view_sleep(self):
        if self.show_sleep_history:
            return self.view_sleep_history()

        hours_label = ft.Text(f"{self.sleep_hours} Hours", size=24, weight="bold")
        def on_hours_change(e):
            self.sleep_hours = e.control.value
            hours_label.value = f"{int(self.sleep_hours)} Hours" if self.sleep_hours % 1 == 0 else f"{self.sleep_hours:.1f} Hours"
            hours_label.update()

        quality_map = { # For user to choose sleep quality.
            1: "Horrible (Insomnia)",
            2: "Poor",
            3: "Average",
            4: "Good",
            5: "Well Rested"
        }
        quality_text = ft.Text(quality_map[int(self.sleep_quality)], size=16, color="#B39DDB", weight="bold") 

        def on_quality_change(e):
            self.sleep_quality = int(e.control.value)
            quality_text.value = quality_map[self.sleep_quality]
            quality_text.update()

        nap_minutes = int(self.nap_hours * 60)
        nap_label = ft.Text(f"{nap_minutes} min" if nap_minutes > 0 else "No Nap", size=16, weight="bold")
        
        initial_nap_msg = ""
        initial_nap_col = C_GREY_400
        if nap_minutes > 30:
            initial_nap_msg = "⚠️ Short naps are better. Long naps (>30m) cause inertia."
            initial_nap_col = C_WARNING
        elif nap_minutes >= 15:
            initial_nap_msg = "Power naps (15-30m) boost energy."
            initial_nap_col = ACCENT_NAP
        elif nap_minutes > 0:
             initial_nap_msg = "Too short for benefit. Aim for 15-30m."
             initial_nap_col = C_GREY_400

        nap_feedback = ft.Text(initial_nap_msg, size=12, color=initial_nap_col)

        def on_nap_change(e):
            self.nap_hours = e.control.value
            mins = int(self.nap_hours * 60)
            nap_label.value = f"{mins} min" if mins > 0 else "No Nap"
            
            # Warnings for nap duration (Too short, Too Long, and optimal)
            if mins > 30:
                nap_feedback.value = "⚠️ Short naps are better. Long naps (>30m) cause inertia."
                nap_feedback.color = C_WARNING
            elif mins >= 15:
                nap_feedback.value = "Power naps (15-30m) boost energy."
                nap_feedback.color = ACCENT_NAP
            elif mins > 0:
                nap_feedback.value = "Too short for benefit. Aim for 15-30m."
                nap_feedback.color = C_GREY_400
            else:
                nap_feedback.value = ""
            
            nap_label.update()
            nap_feedback.update()

        bed_str = self.bedtime.strftime("%H:%M") if self.bedtime else "--:--"
        wake_str = self.wakeup.strftime("%H:%M") if self.wakeup else "--:--"
        
        schedule_feedback = ft.Container()
        
        if self.bedtime and self.wakeup:
            is_late_sleep = 2 <= self.bedtime.hour < 6
            is_late_wake = self.wakeup.hour >= 13
            
            #Warning for risky sleep schedule --> effects on mood
            if is_late_sleep and is_late_wake:
                schedule_feedback = ft.Container(
                    bgcolor=C_WARNING,
                    padding=10,
                    border_radius=10,
                    content=ft.Row([
                        ft.Icon("warning_amber", color="white", size=20),
                        ft.Column([
                            ft.Text("Risky Sleep Schedule", weight="bold", color="black", size=13),
                            ft.Text("Sleeping late (>2:00) and waking late (>13:00) increases risk of depressive moods.", color="black", size=11, width=450),
                            ft.Text("Go to sleep earlier and wake up earlier for mood boosts.", color="black", size=11, width=350)
                        ], spacing=1)
                    ])
                )
            else:
                schedule_feedback = ft.Container(height=0)

        return ft.Column(
            [
                ft.Container(height=5),
                ft.Row([
                    ft.Row([
                        ft.Icon("nights_stay", size=30, color="#B39DDB"),
                        ft.Text("Rest & Recovery", size=28, weight="bold", color="white"),
                    ]),
                    ft.IconButton(
                        icon="history", 
                        icon_color="white", 
                        tooltip="View History",
                        on_click=self.toggle_sleep_history
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text("Prioritize your mental clarity through quality sleep.", color="#B0BEC5", size=12),
                
                ft.Divider(height=15, color=C_TRANSPARENT),

                ft.Container(
                    bgcolor=GLASS_COLOR, 
                    padding=25,
                    border_radius=20,
                    border=ft.border.all(1, C_WHITE10),
                    content=ft.Column([
                        
                        ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Icon("access_time", color="#90CAF9", size=16),
                                    ft.Text("Sleep Duration", size=16, weight="w500")
                                ]),
                                ft.Container(height=5),
                                ft.Slider(
                                    min=0, max=12, divisions=24, 
                                    value=self.sleep_hours, 
                                    active_color="#90CAF9", 
                                    thumb_color="white",
                                    on_change=on_hours_change
                                ),
                                ft.Row([hours_label], alignment=ft.MainAxisAlignment.CENTER),
                            ], expand=True), 

                            ft.Container(width=20), 

                            ft.Column([
                                ft.Row([
                                    ft.Icon("schedule", color=ACCENT_WARNING, size=16),
                                    ft.Text("Schedule", size=14, weight="w500")
                                ]),
                                ft.Container(height=5),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Bedtime", size=10, color=C_GREY_400),
                                        ft.ElevatedButton(
                                            text=bed_str,
                                            icon="bed",
                                            bgcolor=C_WHITE10,
                                            color="white",
                                            height=30,
                                            style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=11)),
                                            on_click=self.open_bedtime_picker
                                        )
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                    
                                    ft.Container(width=5),

                                    ft.Column([
                                        ft.Text("Wake Up", size=10, color=C_GREY_400),
                                        ft.ElevatedButton(
                                            text=wake_str,
                                            icon="wb_sunny",
                                            bgcolor=C_WHITE10,
                                            color="white",
                                            height=30,
                                            style=ft.ButtonStyle(padding=5, text_style=ft.TextStyle(size=11)),
                                            on_click=self.open_wakeup_picker
                                        )
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ]),
                            ]),
                        ], vertical_alignment=ft.CrossAxisAlignment.START, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        ft.Container(height=5),
                        schedule_feedback,

                        ft.Divider(height=20, color=C_WHITE10),

                        ft.Row([
                            ft.Icon("star_outline", color="#B39DDB", size=16),
                            ft.Text("Quality of Sleep", size=16, weight="w500"),
                            ft.Container(width=5),
                            
                            # Information on different options for sleep quality
                            ft.IconButton(
                                icon="info_outline", 
                                icon_color=C_GREY_400,
                                icon_size=18,
                                tooltip=(
                                    "1: Horrible - Barely slept at all.\n"
                                    "2: Poor - Restless, woke up frequently.\n"
                                    "3: Average - Okay sleep, usual routine.\n"
                                    "4: Good - Restful, mostly uninterrupted.\n"
                                    "5: Well Rested - Didn't wake up once, feeling extremely energized."
                                )
                            )
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.Column([
                            ft.Slider(
                                min=1, max=5, divisions=4, 
                                value=self.sleep_quality,
                                active_color="#B39DDB", 
                                thumb_color="white",
                                on_change=on_quality_change
                            ),
                            ft.Row([
                                ft.Text("1", size=10, color=C_GREY_400),
                                ft.Row([
                                    ft.Text("Feeling: ", color=C_GREY_400, size=12),
                                    quality_text
                                ]),
                                ft.Text("5", size=10, color=C_GREY_400),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=0),

                        ft.Divider(height=20, color=C_WHITE10),

                        ft.Row([
                            ft.Icon("wb_sunny_outlined", color=ACCENT_NAP, size=16),
                            ft.Text("Daytime Nap", size=16, weight="w500")
                        ]),
                        ft.Container(height=5),
                        ft.Slider(
                            min=0, max=3, divisions=36, 
                            value=self.nap_hours, 
                            active_color=ACCENT_NAP, 
                            thumb_color="white",
                            on_change=on_nap_change
                        ),
                        ft.Column([
                            ft.Row([
                                nap_label,
                                ft.Container(width=10),
                                nap_feedback
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),

                    ])
                ),
                
                ft.Container(height=10),
                
                ft.Container( # informative quote on how important sleep is
                    padding=10,
                    content=ft.Text(
                        "“Sleep is the best meditation.” — Dalai Lama",
                        italic=True,
                        color=C_WHITE10, 
                        text_align=ft.TextAlign.CENTER,
                        size=12
                    ),
                    alignment=ft.alignment.center
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def view_mindfulness(self):
        # Calm Color Palette
        OCEAN_DEEP = "#0F2027"
        OCEAN_LIGHT = "#3985A5"

        return ft.Container(
            expand=True,
            padding=30,
            # This adds the calming "Ocean" background
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[OCEAN_DEEP, OCEAN_LIGHT],
            ),
            content=ft.Column([
                ft.Text("Mindfulness Sanctuary", size=32, weight="bold", color="white"),
                ft.Tabs(
                    selected_index=0,
                    tabs=[
                        ft.Tab(text="Meditation", content=self.ui_meditation_tab()),
                        ft.Tab(text="Breathing Exercise", content=self.ui_breathing_tab()),
                        ft.Tab(text="Emergency Help", content=self.ui_help_tab()),
                    ],
                    expand=1
                )
            ], scroll=ft.ScrollMode.AUTO)
        )

    def ui_meditation_tab(self):
        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Guided Meditation", size=20, weight="bold"),
                ft.Container(
                    bgcolor=CARD_COLOR, padding=30, border_radius=15,
                    content=ft.Column([
                        ft.Icon("spa", size=50, color=ACCENT_MOVEMENT),
                        self.meditation_timer_text,
                        ft.Row([
                            # FIXED: Added 'lambda' to pass the minutes to the timer
                            ft.ElevatedButton("5 Min", on_click=lambda e: self.start_meditation_timer(e, 300)),
                            ft.ElevatedButton("10 Min", on_click=lambda e: self.start_meditation_timer(e, 600)),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
            ])
        )
    
    def animate_breathing(self, e):
        def run():
            try:
                # --- PHASE 1: INHALE (4s) ---
                self.breathing_circle.scale = 1.0 
                self.page.update()
                
                self.breath_status.color = "#00E676" # Hardcoded Green
                self.breathing_circle.bgcolor = "#00E676"
                self.breathing_circle.scale = 2.5  
                self.breathing_circle.opacity = 0.8
                self.breathing_circle.animate_scale = ft.Animation(4000, "decelerate")
                
                for i in range(4, 0, -1):
                    self.breath_status.value = f"INHALE... {i}"
                    self.page.update()
                    time.sleep(1)

                # --- PHASE 2: HOLD (7s) ---
                self.breath_status.color = "#FF5252" # Hardcoded Red
                self.breathing_circle.bgcolor = "#FF5252"
                self.page.update()
                
                for i in range(7, 0, -1):
                    self.breath_status.value = f"HOLD... {i}"
                    self.page.update()
                    time.sleep(1)

                # --- PHASE 3: RELEASE (8s) ---
                # This transition is now forced with hardcoded Blue
                self.breath_status.color = "#448AFF" 
                self.breathing_circle.bgcolor = "#448AFF"
                self.breathing_circle.scale = 1.0  
                self.breathing_circle.opacity = 0.2
                self.breathing_circle.animate_scale = ft.Animation(8000, "accelerate")
                
                # We update the page BEFORE the loop to ensure the color changes immediately
                self.page.update() 

                for i in range(8, 0, -1):
                    self.breath_status.value = f"RELEASE... {i}"
                    self.page.update()
                    time.sleep(1)

                # --- RESET ---
                self.breath_status.value = "Ready to breathe?"
                self.breath_status.color = "white"
                self.breathing_circle.bgcolor = "#00E676"
                self.page.update()
                
            except Exception as ex:
                # This will tell you EXACTLY why it got stuck in the terminal
                logging.error(f"ANIMATION CRASHED: {ex}")

        threading.Thread(target=run, daemon=True).start()
        


    def ui_breathing_tab(self):
        self.breathing_circle = ft.Container(
            width=100, height=100,
            bgcolor=ACCENT_MOVEMENT,
            border_radius=50,
            opacity=0.2,
            scale=1.0,
            # Critical for smooth movement and color shifting
            animate_scale=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
            animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
            shadow=ft.BoxShadow(
                blur_radius=50,
                spread_radius=-10,
                color=ft.Colors.with_opacity(0.3, ACCENT_MOVEMENT), # Fixed Capital 'C'
            ),
        )

        return ft.Container(
            padding=40,
            content=ft.Column([
                ft.Text("4-7-8 Rhythm", size=28, weight="bold"),
                ft.Container(height=40),
                ft.Container(
                    height=300, width=400,
                    alignment=ft.alignment.center,
                    content=ft.Stack([
                        # Outer Guide Ring
                        ft.Container(
                            width=260, height=260,
                            border=ft.border.all(1, C_WHITE10),
                            border_radius=130,
                        ),
                        self.breathing_circle
                    ], alignment=ft.alignment.center)
                ),
                self.breath_status,
                ft.Container(height=40),
                ft.ElevatedButton(
                    "BEGIN SESSION", 
                    on_click=self.animate_breathing,
                    bgcolor=C_WHITE10,
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20))
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def ui_help_tab(self):
        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("You are not alone.", size=24, weight="bold", color=C_RED_400),
                ft.Container(height=10),
                # FIXED: Using string "phone" to prevent flet icon errors
                self.create_help_hotline("Line", "804", "Available 24/7", "phone"),
                self.create_help_hotline("Live Chat Support", "+490741741", "Free support", "sms"),
                self.create_help_hotline("Email", "info@zenith.de", "Free support", "sms"),
            ])
        )
    
    

    def start_meditation_timer(self, e, duration_seconds):
        # 1. Stop any existing timer by changing a unique ID
        self.timer_running = False 
        time.sleep(0.1) # Give the old thread a tiny moment to stop
        
        # 2. Start new timer session
        self.timer_running = True
        current_timer_id = random.random() # Create a unique ID for this click
        self.active_timer_id = current_timer_id
        
        e.control.disabled = True
        self.page.update()

        def run_timer():
            seconds = duration_seconds
            # The timer only runs if its ID is the "Active" one
            while seconds > 0 and self.active_timer_id == current_timer_id:
                mins, secs = divmod(seconds, 60)
                self.meditation_timer_text.value = f"{mins:02d}:{secs:02d}"
                self.page.update()
                time.sleep(1)
                seconds -= 1
            
            # Only show "Done" if the timer actually finished
            if self.active_timer_id == current_timer_id:
                self.meditation_timer_text.value = "Done!"
                e.control.disabled = False
                self.page.update()

        threading.Thread(target=run_timer, daemon=True).start()

    

    def create_help_hotline(self, name, contact, desc, icon):
        # We use the string "phone" instead of ft.icons.PHONE to avoid crashes
        return ft.Container(
            bgcolor=CARD_COLOR, padding=15, border_radius=10, margin=ft.margin.only(bottom=10),
            content=ft.Row([
                ft.Icon(icon, color=C_RED_400), 
                ft.Column([
                    ft.Text(name, weight="bold", size=16),
                    ft.Text(contact, color=ACCENT_MOVEMENT, size=14, weight="bold"),
                    ft.Text(desc, size=12, color=C_GREY_400),
                ], spacing=2)
            ])
        )
      
    # --- HELPERS ---

    def create_stat_card(self, title, value, icon, color, subtitle=None):
        bottom_content = ft.Column(
            spacing=0,
            controls=[
                ft.Text(
                    value,
                    size=36,
                    weight="bold",
                    color=TEXT_COLOR, 
                )
            ]
        )

        if subtitle:
            bottom_content.controls.append(
                ft.Text(
                    subtitle,
                    size=12,
                    color=C_GREY_400,
                )
            )

        return ft.Container(
            width=220,
            height=130,
            bgcolor=CARD_COLOR, 
            border_radius=15,
            padding=20,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(icon, color=color, size=20),
                            ft.Text(title, color=C_GREY_400, size=14, weight="w500"),
                        ]
                    ),
                    bottom_content,
                ],
            ),
        )

    
    
def main(page: ft.Page):
    print("Zenith Habit Tracker starting...")
    try:
        app = HabitApp(page)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        page.add(ft.Text(f"Error loading app: {e}", size=30, color="red"))

if __name__ == "__main__":
    ft.app(target=main)