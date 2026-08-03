import os
import subprocess
import webbrowser  
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import minecraft_launcher_lib

CARPETA_MINECRAFT = os.path.abspath("./datos_minecraft")

print("Conectando con Mojang para listar versiones...")
try:
    lista_completa = minecraft_launcher_lib.utils.get_version_list()
    versiones_disponibles = [v["id"] for v in lista_completa if v["type"] == "release"]
except Exception:
    versiones_disponibles = ["1.21.1", "1.20.1", "1.16.5", "1.8.9"]

def lanzar_juego():
    username = entrada_usuario.get().strip()
    version_seleccionada = combo_versiones.get()
    tipo_juego = combo_tipo.get()
    sistema_skins = combo_skins.get()
    
    if not username or username == "Introduce tu Nickname...":
        messagebox.showerror("Z3spr1 Dashboard", "Por favor, escribe un nombre de usuario válido.")
        return
    
    boton_jugar.config(text="CARGANDO...", state="disabled", bg="#16a085")
    ventana.update()
    
    try:
        argumentos_jvm = ["-Xmx2G", "-Xms1G"]
        
        if "Ely.by" in sistema_skins:
            argumentos_jvm.extend([
                "-Dminecraft.api.auth.host=https://ely.by",
                "-Dminecraft.api.account.host=https://ely.by",
                "-Dminecraft.api.session.host=https://ely.by",
                "-Dminecraft.api.services.host=https://ely.by"
            ])

        opciones = {
            "username": username,
            "uuid": "00000000-0000-0000-0000-000000000000",
            "token": "00000000000000000000000000000000",
            "jvmArguments": argumentos_jvm
        }
        
        minecraft_launcher_lib.install.install_minecraft_version(version_seleccionada, CARPETA_MINECRAFT)
        
        if "Fabric" in tipo_juego:
            minecraft_launcher_lib.fabric.install_fabric(version_seleccionada, CARPETA_MINECRAFT)
            lista_versiones = minecraft_launcher_lib.utils.get_installed_versions(CARPETA_MINECRAFT)
            versiones_fabric = [v["id"] for v in lista_versiones if "fabric-loader" in v["id"] and version_seleccionada in v["id"]]
            if not versiones_fabric:
                raise Exception("Fabric no disponible")
            version_a_ejecutar = versiones_fabric
        else:
            version_a_ejecutar = version_seleccionada
            
        comando = minecraft_launcher_lib.command.get_minecraft_command(version_a_ejecutar, CARPETA_MINECRAFT, opciones)
        ventana.withdraw()
        subprocess.run(comando)
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar: {str(e)}")
    finally:
        ventana.deiconify()
        boton_jugar.config(text="¡INICIAR MINECRAFT!", state="normal", bg="#2ecc71")

# --- FUNCIONES INTERACTIVAS ---
def abrir_web_skins(e):
    webbrowser.open("https://ely.by") 

def al_entrar_boton(e):
    if boton_jugar['state'] == 'normal':
        boton_jugar.config(bg="#27ae60", cursor="hand2")

def al_salir_boton(e):
    if boton_jugar['state'] == 'normal':
        boton_jugar.config(bg="#2ecc71")

def al_entrar_enlace(e):
    enlace_skins.config(fg="#00e676", cursor="hand2") # Cambia a verde brillante al pasar el ratón

def al_salir_enlace(e):
    enlace_skins.config(fg="#00b0ff") # Vuelve al azul del hipervínculo

def limpiar_placeholder(e):
    if entrada_usuario.get() == "Introduce tu Nickname...":
        entrada_usuario.delete(0, tk.END)
        entrada_usuario.config(fg="#ffffff")

def restaurar_placeholder(e):
    if not entrada_usuario.get().strip():
        entrada_usuario.insert(0, "Introduce tu Nickname...")
        entrada_usuario.config(fg="#7f8c8d")

# --- CONFIGURACIÓN DE LA INTERFAZ ---
ventana = tk.Tk()
ventana.title("Z3spr1 Dashboard Pro v1.7") 
ventana.geometry("450x560") 
ventana.configure(bg="#0f172a") # Fondo Azul Medianoche Oscuro
ventana.resizable(False, False)

# NUEVO DISEÑO PREMIUM PARA LOS MENÚS DESPLEGABLES (COMBOBOX)
estilo = ttk.Style()
estilo.theme_use('clam')

# Configuración del fondo, letras y bordes del menú desplegable cerrado
estilo.configure("TCombobox", 
                 fieldbackground="#1e293b",  # Fondo de la caja (Gris oscuro/azul)
                 background="#1e293b",       # Fondo del botón de la flecha
                 foreground="#ffffff",       # Color del texto seleccionado (Blanco)
                 arrowcolor="#00b0ff",       # Color de la flecha desplegable (Cian neón)
                 bordercolor="#334155",      # Borde sutil exterior
                 lightcolor="#1e293b",
                 darkcolor="#1e293b")

# Configuración del color cuando pasas el ratón por encima del menú
estilo.map("TCombobox", 
           fieldbackground=[("readonly", "#1e293b"), ("focus", "#334155")],
           foreground=[("readonly", "#ffffff")],
           background=[("readonly", "#1e293b"), ("active", "#334155")],
           arrowcolor=[("readonly", "#00b0ff"), ("active", "#00e676")]) # La flecha brilla en verde al tocarla

# Aplicar el estilo oscuro a la lista desplegable interna de Windows (La lista de opciones flotante)
ventana.option_add("*TCombobox*Listbox.background", "#1e293b")
ventana.option_add("*TCombobox*Listbox.foreground", "#ffffff")
ventana.option_add("*TCombobox*Listbox.selectBackground", "#00b0ff")
ventana.option_add("*TCombobox*Listbox.selectForeground", "#000000")

# Encabezado Principal
titulo = tk.Label(ventana, text="Z3SPR1 CLIENT", font=("Segoe UI", 22, "bold"), fg="#ffffff", bg="#0f172a")
titulo.pack(pady=(25, 5))

marco = tk.Frame(ventana, bg="#0f172a")
marco.pack(pady=10)

# Campo de Usuario
tk.Label(marco, text="APODO DEL JUGADOR", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(anchor="w", padx=45)
entrada_usuario = tk.Entry(marco, font=("Segoe UI", 12), width=28, bg="#1e293b", fg="#7f8c8d", bd=0, insertbackground="white", justify="center")
entrada_usuario.pack(pady=(5, 15), ipady=6)
entrada_usuario.insert(0, "Introduce tu Nickname...")
entrada_usuario.bind("<FocusIn>", limpiar_placeholder)
entrada_usuario.bind("<FocusOut>", restaurar_placeholder)

# Selector de Versión (Aplica el estilo nuevo automáticamente)
tk.Label(marco, text="VERSIÓN REQUERIDA", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(anchor="w", padx=45)
combo_versiones = ttk.Combobox(marco, values=versiones_disponibles, font=("Segoe UI", 11), width=28, state="readonly")
combo_versiones.pack(pady=(5, 15), ipady=4)
combo_versiones.current(0)

# Selector de Motor de Juego (Aplica el estilo nuevo automáticamente)
tk.Label(marco, text="NÚCLEO DEL JUEGO", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(anchor="w", padx=45)
combo_tipo = ttk.Combobox(marco, values=["Vanilla (Original / Limpio)", "Fabric (Soporte para Mods)"], font=("Segoe UI", 11), width=28, state="readonly")
combo_tipo.pack(pady=(5, 15), ipady=4)
combo_tipo.current(0)

# Selector de Skins (Aplica el estilo nuevo automáticamente)
tk.Label(marco, text="SISTEMA DE ASPECTOS", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(anchor="w", padx=45)
combo_skins = ttk.Combobox(marco, values=["Oficial (Mojang Base)", "Ely.by (Cargar Skins No-Prem)"], font=("Segoe UI", 11), width=28, state="readonly")
combo_skins.pack(pady=(5, 5), ipady=4)
combo_skins.current(1)

# Enlace Web de Skins
enlace_skins = tk.Label(marco, text="¿No tienes cuenta? Registra tu skin aquí", 
                        font=("Segoe UI", 9, "underline"), fg="#00b0ff", bg="#0f172a")
enlace_skins.pack(pady=(0, 15))
enlace_skins.bind("<Button-1>", abrir_web_skins)
enlace_skins.bind("<Enter>", al_entrar_enlace)
enlace_skins.bind("<Leave>", al_salir_enlace)

# Botón de juego Verde Esmeralda
boton_jugar = tk.Button(ventana, text="¡INICIAR MINECRAFT!", font=("Segoe UI", 12, "bold"), 
                        bg="#2ecc71", fg="#ffffff", activebackground="#27ae60", activeforeground="#ffffff",
                        width=24, height=2, bd=0, relief="flat")
boton_jugar.config(command=lanzar_juego)
boton_jugar.pack(pady=(5, 10))

boton_jugar.bind("<Enter>", al_entrar_boton)
boton_jugar.bind("<Leave>", al_salir_boton)

nota_seguridad = tk.Label(ventana, text="🛡️ Verificado: Entorno seguro de código abierto.", 
                          font=("Segoe UI", 8), fg="#475569", bg="#0f172a")
nota_seguridad.pack(side="bottom", pady=15)

ventana.mainloop()

