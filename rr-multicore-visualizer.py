import tkinter as tk
from tkinter import ttk, messagebox, Scale
import collections
import time
import random
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CORE_AREA_Y_START = 100
CORE_AREA_HEIGHT = 150
QUEUE_AREA_Y_START = CORE_AREA_Y_START + CORE_AREA_HEIGHT + 50
QUEUE_AREA_HEIGHT = 150
PROCESS_RADIUS = 15
ANIMATION_STEP_DELAY_MS = 1000 
ANIMATION_MOVE_STEPS = 30

class Process:
    """Represents a process with its properties and visual representation."""
    def __init__(self, p_id, arrival_time, burst_time, canvas, color):
        self.id = p_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_burst_time = burst_time
        self.start_time = -1
        self.completion_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.state = "New" 
        self.current_core = None
        self.time_on_core_current_quantum = 0
        self.canvas = canvas
        self.color = color
        self.visual_id = None
        self.text_id = None 
        self.target_x = None
        self.target_y = None
        self.current_x = None
        self.current_y = None

    def create_visual(self, x, y):
        """Creates the visual representation on the canvas."""
        self.current_x = x
        self.current_y = y
        self.visual_id = self.canvas.create_oval(
            x - PROCESS_RADIUS, y - PROCESS_RADIUS,
            x + PROCESS_RADIUS, y + PROCESS_RADIUS,
            fill=self.color, outline="black"
        )
        self.text_id = self.canvas.create_text(
            x, y, text=f"P{self.id}", fill="white"
        )
        self.canvas.tag_raise(self.text_id, self.visual_id) 

    def move_visual(self, dx, dy):
        """Moves the visual representation by dx, dy."""
        if self.visual_id:
            self.canvas.move(self.visual_id, dx, dy)
            self.canvas.move(self.text_id, dx, dy)
            self.current_x += dx
            self.current_y += dy

    def set_position(self, x, y):
        """Instantly sets the visual representation's position."""
        if self.visual_id:
            dx = x - self.current_x
            dy = y - self.current_y
            self.move_visual(dx, dy) 

    def destroy_visual(self):
        """Removes the visual representation from the canvas."""
        if self.visual_id:
            self.canvas.delete(self.visual_id)
            self.canvas.delete(self.text_id)
            self.visual_id = None
            self.text_id = None

    def update_tooltip(self, text):
         """ Placeholder for potentially showing process details on hover """

         pass

    def __repr__(self):
        return f"P{self.id} (AT:{self.arrival_time}, BT:{self.burst_time})"

class RRSchedulerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Multicore Round Robin Scheduling Simulator")
        self.master.geometry("1000x800") 

        self.processes = []
        self.ready_queue = collections.deque()
        self.terminated_processes = []
        self.cores = [] 
        self.gantt_data = []

        self.current_time = 0
        self.time_quantum = 1
        self.num_cores = 2
        self.simulation_running = False
        self.simulation_paused = False
        self.animation_speed_factor = 1.0 # 1.0
        self.process_counter = 0
        self.colors = ["red", "blue", "green", "orange", "purple", "brown", "pink", "cyan", "magenta", "yellow", "lime", "teal"]
        random.shuffle(self.colors)
        self.color_index = 0

        self._setup_gui()

    def _get_next_color(self):
        """Cycles through the color list."""
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color

    def _setup_gui(self):
        """Creates and arranges the GUI elements."""
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        ttk.Label(control_frame, text="Arrival Time:").grid(row=0, column=0, sticky="w", pady=2)
        self.arrival_time_entry = ttk.Entry(control_frame, width=5)
        self.arrival_time_entry.grid(row=0, column=1, sticky="w", pady=2)
        self.arrival_time_entry.insert(0, "0")

        ttk.Label(control_frame, text="Burst Time:").grid(row=1, column=0, sticky="w", pady=2)
        self.burst_time_entry = ttk.Entry(control_frame, width=5)
        self.burst_time_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.burst_time_entry.insert(0, "5")

        self.add_process_button = ttk.Button(control_frame, text="Tambah Process", command=self.add_process)
        self.add_process_button.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Label(control_frame, text="List Proses:").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.process_listbox = tk.Listbox(control_frame, height=8, width=30)
        self.process_listbox.grid(row=4, column=0, columnspan=2, pady=2, sticky="ew")

        ttk.Label(control_frame, text="Quantum Time:").grid(row=5, column=0, sticky="w", pady=2)
        self.time_quantum_spinbox = tk.Spinbox(control_frame, from_=1, to=10, width=5, wrap=True)
        self.time_quantum_spinbox.grid(row=5, column=1, sticky="w", pady=2)
        self.time_quantum_spinbox.delete(0, tk.END)
        self.time_quantum_spinbox.insert(0, "2") # Default

        ttk.Label(control_frame, text="Number of Cores:").grid(row=6, column=0, sticky="w", pady=2)
        self.num_cores_spinbox = tk.Spinbox(control_frame, from_=1, to=8, width=5, wrap=True, command=self._update_core_display_on_change)
        self.num_cores_spinbox.grid(row=6, column=1, sticky="w", pady=2)
        self.num_cores_spinbox.delete(0, tk.END)
        self.num_cores_spinbox.insert(0, "2") # Default

        self.start_button = ttk.Button(control_frame, text="Mulai Simulasi", command=self.start_simulation)
        self.start_button.grid(row=7, column=0, columnspan=2, pady=(15, 5))

        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.grid(row=8, column=0, columnspan=2, pady=5)

        self.reset_button = ttk.Button(control_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.grid(row=9, column=0, columnspan=2, pady=5)

        ttk.Label(control_frame, text="Animation Speed:").grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.speed_scale = Scale(control_frame, from_=0.2, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, label="Faster <-> Slower", command=self.update_speed)
        self.speed_scale.set(1.0) # Default
        self.speed_scale.grid(row=11, column=0, columnspan=2, sticky="ew")

        self.time_label = ttk.Label(control_frame, text="Time: 0", font=("Arial", 12))
        self.time_label.grid(row=12, column=0, columnspan=2, pady=(15, 5))

        vis_frame = ttk.Frame(main_frame, padding="10")
        vis_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(vis_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white", scrollregion=(0,0,CANVAS_WIDTH, CANVAS_HEIGHT + 200))
        hbar = ttk.Scrollbar(vis_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(vis_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        self._draw_simulation_areas()

        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.results_label = ttk.Label(results_frame, text="Waiting for simulation end...")
        self.results_label.pack(pady=5)

        self._update_core_display_on_change()


def _draw_simulation_areas(self):
        """Draws the static parts of the simulation area like core boxes and queue area."""
        self.canvas.delete("areas") # Clear

        self.canvas.create_text(10, CORE_AREA_Y_START - 15, text="CPU Cores:", anchor="w", font=("Arial", 12, "bold"), tags="areas")
        self.canvas.create_rectangle(5, CORE_AREA_Y_START, CANVAS_WIDTH - 5, CORE_AREA_Y_START + CORE_AREA_HEIGHT, outline="gray", dash=(2, 2), tags="areas")

        self.canvas.create_text(10, QUEUE_AREA_Y_START - 15, text="Ready Queue:", anchor="w", font=("Arial", 12, "bold"), tags="areas")
        self.canvas.create_rectangle(5, QUEUE_AREA_Y_START, CANVAS_WIDTH - 5, QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT, outline="gray", dash=(2, 2), tags="areas")

        self.gantt_y_start = QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT + 50
        self.canvas.create_text(10, self.gantt_y_start - 15, text="Gantt Chart:", anchor="w", font=("Arial", 12, "bold"), tags="areas")

        self._update_core_display()


    def _update_core_display_on_change(self, event=None):
        """Handles changes in the number of cores spinbox."""
        if self.simulation_running:
             messagebox.showwarning("Warning", "Cannot change core count during simulation. Reset first.")
             self.num_cores_spinbox.delete(0, tk.END)
             self.num_cores_spinbox.insert(0, str(self.num_cores)) # Revert
             return
        try:
            self.num_cores = int(self.num_cores_spinbox.get())
            if not 1 <= self.num_cores <= 8:
                raise ValueError("Core count must be between 1 and 8.")
            self._update_core_display()
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid number of cores: {e}")
            self.num_cores_spinbox.delete(0, tk.END)
            self.num_cores_spinbox.insert(0, str(self.num_cores)) # Revert


    def _update_core_display(self):
         """Draws or redraws the core representations."""
         self.canvas.delete("core_visual") # Clear

         core_box_width = (CANVAS_WIDTH - 20) / self.num_cores
         core_box_height = CORE_AREA_HEIGHT * 0.6
         y_pos = CORE_AREA_Y_START + (CORE_AREA_HEIGHT - core_box_height) / 2

         self.cores = [] # Reset

         for i in range(self.num_cores):
             x_start = 10 + i * core_box_width
             x_end = x_start + core_box_width - 10 # Small
             center_x = (x_start + x_end) / 2
             center_y = y_pos + core_box_height / 2

             core_id = self.canvas.create_rectangle(
                 x_start, y_pos, x_end, y_pos + core_box_height,
                 outline="blue", fill="lightblue", tags=("core_visual", f"core_{i}")
             )
             self.canvas.create_text(
                 center_x, y_pos - 10, text=f"Core {i}", anchor="s", tags=("core_visual", f"core_text_{i}")
             )
             self.cores.append({
                 'id': i,
                 'state': 'Idle',
                 'process': None,
                 'visual_id': core_id,
                 'x': center_x, # Target
                 'y': center_y, # Target
                 'start_x': x_start,
                 'start_y': y_pos,
                 'end_x': x_end,
                 'end_y': y_pos + core_box_height
             })

    def tambah_process(self):
        """Adds a new process from the input fields."""
        if self.simulation_running:
             messagebox.showwarning("Warning", "Cannot add processes during simulation.")
             return
        try:
            arrival_time = int(self.arrival_time_entry.get())
            burst_time = int(self.burst_time_entry.get())
            if arrival_time < 0 or burst_time <= 0:
                raise ValueError("Arrival time must be >= 0 and Burst time must be > 0.")

            self.process_counter += 1
            new_process = Process(self.process_counter, arrival_time, burst_time, self.canvas, self._get_next_color())
            self.processes.append(new_process)
            self.process_listbox.insert(tk.END, repr(new_process))

            self.arrival_time_entry.delete(0, tk.END)
            self.arrival_time_entry.insert(0, str(arrival_time + 1))
            self.burst_time_entry.delete(0, tk.END)
            self.burst_time_entry.insert(0, str(random.randint(3, 8))) # Suggest


        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
