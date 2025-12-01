import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import ctypes
import os
import sys
import threading
import winreg
import datetime
import time
import random

# --- CONFIGURACIÓN Y TEMA ---
COLORS = {
    "bg_dark": "#0a0a0a",      # Website Main BG
    "bg_panel": "#171717",     # Website Card BG
    "bg_hover": "#262626",
    "accent": "#3b82f6",       # Website Accent
    "accent_hover": "#2563eb",
    "text_main": "#ffffff",
    "text_sec": "#a3a3a3",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "success": "#10b981",
    "border": "#333333",
    "toggle_off": "#404040"
}

FONTS = {
    "header": ("Segoe UI", 20, "bold"),
    "subheader": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 9)
}

def set_dark_title_bar(window):
    """
    Forces the Windows title bar to be dark using the DwmSetWindowAttribute API.
    Works on Windows 10 (newer builds) and Windows 11.
    """
    try:
        window.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ctypes.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
        value = 2
        value = ctypes.c_int(value)
        set_window_attribute(hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        print(f"Failed to set dark title bar: {e}")

# --- SISTEMA DE LOGS ---
class Logger:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.log_dir, f"DrVicho_Log_{timestamp}.txt")
        
    def log(self, level, message, details=""):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        if details:
            entry += f"\n    >> Detalles: {details}"
        
        print(entry) 
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        
        return entry

    def get_log_content(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.read()
        return "No hay logs disponibles."

# --- WIDGETS PERSONALIZADOS (CANVAS) ---

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=200, height=45, bg_color=COLORS["accent"], text_color="#ffffff"):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_panel"], highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = COLORS["accent_hover"] if bg_color == COLORS["accent"] else "#444444"
        self.text_color = text_color
        self.text = text
        self.radius = 12 # Rounded corners
        
        self.draw()
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1+radius, y1,
                  x1+radius, y1,
                  x2-radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def draw(self):
        self.delete("all")
        # Background shape
        self.rect = self.round_rect(2, 2, int(self['width'])-2, int(self['height'])-2, self.radius, fill=self.bg_color, outline="")
        # Text
        self.text_id = self.create_text(int(self['width'])/2, int(self['height'])/2, text=self.text, fill=self.text_color, font=FONTS["body_bold"])
        
        self.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.tag_bind(self.text_id, "<Button-1>", self.on_click)

    def on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg_color)
        self.config(cursor="")

    def on_click(self, event):
        if self.command:
            self.command()

    def set_state(self, state):
        if state == "disabled":
            self.itemconfig(self.rect, fill="#333333")
            self.itemconfig(self.text_id, fill="#666666")
            self.unbind("<Button-1>")
        else:
            self.itemconfig(self.rect, fill=self.bg_color)
            self.itemconfig(self.text_id, fill=self.text_color)
            self.bind("<Button-1>", self.on_click)

class CustomCheckbox(tk.Canvas):
    def __init__(self, parent, text, variable, command=None, width=300, height=35):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_panel"], highlightthickness=0)
        self.variable = variable
        self.command = command
        self.text = text
        self.bg_color = COLORS["bg_panel"]
        
        self.box_size = 20
        self.box_x = 5
        self.box_y = (height - self.box_size) // 2
        
        self.draw()
        
        self.bind("<Button-1>", self.toggle)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.variable.trace_add("write", lambda *args: self.draw())

    def draw(self):
        self.delete("all")
        self.create_rectangle(0, 0, int(self['width']), int(self['height']), fill=self.bg_color, outline="", tags="bg")
        
        # Checkbox Box (Rounded)
        fill_color = COLORS["accent"] if self.variable.get() else ""
        outline_color = COLORS["accent"] if self.variable.get() else COLORS["text_sec"]
        
        # Simple rounded box simulation
        self.create_rectangle(self.box_x, self.box_y, self.box_x + self.box_size, self.box_y + self.box_size, 
                              fill=fill_color, outline=outline_color, width=2, tags="box")
        
        if self.variable.get():
            self.create_line(self.box_x + 5, self.box_y + 10, self.box_x + 9, self.box_y + 14, 
                             fill="white", width=2, tags="check", capstyle="round")
            self.create_line(self.box_x + 9, self.box_y + 14, self.box_x + 15, self.box_y + 6, 
                             fill="white", width=2, tags="check", capstyle="round")
            
        self.create_text(self.box_x + self.box_size + 15, int(self['height'])//2, 
                         text=self.text, fill=COLORS["text_main"], font=FONTS["body"], anchor="w", tags="text")

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def on_enter(self, event):
        self.bg_color = COLORS["bg_hover"]
        self.draw()
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.bg_color = COLORS["bg_panel"]
        self.draw()
        self.config(cursor="")

class CustomToggle(tk.Canvas):
    def __init__(self, parent, text, variable, command=None, width=300, height=35):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_panel"], highlightthickness=0)
        self.variable = variable
        self.command = command
        self.text = text
        self.bg_color = COLORS["bg_panel"]
        
        self.toggle_w = 44
        self.toggle_h = 24
        self.toggle_x = width - self.toggle_w - 10
        self.toggle_y = (height - self.toggle_h) // 2
        
        self.draw()
        
        self.bind("<Button-1>", self.toggle)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.variable.trace_add("write", lambda *args: self.draw())

    def draw(self):
        self.delete("all")
        self.create_rectangle(0, 0, int(self['width']), int(self['height']), fill=self.bg_color, outline="", tags="bg")
        
        self.create_text(10, int(self['height'])//2, text=self.text, fill=COLORS["text_main"], font=FONTS["body"], anchor="w", tags="text")
        
        # Track
        track_color = COLORS["accent"] if self.variable.get() else COLORS["toggle_off"]
        self.round_rect(self.toggle_x, self.toggle_y, self.toggle_x + self.toggle_w, self.toggle_y + self.toggle_h, 12, fill=track_color, outline="")
        
        # Knob
        knob_x = (self.toggle_x + self.toggle_w - self.toggle_h + 2) if self.variable.get() else (self.toggle_x + 2)
        self.create_oval(knob_x, self.toggle_y + 2, knob_x + self.toggle_h - 4, self.toggle_y + self.toggle_h - 2, fill="white", outline="")

    def round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()
            
    def on_enter(self, event):
        self.bg_color = COLORS["bg_hover"]
        self.draw()
        self.config(cursor="hand2")

    def on_leave(self, event):
        self.bg_color = COLORS["bg_panel"]
        self.draw()
        self.config(cursor="")


# --- APLICACIÓN PRINCIPAL ---
class DrVichoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DrVicho Optimizer")
        self.root.geometry("1150x800")
        self.root.configure(bg=COLORS["bg_dark"])
        
        # Apply Dark Title Bar
        set_dark_title_bar(self.root)
        
        self.logger = Logger()
        
        self.setup_styles()
        self.features = self.get_features()
        self.check_vars = {}
        
        self.create_layout()
        self.populate_features()
        
        self.logger.log("INFO", "Aplicación iniciada correctamente.")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure standard colors
        style.configure("TFrame", background=COLORS["bg_panel"])
        style.configure("Main.TFrame", background=COLORS["bg_dark"])
        style.configure("Sidebar.TFrame", background=COLORS["bg_panel"])
        
        # Labels
        style.configure("TLabel", background=COLORS["bg_panel"], foreground=COLORS["text_main"], font=FONTS["body"])
        style.configure("Header.TLabel", background=COLORS["bg_panel"], foreground=COLORS["accent"], font=FONTS["header"])
        style.configure("SubHeader.TLabel", background=COLORS["bg_panel"], foreground=COLORS["text_sec"], font=FONTS["subheader"])
        
        # Scrollbar
        style.configure("Vertical.TScrollbar", gripcount=0, background=COLORS["bg_hover"], darkcolor=COLORS["bg_dark"], lightcolor=COLORS["bg_dark"], troughcolor=COLORS["bg_panel"], bordercolor=COLORS["bg_panel"], arrowcolor=COLORS["text_sec"])
        style.map("Vertical.TScrollbar", background=[("active", COLORS["accent"])])

    def create_layout(self):
        # Contenedor Principal
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill="both", expand=True)

        # Barra Lateral (Sidebar)
        sidebar = ttk.Frame(main_container, style="Sidebar.TFrame", width=280)
        sidebar.pack(side="left", fill="y", padx=(0, 0))
        sidebar.pack_propagate(False)
        
        # Logo / Título
        title_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        title_frame.pack(pady=(40, 10), padx=30, anchor="w")
        ttk.Label(title_frame, text="DrVicho", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_frame, text="Optimizer v2.0", font=("Segoe UI", 11), foreground=COLORS["text_sec"], background=COLORS["bg_panel"]).pack(anchor="w")
        
        # Botones Presets
        ttk.Label(sidebar, text="PRESETS RÁPIDOS", font=("Segoe UI", 9, "bold"), foreground=COLORS["text_sec"], background=COLORS["bg_panel"]).pack(pady=(30, 15), padx=30, anchor="w")
        
        self.btn_standard = ModernButton(sidebar, text="Estándar", width=220, height=45, bg_color="#262626", text_color="white", command=lambda: self.apply_preset("standard"))
        self.btn_standard.pack(pady=8)
        
        self.btn_minimal = ModernButton(sidebar, text="Minimal", width=220, height=45, bg_color="#262626", text_color="white", command=lambda: self.apply_preset("minimal"))
        self.btn_minimal.pack(pady=8)
        
        self.btn_clear = ModernButton(sidebar, text="Limpiar Todo", width=220, height=45, bg_color="#262626", text_color="white", command=lambda: self.apply_preset("clear"))
        self.btn_clear.pack(pady=8)

        # Separator (Visual only)
        tk.Frame(sidebar, height=1, bg=COLORS["border"]).pack(fill="x", pady=30, padx=30)
        
        # Info Panel
        ttk.Label(sidebar, text="INFORMACIÓN", font=("Segoe UI", 9, "bold"), foreground=COLORS["text_sec"], background=COLORS["bg_panel"]).pack(pady=(0, 10), padx=30, anchor="w")
        self.info_panel = tk.Text(sidebar, height=10, width=25, bg=COLORS["bg_panel"], fg=COLORS["text_sec"], font=FONTS["small"], relief="flat", wrap="word", highlightthickness=0)
        self.info_panel.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.info_panel.insert("1.0", "Pasa el mouse sobre una opción para ver detalles técnicos.")
        self.info_panel.config(state="disabled")

        # Área de Contenido Principal
        content_area = ttk.Frame(main_container, style="Main.TFrame")
        content_area.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        # Encabezado
        header_frame = ttk.Frame(content_area, style="Main.TFrame")
        header_frame.pack(fill="x", pady=(40, 20), padx=40)
        
        ttk.Label(header_frame, text="Panel de Control", font=FONTS["header"], foreground=COLORS["text_main"], background=COLORS["bg_dark"]).pack(side="left")
        
        # Grid de Contenido (Canvas Scrolleable)
        canvas_container = ttk.Frame(content_area, style="Main.TFrame")
        canvas_container.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        self.canvas = tk.Canvas(canvas_container, bg=COLORS["bg_dark"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Main.TFrame")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Barra Inferior
        action_bar = ttk.Frame(self.root, style="Sidebar.TFrame", height=90)
        action_bar.pack(side="bottom", fill="x")
        action_bar.pack_propagate(False)
        
        # Border Top for Action Bar
        tk.Frame(action_bar, height=1, bg=COLORS["border"]).pack(side="top", fill="x")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_bar, variable=self.progress_var, maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(side="left", padx=40, pady=30)
        
        self.status_label = ttk.Label(action_bar, text="Listo para optimizar", font=FONTS["body"], foreground=COLORS["text_sec"])
        self.status_label.pack(side="left", pady=30, padx=10)

        self.btn_optimize = ModernButton(action_bar, text="APLICAR CAMBIOS", width=240, height=50, command=self.start_optimization_flow)
        self.btn_optimize.pack(side="right", padx=40, pady=20)

    def get_features(self):
        # Misma lista de features, pero añadimos el tipo 'toggle' para las de personalización
        features = [
            # --- TWEAKS ESENCIALES (Checkboxes) ---
            {"name": "Crear Punto de Restauración", "desc": "Crea un respaldo del sistema.", "tech": "Checkpoint-Computer", "cmd": self.create_restore_point, "category": "Esenciales", "type": "check", "standard": True, "minimal": True},
            {"name": "Limpiar Temporales", "desc": "Borra archivos basura.", "tech": "Remove-Item Temp", "cmd": self.clean_temp_files, "category": "Esenciales", "type": "check", "standard": True, "minimal": True},
            {"name": "Deshabilitar Telemetría", "desc": "Mejora privacidad.", "tech": "Stop DiagTrack", "cmd": self.disable_telemetry, "category": "Esenciales", "type": "check", "standard": True, "minimal": False},
            {"name": "Deshabilitar Historial", "desc": "No guardar actividad.", "tech": "PublishUserActivities=0", "cmd": self.disable_activity_history, "category": "Esenciales", "type": "check", "standard": True, "minimal": False},
            {"name": "Desactivar GameDVR", "desc": "Libera recursos gaming.", "tech": "GameDVR_Enabled=0", "cmd": self.disable_game_bar, "category": "Esenciales", "type": "check", "standard": False, "minimal": False},
            {"name": "Desactivar Hibernación", "desc": "Ahorra espacio en disco.", "tech": "powercfg -h off", "cmd": self.disable_hibernation, "category": "Esenciales", "type": "check", "standard": False, "minimal": False},
            {"name": "Deshabilitar Ubicación", "desc": "Apaga geolocalización.", "tech": "SensorPermissionState=0", "cmd": self.disable_location, "category": "Esenciales", "type": "check", "standard": True, "minimal": False},
            {"name": "Limpieza de Disco", "desc": "Abre cleanmgr.", "tech": "cleanmgr.exe", "cmd": self.run_disk_cleanup, "category": "Esenciales", "type": "check", "standard": True, "minimal": True},
            {"name": "DNS Cloudflare (1.1.1.1)", "desc": "DNS más rápido y privado.", "tech": "Set-DnsClientServerAddress", "cmd": self.set_cloudflare_dns, "category": "Red", "type": "check", "standard": True, "minimal": False},
            {"name": "Desactivar Sticky Keys", "desc": "Evita el diálogo al presionar Shift 5 veces.", "tech": "RegKey: StickyKeys", "cmd": self.disable_sticky_keys, "category": "Gaming", "type": "check", "standard": True, "minimal": True},
            {"name": "Apps en Segundo Plano", "desc": "Evita que apps consuman RAM sin uso.", "tech": "LetAppsRunInBackground=2", "cmd": self.disable_background_apps, "category": "Rendimiento", "type": "check", "standard": True, "minimal": False},
            {"name": "Desactivar Sugerencias", "desc": "Quita anuncios en Inicio y Configuración.", "tech": "ContentDeliveryManager", "cmd": self.disable_windows_suggestions, "category": "Limpieza", "type": "check", "standard": True, "minimal": False},
            {"name": "Desactivar Pantalla Bloqueo", "desc": "Va directo al login al iniciar.", "tech": "NoLockScreen=1", "cmd": self.disable_lock_screen, "category": "Personalización", "type": "check", "standard": False, "minimal": False},
            {"name": "Desactivar Fax/XPS", "desc": "Elimina servicios de impresión antiguos.", "tech": "Disable-WindowsOptionalFeature", "cmd": self.disable_fax_xps, "category": "Limpieza", "type": "check", "standard": True, "minimal": False},
            {"name": "Optimizar NTFS", "desc": "Mejora rendimiento de disco.", "tech": "fsutil behavior", "cmd": self.optimize_ntfs, "category": "Rendimiento", "type": "check", "standard": True, "minimal": False},
            {"name": "Desactivar Notificaciones", "desc": "Silencia notificaciones molestas.", "tech": "ToastEnabled=0", "cmd": self.disable_notifications, "category": "Privacidad", "type": "check", "standard": False, "minimal": False},
            {"name": "Debloat Edge", "desc": "Quita barra lateral y preinicio de Edge.", "tech": "RegKey: Edge Policies", "cmd": self.debloat_edge, "category": "Limpieza", "type": "check", "standard": True, "minimal": False},
            
            # --- PERSONALIZACIÓN (Toggles) ---
            {"name": "Tema Oscuro", "desc": "Activa el modo oscuro de Windows.", "tech": "AppsUseLightTheme=0", "cmd": self.set_dark_theme, "category": "Personalización", "type": "toggle", "standard": True, "minimal": False},
            {"name": "Bing en Inicio", "desc": "Muestra/Oculta Bing en búsquedas.", "tech": "DisableSearchBoxSuggestions", "cmd": self.toggle_bing, "category": "Personalización", "type": "toggle", "standard": True, "minimal": False},
            {"name": "Snap Assist", "desc": "Ajuste de ventanas.", "tech": "WindowArrangementActive", "cmd": self.toggle_snap, "category": "Personalización", "type": "toggle", "standard": True, "minimal": False},
            {"name": "Aceleración Mouse", "desc": "Precisión del puntero.", "tech": "MouseSpeed", "cmd": self.disable_mouse_acceleration, "category": "Personalización", "type": "toggle", "standard": False, "minimal": False},
            {"name": "Extensiones de Archivo", "desc": "Mostrar extensiones .txt, .exe...", "tech": "HideFileExt=0", "cmd": self.show_extensions, "category": "Personalización", "type": "toggle", "standard": True, "minimal": False},
            {"name": "Archivos Ocultos", "desc": "Mostrar archivos ocultos.", "tech": "Hidden=1", "cmd": self.show_hidden_files, "category": "Personalización", "type": "toggle", "standard": False, "minimal": False},
            {"name": "Botón Vista Tareas", "desc": "Mostrar en barra de tareas.", "tech": "ShowTaskViewButton", "cmd": self.toggle_taskview, "category": "Personalización", "type": "toggle", "standard": True, "minimal": True},
            {"name": "Botón Widgets", "desc": "Mostrar widgets.", "tech": "TaskbarDa", "cmd": self.toggle_widgets, "category": "Personalización", "type": "toggle", "standard": True, "minimal": True},
        ]
        return features

    def populate_features(self):
        # Dividir en dos columnas visuales usando Frames
        left_col = ttk.Frame(self.scrollable_frame)
        left_col.pack(side="left", fill="both", expand=True, padx=10)
        
        right_col = ttk.Frame(self.scrollable_frame)
        right_col.pack(side="left", fill="both", expand=True, padx=10)

        # Títulos de columnas
        ttk.Label(left_col, text="Tweaks Esenciales", font=("Segoe UI", 12, "bold"), foreground=COLORS["accent"]).pack(anchor="w", pady=(0, 10))
        ttk.Label(right_col, text="Personalización", font=("Segoe UI", 12, "bold"), foreground=COLORS["accent"]).pack(anchor="w", pady=(0, 10))

        for i, feature in enumerate(self.features):
            target_col = left_col if feature["category"] == "Esenciales" else right_col
            
            var = tk.BooleanVar(value=False)
            self.check_vars[i] = var
            
            if feature["type"] == "check":
                widget = CustomCheckbox(target_col, text=feature["name"], variable=var, width=350)
            else:
                widget = CustomToggle(target_col, text=feature["name"], variable=var, width=350)
            
            widget.pack(anchor="w", pady=2)
            
            # Binding para tooltip
            widget.bind("<Enter>", lambda e, w=widget, desc=feature["desc"], tech=feature.get("tech", ""): [w.on_enter(e), self.show_info(desc, tech)])
            widget.bind("<Leave>", lambda e, w=widget: [w.on_leave(e), self.show_info("")])

    def show_info(self, text, tech=""):
        self.info_panel.config(state="normal")
        self.info_panel.delete("1.0", tk.END)
        if text:
            self.info_panel.insert("1.0", text + "\n\n")
            if tech:
                self.info_panel.insert("end", f"[TÉCNICO]: {tech}", "tech_tag")
                self.info_panel.tag_config("tech_tag", foreground=COLORS["accent"])
        else:
            self.info_panel.insert("1.0", "Pasa el mouse sobre una opción para ver detalles.")
        self.info_panel.config(state="disabled")

    def apply_preset(self, preset_type):
        for i, feature in enumerate(self.features):
            var = self.check_vars[i]
            if preset_type == "clear":
                var.set(False)
            elif preset_type == "standard":
                var.set(feature.get("standard", False))
            elif preset_type == "minimal":
                var.set(feature.get("minimal", False))
        
        messagebox.showinfo("Preset Aplicado", f"Se ha seleccionado el perfil: {preset_type.capitalize()}")

    def start_optimization_flow(self):
        selected_indices = [i for i, var in self.check_vars.items() if var.get()]
        if not selected_indices:
            messagebox.showwarning("Atención", "No has seleccionado ninguna optimización.")
            return

        if not messagebox.askyesno("Confirmación", "¿Estás seguro de aplicar las optimizaciones seleccionadas?"):
            return

        self.btn_optimize.set_state("disabled")
        threading.Thread(target=self.run_optimization_process, args=(selected_indices,), daemon=True).start()

    def run_optimization_process(self, indices):
        self.update_status("Iniciando...", 0)
        time.sleep(1)
        
        total = len(indices)
        completed = 0
        
        for i in indices:
            feature = self.features[i]
            self.update_status(f"Aplicando: {feature['name']}...", 0, keep_progress=True)
            self.execute_feature(i)
            completed += 1
            self.update_progress(completed, total)
            time.sleep(0.3)

        self.update_status("¡Completado!", 100)
        messagebox.showinfo("Éxito", "Optimización finalizada. Reinicia tu PC.")
        self.root.after(0, self.reset_ui)

    def execute_feature(self, index):
        feature = self.features[index]
        try:
            if feature["cmd"]:
                feature["cmd"]()
        except Exception as e:
            self.logger.log("ERROR", f"Fallo en {feature['name']}", str(e))

    def update_status(self, text, progress_val, keep_progress=False):
        self.root.after(0, lambda: self.status_label.config(text=text))
        if not keep_progress:
            self.root.after(0, lambda: self.progress_var.set(progress_val))

    def update_progress(self, current, total):
        val = (current / total * 100)
        self.root.after(0, lambda: self.progress_var.set(val))

    def reset_ui(self):
        self.btn_optimize.set_state("normal")
        self.status_label.config(text="Listo")
        self.progress_var.set(0)

    # --- LÓGICA DE OPTIMIZACIÓN (WRAPPERS) ---
    def run_powershell(self, cmd):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(["powershell", "-Command", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, text=True)
            stdout, stderr = process.communicate()
            if stderr:
                self.logger.log("SHELL_ERR", "Error en PowerShell", stderr.strip())
                return False, stderr.strip()
            if stdout:
                self.logger.log("SHELL_OUT", "Salida PowerShell", stdout.strip())
            return True, stdout.strip()
        except Exception as e:
            self.logger.log("SHELL_EX", "Excepción ejecutando comando", str(e))
            return False, str(e)

    def run_registry(self, key, path, name, value, type_reg):
        try:
            reg_key = winreg.OpenKey(key, path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg_key, name, 0, type_reg, value)
            winreg.CloseKey(reg_key)
            self.logger.log("REGISTRY", f"Modificado: {path}\\{name} -> {value}")
            return True, ""
        except Exception as e:
            try:
                reg_key = winreg.CreateKey(key, path)
                winreg.SetValueEx(reg_key, name, 0, type_reg, value)
                winreg.CloseKey(reg_key)
                self.logger.log("REGISTRY", f"Creado y Modificado: {path}\\{name} -> {value}")
                return True, "Key created"
            except Exception as e2:
                self.logger.log("REGISTRY_ERR", f"Fallo en {path}", str(e2))
                return False, str(e2)

    # --- FUNCIONES ESENCIALES (RESTAURADAS) ---
    def create_restore_point(self):
        self.run_powershell("Checkpoint-Computer -Description 'DrVicho_Backup' -RestorePointType 'MODIFY_SETTINGS'")

    def clean_temp_files(self):
        cmds = [
            "Remove-Item -Path $env:TEMP\* -Recurse -Force -ErrorAction SilentlyContinue",
            "Remove-Item -Path 'C:\Windows\Temp\*' -Recurse -Force -ErrorAction SilentlyContinue",
            "Clear-DnsClientCache"
        ]
        for cmd in cmds:
            self.run_powershell(cmd)

    def disable_telemetry(self):
        self.run_powershell("Stop-Service DiagTrack -Force -ErrorAction SilentlyContinue")
        self.run_powershell("Set-Service DiagTrack -StartupType Disabled")
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD)

    def disable_activity_history(self):
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities", 0, winreg.REG_DWORD)

    def disable_game_bar(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_Enabled", 0, winreg.REG_DWORD)

    def disable_hibernation(self):
        self.run_powershell("powercfg -h off")

    def disable_location(self):
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location", "Value", "Deny", winreg.REG_SZ)

    def run_disk_cleanup(self):
        subprocess.Popen("cleanmgr.exe")

    # --- FUNCIONES DE PERSONALIZACIÓN (TOGGLES) ---
    def set_dark_theme(self):
        # 0 = Dark, 1 = Light
        val = 0 
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", val, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", val, winreg.REG_DWORD)

    def toggle_bing(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", 1, winreg.REG_DWORD)

    def toggle_snap(self):
        # 0 = Off, 1 = On
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "WindowArrangementActive", "0", winreg.REG_SZ)

    def disable_mouse_acceleration(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", "0", winreg.REG_SZ)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold1", "0", winreg.REG_SZ)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold2", "0", winreg.REG_SZ)

    def show_extensions(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 0, winreg.REG_DWORD)
        self.run_powershell("Get-Process explorer | Stop-Process") # Restart explorer to apply

    def show_hidden_files(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden", 1, winreg.REG_DWORD)
        self.run_powershell("Get-Process explorer | Stop-Process")

    def toggle_taskview(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowTaskViewButton", 0, winreg.REG_DWORD)

    def toggle_widgets(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa", 0, winreg.REG_DWORD)

    # --- NUEVAS FUNCIONES DE OPTIMIZACIÓN ---
    def disable_sticky_keys(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\StickyKeys", "Flags", "506", winreg.REG_SZ)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\Keyboard Response", "Flags", "122", winreg.REG_SZ)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", "58", winreg.REG_SZ)

    def disable_background_apps(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", "GlobalUserDisabled", 1, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\AppPrivacy", "LetAppsRunInBackground", 2, winreg.REG_DWORD)

    def disable_windows_suggestions(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SoftLandingEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "RotatingLockScreenEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "RotatingLockScreenOverlayEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338387Enabled", 0, winreg.REG_DWORD)

    def disable_lock_screen(self):
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen", 1, winreg.REG_DWORD)

    def disable_fax_xps(self):
        services = ["Spooler", "Fax", "XblAuthManager", "XblGameSave", "XboxNetApiSvc", "XboxGipSvc"] # Added Xbox services here too for good measure if not used
        for srv in services:
             self.run_powershell(f"Stop-Service {srv} -Force -ErrorAction SilentlyContinue; Set-Service {srv} -StartupType Disabled")
        self.run_powershell("Disable-WindowsOptionalFeature -Online -FeatureName Printing-PrintToPDFServices-Features -NoRestart")
        self.run_powershell("Disable-WindowsOptionalFeature -Online -FeatureName Printing-XPSServices-Features -NoRestart")

    def set_cloudflare_dns(self):
        self.run_powershell("Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ServerAddresses 1.1.1.1, 1.0.0.1")

    def disable_uac(self):
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "EnableLUA", 0, winreg.REG_DWORD)

    def debloat_edge(self):
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", "HubsSidebarEnabled", 0, winreg.REG_DWORD)
        self.run_registry(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled", 0, winreg.REG_DWORD)

    def optimize_ntfs(self):
        self.run_powershell("fsutil behavior set disablelastaccess 1")
        self.run_powershell("fsutil behavior set encryptpagingfile 0")

    def disable_notifications(self):
        self.run_registry(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 0, winreg.REG_DWORD)


if __name__ == "__main__":
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    try:
        if is_admin():
            root = tk.Tk()
            app = DrVichoApp(root)
            root.mainloop()
        else:
            # Re-run the program with admin rights
            executable = f'"{sys.executable}"'
            script = f'"{os.path.abspath(sys.argv[0])}"'
            params = " ".join([script] + sys.argv[1:])
            
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            
            if ret <= 32: # Error code
                raise RuntimeError(f"ShellExecute failed with code {ret}")
            
            # EXIT IMMEDIATELY to prevent double execution
            sys.exit(0)
                
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error Fatal", f"La aplicación ha fallado al iniciar:\n\n{err}")
        except:
            with open("crash_log.txt", "w") as f:
                f.write(err)
            print(err)
            input("Presiona Enter para salir...")
