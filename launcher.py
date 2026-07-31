"""Z3spr1 Client - Lanzador de Minecraft (Vanilla / Fabric).

La descarga y la ejecucion del juego corren en un hilo aparte para que la
ventana nunca se congele; el hilo solo publica eventos y la interfaz se
actualiza siempre desde el hilo principal de Tkinter.
"""

import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
import uuid
import webbrowser
from tkinter import messagebox, ttk

try:
    import minecraft_launcher_lib as mll
except ImportError:
    tk.Tk().withdraw()
    messagebox.showerror(
        "Z3spr1 Client",
        "Falta la libreria 'minecraft_launcher_lib'.\n\n"
        "Abre una consola y ejecuta:\n    pip install minecraft-launcher-lib",
    )
    sys.exit(1)

# --- RUTAS (siempre relativas al script, no al directorio de trabajo) ---
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_MINECRAFT = os.path.join(DIR_BASE, "datos_minecraft")
ARCHIVO_CONFIG = os.path.join(DIR_BASE, "config.json")
ARCHIVO_ICONO = os.path.join(DIR_BASE, "icono.ico.ico")

# --- CONSTANTES ---
PLACEHOLDER = "Introduce tu Nickname..."
VERSIONES_FALLBACK = ["1.21.1", "1.20.1", "1.16.5", "1.8.9"]
REGEX_USUARIO = re.compile(r"^[A-Za-z0-9_]{3,16}$")
OPCIONES_RAM = ["2 GB", "3 GB", "4 GB", "6 GB", "8 GB", "12 GB", "16 GB"]
NUCLEOS = ["Vanilla (Original / Limpio)", "Fabric (Soporte para Mods)"]
SKINS = ["Oficial (Mojang Base)", "Ely.by (Cargar Skins No-Prem)"]
HOSTS_ELY = ["auth", "account", "session", "services"]

# Flags de recoleccion de basura que reducen los tirones dentro del juego.
ARGUMENTOS_JVM_BASE = [
    "-XX:+UnlockExperimentalVMOptions",
    "-XX:+UseG1GC",
    "-XX:+ParallelRefProcEnabled",
    "-XX:MaxGCPauseMillis=50",
    "-XX:G1NewSizePercent=20",
    "-XX:G1HeapRegionSize=32M",
]

# --- PALETA ---
C = {
    "fondo": "#0f172a",
    "panel": "#1e293b",
    "borde": "#334155",
    "texto": "#ffffff",
    "tenue": "#94a3b8",
    "apagado": "#475569",
    "gris": "#7f8c8d",
    "acento": "#00b0ff",
    "brillo": "#00e676",
    "boton": "#2ecc71",
    "boton_hover": "#27ae60",
    "boton_off": "#16a085",
}
FUENTE = "Segoe UI"


class ErrorLanzador(Exception):
    """Fallo esperado y explicable para el usuario."""


def uuid_offline(username):
    """Reproduce java.util.UUID.nameUUIDFromBytes("OfflinePlayer:<nombre>").

    Da a cada jugador un UUID estable, de modo que el inventario y los permisos
    sobreviven entre partidas (el original usaba ceros para todo el mundo).
    """
    datos = bytearray(hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).digest())
    datos[6] = (datos[6] & 0x0F) | 0x30  # version 3
    datos[8] = (datos[8] & 0x3F) | 0x80  # variante IETF
    return str(uuid.UUID(bytes=bytes(datos)))


def clave_version(texto):
    """Ordena '0.16.10' por encima de '0.16.9' (comparar cadenas no lo hace)."""
    return tuple(int(t) if t.isdigit() else 0 for t in re.split(r"[._-]", texto))


def ram_recomendada():
    """RAM total del equipo / 4, redondeada a una opcion de la lista."""
    try:
        import ctypes

        class Estado(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        estado = Estado()
        estado.dwLength = ctypes.sizeof(Estado)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado))
        total_gb = estado.ullTotalPhys / (1024 ** 3)
        objetivo = max(2, int(total_gb // 2))
    except Exception:
        objetivo = 4
    validas = [int(o.split()[0]) for o in OPCIONES_RAM]
    return f"{min(validas, key=lambda gb: (abs(gb - objetivo), gb))} GB"


def cargar_config():
    try:
        with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


class Lanzador:
    def __init__(self):
        self.config = cargar_config()
        self.eventos = queue.Queue()          # hilo de trabajo -> interfaz
        self.candado = threading.Lock()
        self.progreso = {"texto": "", "valor": 0, "maximo": 0}
        self.ocupado = False
        self._construir_interfaz()
        self._bombear_eventos()
        threading.Thread(target=self._buscar_versiones, daemon=True).start()

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _construir_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title("Z3spr1 Dashboard Pro v1.8")
        self.ventana.configure(bg=C["fondo"])
        self.ventana.resizable(False, False)
        self.ventana.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        if os.path.exists(ARCHIVO_ICONO):
            try:
                self.ventana.iconbitmap(ARCHIVO_ICONO)
            except tk.TclError:
                pass

        self._aplicar_estilos()

        tk.Label(self.ventana, text="Z3SPR1 CLIENT", font=(FUENTE, 22, "bold"),
                 fg=C["texto"], bg=C["fondo"]).pack(pady=(25, 5))

        marco = tk.Frame(self.ventana, bg=C["fondo"])
        marco.pack(pady=10)

        self._etiqueta(marco, "APODO DEL JUGADOR")
        self.entrada_usuario = tk.Entry(marco, font=(FUENTE, 12), width=28, bg=C["panel"],
                                        fg=C["gris"], bd=0, insertbackground=C["texto"],
                                        justify="center")
        self.entrada_usuario.pack(pady=(5, 15), ipady=6)
        self.entrada_usuario.bind("<FocusIn>", self._limpiar_placeholder)
        self.entrada_usuario.bind("<FocusOut>", self._restaurar_placeholder)
        self.entrada_usuario.bind("<Return>", lambda _e: self._al_pulsar_jugar())
        self._poner_usuario(self.config.get("username", ""))

        self.combo_versiones = self._desplegable(marco, "VERSION REQUERIDA", VERSIONES_FALLBACK)
        self.combo_nucleo = self._desplegable(marco, "NUCLEO DEL JUEGO", NUCLEOS)
        self.combo_ram = self._desplegable(marco, "MEMORIA ASIGNADA", OPCIONES_RAM)
        self.combo_skins = self._desplegable(marco, "SISTEMA DE ASPECTOS", SKINS, relleno_inferior=5)

        self._seleccionar(self.combo_nucleo, self.config.get("nucleo"), NUCLEOS[0])
        self._seleccionar(self.combo_ram, self.config.get("ram"), ram_recomendada())
        self._seleccionar(self.combo_skins, self.config.get("skins"), SKINS[1])

        self.enlace_skins = tk.Label(marco, text="No tienes cuenta? Registra tu skin aqui",
                                     font=(FUENTE, 9, "underline"), fg=C["acento"], bg=C["fondo"])
        self.enlace_skins.pack(pady=(0, 15))
        self.enlace_skins.bind("<Button-1>", lambda _e: webbrowser.open("https://ely.by"))
        self.enlace_skins.bind("<Enter>", lambda _e: self.enlace_skins.config(fg=C["brillo"], cursor="hand2"))
        self.enlace_skins.bind("<Leave>", lambda _e: self.enlace_skins.config(fg=C["acento"]))

        self.boton_jugar = tk.Button(self.ventana, text="INICIAR MINECRAFT", font=(FUENTE, 12, "bold"),
                                     bg=C["boton"], fg=C["texto"], activebackground=C["boton_hover"],
                                     activeforeground=C["texto"], width=24, height=2, bd=0,
                                     relief="flat", command=self._al_pulsar_jugar)
        self.boton_jugar.pack(pady=(5, 8))
        self.boton_jugar.bind("<Enter>", lambda _e: self._resaltar_boton(True))
        self.boton_jugar.bind("<Leave>", lambda _e: self._resaltar_boton(False))

        self.barra = ttk.Progressbar(self.ventana, style="Z3.Horizontal.TProgressbar",
                                     length=300, mode="determinate")
        self.etiqueta_estado = tk.Label(self.ventana, text="Buscando versiones disponibles...",
                                        font=(FUENTE, 8), fg=C["tenue"], bg=C["fondo"],
                                        wraplength=400)
        self.etiqueta_estado.pack(pady=(0, 4))

        tk.Label(self.ventana, text="Verificado: entorno seguro de codigo abierto.",
                 font=(FUENTE, 8), fg=C["apagado"], bg=C["fondo"]).pack(side="bottom", pady=12)

        # El alto se calcula tras empaquetar para que nada quede recortado.
        self.ventana.update_idletasks()
        self.ventana.geometry(f"460x{self.ventana.winfo_reqheight() + 12}")

    def _aplicar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TCombobox", fieldbackground=C["panel"], background=C["panel"],
                         foreground=C["texto"], arrowcolor=C["acento"], bordercolor=C["borde"],
                         lightcolor=C["panel"], darkcolor=C["panel"])
        estilo.map("TCombobox",
                   fieldbackground=[("readonly", C["panel"]), ("focus", C["borde"])],
                   foreground=[("readonly", C["texto"])],
                   background=[("readonly", C["panel"]), ("active", C["borde"])],
                   arrowcolor=[("readonly", C["acento"]), ("active", C["brillo"])])
        estilo.configure("Z3.Horizontal.TProgressbar", troughcolor=C["panel"],
                         background=C["acento"], bordercolor=C["panel"],
                         lightcolor=C["acento"], darkcolor=C["acento"])
        # Lista flotante del desplegable (widget nativo, solo acepta option_add).
        self.ventana.option_add("*TCombobox*Listbox.background", C["panel"])
        self.ventana.option_add("*TCombobox*Listbox.foreground", C["texto"])
        self.ventana.option_add("*TCombobox*Listbox.selectBackground", C["acento"])
        self.ventana.option_add("*TCombobox*Listbox.selectForeground", "#000000")

    def _etiqueta(self, padre, texto):
        tk.Label(padre, text=texto, font=(FUENTE, 8, "bold"), fg=C["tenue"],
                 bg=C["fondo"]).pack(anchor="w", padx=45)

    def _desplegable(self, padre, titulo, valores, relleno_inferior=15):
        self._etiqueta(padre, titulo)
        combo = ttk.Combobox(padre, values=valores, font=(FUENTE, 11), width=28, state="readonly")
        combo.pack(pady=(5, relleno_inferior), ipady=4)
        if valores:
            combo.current(0)
        return combo

    @staticmethod
    def _seleccionar(combo, valor, por_defecto):
        opciones = combo.cget("values")
        combo.set(valor if valor in opciones else por_defecto)

    def _resaltar_boton(self, encima):
        if self.boton_jugar["state"] == "normal":
            self.boton_jugar.config(bg=C["boton_hover"] if encima else C["boton"],
                                    cursor="hand2" if encima else "")

    # --- Placeholder del nombre de usuario ---
    def _poner_usuario(self, valor):
        self.entrada_usuario.delete(0, tk.END)
        if valor:
            self.entrada_usuario.insert(0, valor)
            self.entrada_usuario.config(fg=C["texto"])
        else:
            self.entrada_usuario.insert(0, PLACEHOLDER)
            self.entrada_usuario.config(fg=C["gris"])

    def _limpiar_placeholder(self, _evento=None):
        if self.entrada_usuario.get() == PLACEHOLDER:
            self.entrada_usuario.delete(0, tk.END)
            self.entrada_usuario.config(fg=C["texto"])

    def _restaurar_placeholder(self, _evento=None):
        # delete() antes de insertar: si no, el placeholder se pega a los espacios.
        if not self.entrada_usuario.get().strip():
            self._poner_usuario("")

    def _usuario(self):
        texto = self.entrada_usuario.get().strip()
        return "" if texto == PLACEHOLDER else texto

    # ------------------------------------------------------------------
    # Lista de versiones (en segundo plano: la ventana abre al instante)
    # ------------------------------------------------------------------
    def _buscar_versiones(self):
        try:
            lista = mll.utils.get_version_list()
            versiones = [v["id"] for v in lista if v["type"] == "release"]
            if not versiones:
                raise ErrorLanzador("respuesta vacia")
            self.eventos.put(("versiones", (versiones, None)))
        except Exception:
            self.eventos.put(("versiones", (VERSIONES_FALLBACK, "Sin conexion con Mojang: lista local.")))

    def _aplicar_versiones(self, versiones, aviso):
        self.combo_versiones["values"] = versiones
        self._seleccionar(self.combo_versiones, self.config.get("version"), versiones[0])
        self.etiqueta_estado.config(text=aviso or "Listo.",
                                    fg=C["gris"] if aviso else C["tenue"])

    # ------------------------------------------------------------------
    # Lanzamiento
    # ------------------------------------------------------------------
    def _al_pulsar_jugar(self):
        if self.ocupado:
            return
        username = self._usuario()
        if not REGEX_USUARIO.match(username):
            messagebox.showerror(
                "Z3spr1 Dashboard",
                "El apodo debe tener entre 3 y 16 caracteres y usar solo\n"
                "letras, numeros o guion bajo (_).",
            )
            return

        self.ocupado = True
        self.boton_jugar.config(text="CARGANDO...", state="disabled", bg=C["boton_off"], cursor="")
        self.barra.pack(before=self.etiqueta_estado, pady=(0, 6))
        self.barra.config(value=0, maximum=100)
        self.etiqueta_estado.config(text="Preparando...", fg=C["tenue"])
        self._guardar_config(username)

        hilo = threading.Thread(
            target=self._trabajo_lanzamiento,
            args=(username, self.combo_versiones.get(), "Fabric" in self.combo_nucleo.get(),
                  "Ely.by" in self.combo_skins.get(), int(self.combo_ram.get().split()[0])),
            daemon=True,
        )
        hilo.start()

    def _guardar_config(self, username):
        datos = {
            "username": username,
            "version": self.combo_versiones.get(),
            "nucleo": self.combo_nucleo.get(),
            "ram": self.combo_ram.get(),
            "skins": self.combo_skins.get(),
        }
        try:
            with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # que no poder guardar preferencias nunca impida jugar

    def _callback_progreso(self):
        """Callbacks de minecraft_launcher_lib: solo tocan estado compartido."""
        def fijar(clave):
            def establecer(valor):
                with self.candado:
                    self.progreso[clave] = valor
            return establecer
        return {"setStatus": fijar("texto"), "setProgress": fijar("valor"), "setMax": fijar("maximo")}

    def _trabajo_lanzamiento(self, username, version, usar_fabric, usar_ely, ram_gb):
        try:
            os.makedirs(CARPETA_MINECRAFT, exist_ok=True)
            callback = self._callback_progreso()
            mll.install.install_minecraft_version(version, CARPETA_MINECRAFT, callback=callback)
            version_final = self._preparar_fabric(version, callback) if usar_fabric else version

            argumentos = [f"-Xmx{ram_gb}G", f"-Xms{min(ram_gb, 2)}G"] + list(ARGUMENTOS_JVM_BASE)
            if usar_ely:
                argumentos += [f"-Dminecraft.api.{h}.host=https://ely.by" for h in HOSTS_ELY]

            comando = mll.command.get_minecraft_command(version_final, CARPETA_MINECRAFT, {
                "username": username,
                "uuid": uuid_offline(username),
                "token": "0" * 32,
                "jvmArguments": argumentos,
            })

            self.eventos.put(("jugando", None))
            proceso = subprocess.run(comando, cwd=CARPETA_MINECRAFT)
            if proceso.returncode != 0:
                raise ErrorLanzador(
                    f"Minecraft se cerro con el codigo {proceso.returncode}.\n"
                    "Revisa la consola o datos_minecraft/logs para ver el detalle."
                )
        except ErrorLanzador as e:
            self.eventos.put(("error", str(e)))
        except Exception as e:
            self.eventos.put(("error", f"{type(e).__name__}: {e}"))
        finally:
            self.eventos.put(("fin", None))

    def _preparar_fabric(self, version, callback):
        if not mll.fabric.is_minecraft_version_supported(version):
            raise ErrorLanzador(f"Fabric todavia no soporta Minecraft {version}.")
        perfil = self._perfil_fabric(version)
        if perfil is None:
            mll.fabric.install_fabric(version, CARPETA_MINECRAFT, callback=callback)
            perfil = self._perfil_fabric(version)
        if perfil is None:
            raise ErrorLanzador("Fabric se instalo pero no se encontro su perfil de version.")
        return perfil

    @staticmethod
    def _perfil_fabric(version):
        """Perfil Fabric instalado con el loader mas alto para esta version."""
        prefijo, sufijo = "fabric-loader-", f"-{version}"
        candidatos = [v["id"] for v in mll.utils.get_installed_versions(CARPETA_MINECRAFT)
                      if v["id"].startswith(prefijo) and v["id"].endswith(sufijo)]
        if not candidatos:
            return None
        return max(candidatos, key=lambda i: clave_version(i[len(prefijo):-len(sufijo)]))

    # ------------------------------------------------------------------
    # Puente hilo -> interfaz (unico punto que toca los widgets)
    # ------------------------------------------------------------------
    def _bombear_eventos(self):
        while True:
            try:
                nombre, dato = self.eventos.get_nowait()
            except queue.Empty:
                break
            if nombre == "versiones":
                self._aplicar_versiones(*dato)
            elif nombre == "jugando":
                self.etiqueta_estado.config(text="Minecraft en ejecucion...")
                self.ventana.withdraw()
            elif nombre == "error":
                self.ventana.deiconify()  # nunca mostrar un dialogo sin su ventana
                messagebox.showerror("Z3spr1 Client", f"No se pudo iniciar:\n\n{dato}")
            elif nombre == "fin":
                self._restablecer()

        if self.ocupado:
            with self.candado:
                texto, valor, maximo = (self.progreso["texto"], self.progreso["valor"],
                                        self.progreso["maximo"])
            if maximo > 0:
                self.barra.config(maximum=maximo, value=valor)
                porcentaje = f"  ({valor * 100 // maximo}%)"
            else:
                porcentaje = ""
            if texto:
                self.etiqueta_estado.config(text=f"{texto[:70]}{porcentaje}")

        self.ventana.after(120, self._bombear_eventos)

    def _restablecer(self):
        self.ocupado = False
        with self.candado:
            self.progreso.update({"texto": "", "valor": 0, "maximo": 0})
        self.ventana.deiconify()
        self.barra.pack_forget()
        self.etiqueta_estado.config(text="Listo.", fg=C["tenue"])
        self.boton_jugar.config(text="INICIAR MINECRAFT", state="normal", bg=C["boton"])

    def _al_cerrar(self):
        if self.ocupado and not messagebox.askokcancel(
            "Z3spr1 Client", "Hay una descarga o partida en curso. Cerrar de todas formas?"
        ):
            return
        self.ventana.destroy()

    def ejecutar(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    Lanzador().ejecutar()
