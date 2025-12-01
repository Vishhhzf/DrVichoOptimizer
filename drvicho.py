import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import ctypes
import os
import sys
import threading
import winreg
import time
import datetime

# --- CONFIGURACIÓN VISUAL (THEME CYBERPUNK/SLATE) ---
COLORS = {
    "bg_main": "#0f172a",       # Fondo Principal
    "bg_sec": "#1e293b",        # Paneles
    "bg_ter": "#334155",        # Inputs/Logs
    "accent": "#3b82f6",        # Azul Primario
    "accent_hover": "#2563eb",  # Azul Hover
    "success": "#10b981",       # Verde
    "warning": "#f59e0b",       # Amarillo
    "danger": "#ef4444",        # Rojo
    "text_main": "#f1f5f9",     # Blanco Hueso
    "text_sec": "#94a3b8"       # Gris Texto
}

FONTS = {
    "h1": ("Segoe UI Variable Display", 20, "bold"),
    "h2": ("Segoe UI Variable Text", 14, "bold"),
    "body": ("Segoe UI Variable Text", 10),
    "code": ("Consolas", 9)
}

# --- CLASE DE UTILIDADES DEL SISTEMA ---
class SystemUtils:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def run_ps(cmd):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", cmd],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                startupinfo=startupinfo, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            return True, stdout.strip()
        except Exception as e:
            return False, str(e)

    @staticmethod
    def set_reg(key_root, path, name, value, reg_type):
        try:
            try: winreg.CreateKey(key_root, path)
            except: pass
            with winreg.OpenKey(key_root, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, reg_type, value)
            return True, f"Registro OK: {name} -> {value}"
        except Exception as e:
            return False, f"Error Reg: {e}"

    @staticmethod
    def delete_reg_key(key_root, path):
        try:
            winreg.DeleteKey(key_root, path)
            return True, f"Clave eliminada: {path}"
        except:
            return False, "Clave no encontrada o error"

# --- COMPONENTES UI PERSONALIZADOS ---
class ToggleSwitch(tk.Canvas):
    def __init__(self, parent, variable, command=None):
        super().__init__(parent, width=50, height=26, bg=COLORS["bg_sec"], highlightthickness=0)
        self.variable = variable
        self.command = command
        self.variable.trace_add("write", lambda *args: self.animate())
        self.draw()
        self.bind("<Button-1>", lambda e: self.toggle())

    def draw(self):
        self.delete("all")
        state = self.variable.get()
        fill = COLORS["success"] if state else COLORS["bg_ter"]
        self.create_oval(2, 2, 24, 24, fill=fill, outline="")
        self.create_rectangle(13, 2, 37, 24, fill=fill, outline="")
        self.create_oval(26, 2, 48, 24, fill=fill, outline="")
        kx = 28 if state else 4
        self.create_oval(kx, 4, kx+18, 22, fill="white", outline="")

    def animate(self):
        self.draw()

    def toggle(self):
        self.variable.set(not self.variable.get())
        if self.command: self.command()

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=150, height=40, bg_color=COLORS["accent"]):
        super().__init__(parent, width=width, height=height, bg=parent["bg"] if "bg" in parent.keys() else COLORS["bg_main"], highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.text = text
        self.draw()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def draw(self, hover=False):
        self.delete("all")
        fill = COLORS["accent_hover"] if hover else self.bg_color
        # Rounded Rect manual
        r = 10
        w, h = int(self['width']), int(self['height'])
        self.create_polygon(
            r,0, w-r,0, w,0, w,r, w,h-r, w,h, w-r,h, r,h, 0,h, 0,h-r, 0,r, 0,0,
            smooth=True, fill=fill
        )
        self.create_text(w/2, h/2, text=self.text, fill="white", font=FONTS["h2"])

    def on_enter(self, e): self.draw(hover=True); self.config(cursor="hand2")
    def on_leave(self, e): self.draw(hover=False); self.config(cursor="")
    def on_click(self, e): 
        if self.command: self.command()

# --- APLICACIÓN PRINCIPAL ---
class DrVichoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DrVicho Optimizer v5.0 GOD MODE")
        self.root.geometry("1200x850")
        self.root.configure(bg=COLORS["bg_main"])
        
        # Dark Title Bar Hack
        try:
            root.update()
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.windll.user32.GetParent(root.winfo_id()), 20, ctypes.byref(ctypes.c_int(2)), 4)
        except: pass

        self.features = self.load_features()
        self.vars = {f["id"]: tk.BooleanVar(value=False) for f in self.features}
        
        self.setup_layout()
        self.start_monitoring()

    def setup_layout(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg=COLORS["bg_main"], height=60)
        header.pack(fill="x", padx=20, pady=15)
        
        tk.Label(header, text="⚡ DrVicho", font=("Segoe UI", 26, "bold"), fg=COLORS["accent"], bg=COLORS["bg_main"]).pack(side="left")
        tk.Label(header, text="OPTIMIZER v5.0", font=("Segoe UI", 12, "bold"), fg=COLORS["text_sec"], bg=COLORS["bg_main"]).pack(side="left", padx=10, pady=(10,0))
        
        # Stats Widget (Top Right)
        self.stats_label = tk.Label(header, text="CPU: ... | RAM: ...", font=FONTS["code"], fg=COLORS["success"], bg=COLORS["bg_sec"], padx=10, pady=5)
        self.stats_label.pack(side="right")

        # --- TABS CONTAINER ---
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=COLORS["bg_main"], borderwidth=0)
        style.configure('TNotebook.Tab', background=COLORS["bg_sec"], foreground=COLORS["text_sec"], padding=[20, 10], font=FONTS["body"])
        style.map('TNotebook.Tab', background=[('selected', COLORS["accent"])], foreground=[('selected', 'white')])

        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        # Crear Pestañas
        self.tab_gaming = self.create_tab("🎮 Gaming & FPS")
        self.tab_win11 = self.create_tab("🎨 Windows UI")
        self.tab_network = self.create_tab("🌐 Red & Ping")
        self.tab_privacy = self.create_tab("🛡️ Privacidad")
        self.tab_maintenance = self.create_tab("🧹 Mantenimiento")

        # Rellenar Pestañas con Features
        self.populate_tab(self.tab_gaming, "gaming")
        self.populate_tab(self.tab_win11, "win11")
        self.populate_tab(self.tab_network, "network")
        self.populate_tab(self.tab_privacy, "privacy")
        
        # Pestaña Mantenimiento (Botones especiales)
        self.populate_maintenance_tab()

        # --- LOG CONSOLE & ACTION BAR ---
        bottom_panel = tk.Frame(self.root, bg=COLORS["bg_main"])
        bottom_panel.pack(fill="x", padx=20, pady=20)

        # Consola
        self.console = scrolledtext.ScrolledText(bottom_panel, height=8, bg=COLORS["bg_ter"], fg=COLORS["text_main"], font=FONTS["code"], state='disabled', bd=0)
        self.console.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Botón Acción
        action_frame = tk.Frame(bottom_panel, bg=COLORS["bg_main"])
        action_frame.pack(side="right", fill="y")
        
        self.btn_run = ModernButton(action_frame, "APLICAR CAMBIOS", command=self.run_process, width=220, height=60)
        self.btn_run.pack()

    def create_tab(self, title):
        frame = tk.Frame(self.notebook, bg=COLORS["bg_main"])
        self.notebook.add(frame, text=title)
        
        # Scroll setup inside tab
        canvas = tk.Canvas(frame, bg=COLORS["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS["bg_main"])
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        return scroll_frame

    def populate_tab(self, parent, category):
        items = [f for f in self.features if f["cat"] == category]
        row = 0
        col = 0
        
        for item in items:
            frame = tk.Frame(parent, bg=COLORS["bg_sec"], padx=15, pady=10)
            frame.grid(row=row, column=col, sticky="ew", padx=10, pady=5)
            parent.grid_columnconfigure(col, weight=1)
            
            # Switch
            ToggleSwitch(frame, self.vars[item["id"]]).pack(side="right", padx=10)
            
            # Text
            tk.Label(frame, text=item["name"], font=FONTS["h2"], bg=COLORS["bg_sec"], fg="white", anchor="w").pack(fill="x")
            tk.Label(frame, text=item["desc"], font=FONTS["body"], bg=COLORS["bg_sec"], fg=COLORS["text_sec"], anchor="w").pack(fill="x")
            
            col += 1
            if col > 1: # 2 columnas
                col = 0
                row += 1

    def populate_maintenance_tab(self):
        # Esta pestaña es diferente, son botones de acción inmediata
        parent = self.tab_maintenance
        
        tools = [
            ("Reparar Archivos Corruptos (SFC)", "Ejecuta sfc /scannow (Tarda 5-10 min)", self.run_sfc),
            ("Reparar Imagen de Windows (DISM)", "Repara el almacén de componentes.", self.run_dism),
            ("Flush DNS & Reset IP", "Soluciona problemas de conexión.", self.run_net_reset),
            ("Borrar Archivos Temporales", "Libera espacio en disco.", self.run_clean_temp),
        ]
        
        for name, desc, func in tools:
            frame = tk.Frame(parent, bg=COLORS["bg_sec"], padx=20, pady=20)
            frame.pack(fill="x", pady=5)
            
            btn = tk.Button(frame, text="EJECUTAR", bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=5, cursor="hand2", command=func)
            btn.pack(side="right")
            
            tk.Label(frame, text=name, font=FONTS["h2"], bg=COLORS["bg_sec"], fg="white").pack(anchor="w")
            tk.Label(frame, text=desc, font=FONTS["body"], bg=COLORS["bg_sec"], fg=COLORS["text_sec"]).pack(anchor="w")

    def log(self, msg, type="INFO"):
        self.console.config(state='normal')
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        color = COLORS["text_main"]
        if type == "SUCCESS": color = COLORS["success"]
        if type == "ERROR": color = COLORS["danger"]
        
        self.console.insert(tk.END, f"[{timestamp}] ", "gray")
        self.console.insert(tk.END, f"{msg}\n", type)
        self.console.tag_config(type, foreground=color)
        self.console.tag_config("gray", foreground="#666")
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def load_features(self):
        return [
            # --- GAMING ---
            {"id": "ult_perf", "cat": "gaming", "name": "Plan Máximo Rendimiento", "desc": "Desbloquea el plan oculto de energía."},
            {"id": "game_mode", "cat": "gaming", "name": "Forzar Modo Juego", "desc": "Prioriza juegos en la CPU."},
            {"id": "gpu_sched", "cat": "gaming", "name": "GPU Scheduling (HAGS)", "desc": "Reduce latencia de GPU (Requiere Reinicio)."},
            {"id": "fso_disable", "cat": "gaming", "name": "Desactivar Opt. Pantalla Completa", "desc": "Arregla stuttering en juegos viejos."},
            {"id": "mouse_fix", "cat": "gaming", "name": "Fix Aceleración Mouse", "desc": "Desactiva 'Mejorar precisión del puntero' para aim real."},
            {"id": "kb_delay", "cat": "gaming", "name": "Reducir Input Lag Teclado", "desc": "Baja el delay de repetición en el registro."},
            {"id": "power_throt", "cat": "gaming", "name": "Desactivar Power Throttling", "desc": "Evita que Windows baje frecuencias para ahorrar luz."},

            # --- WINDOWS 11 UI ---
            {"id": "classic_ctx", "cat": "win11", "name": "Menú Contextual Clásico", "desc": "Devuelve el clic derecho de Windows 10 (Requiere Reinicio)."},
            {"id": "snap_assist", "cat": "win11", "name": "Desactivar Snap Assist", "desc": "Quita la sugerencia de ventanas molesta."},
            {"id": "widgets_kill", "cat": "win11", "name": "Eliminar Widgets y Chat", "desc": "Libera RAM de la barra de tareas."},
            {"id": "transparency", "cat": "win11", "name": "Desactivar Transparencias", "desc": "Interfaz opaca para mayor rendimiento."},
            
            # --- RED ---
            {"id": "dns_cloud", "cat": "network", "name": "DNS Cloudflare (1.1.1.1)", "desc": "DNS más rápido del mundo."},
            {"id": "tcp_nagle", "cat": "network", "name": "Desactivar Nagle (TCP)", "desc": "Reduce ping enviando paquetes más rápido."},
            {"id": "net_throt", "cat": "network", "name": "Quitar Límite de Red", "desc": "Elimina el throttling de Windows para multimedia."},

            # --- PRIVACIDAD ---
            {"id": "telemetry", "cat": "privacy", "name": "Bloquear Telemetría", "desc": "Detiene el servicio DiagTrack."},
            {"id": "activity", "cat": "privacy", "name": "Sin Historial de Actividad", "desc": "Windows no recordará qué apps abriste."},
            {"id": "location", "cat": "privacy", "name": "Desactivar Geolocalización", "desc": "Impide que apps sepan tu ubicación."},
        ]

    # --- MONITOR DE SISTEMA ---
    def start_monitoring(self):
        def update():
            while True:
                try:
                    cmd = "powershell -NoProfile -Command \"$p = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select -Expand Average; $o = Get-CimInstance Win32_OperatingSystem; $m = (($o.TotalVisibleMemorySize - $o.FreePhysicalMemory)/$o.TotalVisibleMemorySize)*100; Write-Output $p; Write-Output $m\""
                    out = subprocess.check_output(cmd, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW), creationflags=subprocess.CREATE_NO_WINDOW).decode().split('\n')
                    if len(out) >= 2:
                        cpu = int(float(out[0].strip()))
                        ram = int(float(out[1].strip()))
                        if self.root.winfo_exists():
                            self.stats_label.config(text=f"CPU: {cpu}% | RAM: {ram}%", fg=COLORS["danger"] if cpu > 80 else COLORS["success"])
                except: pass
                time.sleep(2)
        threading.Thread(target=update, daemon=True).start()

    # --- LÓGICA DE EJECUCIÓN PRINCIPAL ---
    def run_process(self):
        active = [f for f in self.features if self.vars[f["id"]].get()]
        if not active: return messagebox.showinfo("Info", "Selecciona algo primero.")
        
        if not messagebox.askyesno("Confirmar", f"Aplicar {len(active)} optimizaciones?"): return

        def worker():
            self.log("--- INICIANDO OPTIMIZACIÓN ---")
            
            # SIEMPRE CREAR PUNTO DE RESTAURACIÓN
            self.log("Creando Punto de Restauración...", "INFO")
            SystemUtils.run_ps("Checkpoint-Computer -Description 'DrVicho_v5' -RestorePointType 'MODIFY_SETTINGS'")
            
            total = len(active)
            for i, item in enumerate(active):
                fid = item["id"]
                self.log(f"Aplicando: {item['name']}...")
                
                # --- LÓGICA TWEAKS ---
                if fid == "ult_perf":
                    SystemUtils.run_ps("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61; powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
                
                elif fid == "game_mode":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AllowAutoGameMode", 1, winreg.REG_DWORD)
                
                elif fid == "gpu_sched":
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2, winreg.REG_DWORD)
                
                elif fid == "fso_disable":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", 2, winreg.REG_DWORD)
                
                elif fid == "mouse_fix":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", "0", winreg.REG_SZ)
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold1", "0", winreg.REG_SZ)
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold2", "0", winreg.REG_SZ)

                elif fid == "kb_delay":
                    # Ajustes pro-gamer para teclado
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "KeyboardDelay", "0", winreg.REG_SZ)
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "KeyboardSpeed", "31", winreg.REG_SZ)
                
                elif fid == "power_throt":
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", 1, winreg.REG_DWORD)

                elif fid == "classic_ctx":
                    # El comando mágico para Win11
                    SystemUtils.run_ps('reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve')
                
                elif fid == "snap_assist":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "WindowArrangementActive", "0", winreg.REG_SZ)

                elif fid == "widgets_kill":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa", 0, winreg.REG_DWORD)
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Windows Chat", "ChatIcon", 3, winreg.REG_DWORD)

                elif fid == "transparency":
                    SystemUtils.set_reg(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0, winreg.REG_DWORD)

                elif fid == "dns_cloud":
                    SystemUtils.run_ps("Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ServerAddresses 1.1.1.1, 1.0.0.1")

                elif fid == "tcp_nagle":
                    # Requiere iterar interfaces
                    SystemUtils.run_ps("Get-NetAdapter | ForEach-Object { New-ItemProperty -Path \"HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$($_.InterfaceGuid)\" -Name \"TcpAckFrequency\" -Value 1 -PropertyType DWORD -Force; New-ItemProperty -Path \"HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$($_.InterfaceGuid)\" -Name \"TCPNoDelay\" -Value 1 -PropertyType DWORD -Force }")

                elif fid == "net_throt":
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex", 0xffffffff, winreg.REG_DWORD)

                elif fid == "telemetry":
                    SystemUtils.run_ps("Stop-Service DiagTrack -Force; Set-Service DiagTrack -StartupType Disabled")
                
                elif fid == "activity":
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities", 0, winreg.REG_DWORD)
                
                elif fid == "location":
                    SystemUtils.set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location", "Value", "Deny", winreg.REG_SZ)

                time.sleep(0.1)
            
            self.log("!!! COMPLETADO !!! Reinicia tu PC.", "SUCCESS")
            messagebox.showinfo("DrVicho v5", "Proceso terminado. REINICIA TU PC AHORA.")

        threading.Thread(target=worker, daemon=True).start()

    # --- HERRAMIENTAS MANTENIMIENTO ---
    def run_sfc(self):
        self.log("Iniciando SFC (Esto tarda un rato)...", "WARNING")
        def t():
            SystemUtils.run_ps("sfc /scannow")
            self.log("SFC Finalizado. Revisa si hubo errores.", "SUCCESS")
        threading.Thread(target=t, daemon=True).start()

    def run_dism(self):
        self.log("Iniciando DISM RestoreHealth...", "WARNING")
        def t():
            SystemUtils.run_ps("DISM /Online /Cleanup-Image /RestoreHealth")
            self.log("DISM Finalizado.", "SUCCESS")
        threading.Thread(target=t, daemon=True).start()
    
    def run_net_reset(self):
        SystemUtils.run_ps("netsh int ip reset; ipconfig /flushdns; ipconfig /release; ipconfig /renew")
        self.log("Red reseteada y DNS limpiada.", "SUCCESS")

    def run_clean_temp(self):
        SystemUtils.run_ps("Remove-Item -Path $env:TEMP\* -Recurse -Force -ErrorAction SilentlyContinue")
        self.log("Archivos Temporales eliminados.", "SUCCESS")

if __name__ == "__main__":
    if SystemUtils.is_admin():
        root = tk.Tk()
        app = DrVichoApp(root)
        root.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    
