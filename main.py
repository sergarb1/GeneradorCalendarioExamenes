#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║            GENERADOR HORARIS EXÀMENS - PUNTO DE ENTRADA            ║
╠══════════════════════════════════════════════════════════════════════╣
║  Este es el archivo principal de la aplicación. Cuando ejecutas    ║
║  "python main.py" desde la terminal, este archivo es el primero    ║
║  que se ejecuta. Su trabajo es:                                    ║
║                                                                     ║
║  1. Configurar el PATH para que Python encuentre los módulos       ║
║  2. Crear la aplicación PyQt6                                      ║
║  3. Aplicar el estilo "Fusion" (moderno y multiplataforma)         ║
║  4. Crear y mostrar la ventana principal                           ║
║  5. Iniciar el bucle de eventos (loop principal de la GUI)         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sys      # sys.argv contiene los argumentos de línea de comandos
import os       # os.path para manejar rutas de archivos

# ──────────────────────────────────────────────────────────────────────────────
# Añadimos la carpeta raíz del proyecto al PATH de Python
# Esto es necesario para que los "import" de gui.py, scheduler.py, etc.
# funcionen correctamente aunque se ejecute desde otra ubicación.
# ──────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importamos la clase QApplication de PyQt6, que es el corazón de toda
# aplicación gráfica con Qt. Gestiona el bucle de eventos, la configuración
# global (como los estilos) y los argumentos de línea de comandos.
from PyQt6.QtWidgets import QApplication

# Importamos nuestra clase App (la ventana principal) desde el módulo gui.py
from gui import App


def main():
    """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  Función principal: arranca toda la aplicación                     ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Este es el flujo de arranque:
    
    1. Creamos QApplication, que es OBLIGATORIO en toda aplicación PyQt6.
       Sin ella, no se pueden crear ventanas ni widgets. Recibe los
       argumentos de la línea de comandos (por ejemplo, si el usuario
       pasa argumentos al script).
    
    2. Aplicamos el estilo "Fusion". Qt trae varios estilos integrados:
       - "Fusion": moderno, limpio, consistente en Windows/Mac/Linux
       - "Windows": imita el estilo clásico de Windows
       - "macOS": imita el estilo de macOS
       Nosotros usamos Fusion porque se ve bien en todos los sistemas
       y combina perfectamente con nuestro tema personalizado (QSS).
    
    3. Creamos nuestra ventana principal (App) y la mostramos con show().
       La clase App hereda de QMainWindow y define toda la interfaz:
       pestañas, botones, listas, etc.
    
    4. app.exec() inicia el bucle de eventos (event loop). Este bucle
       se queda ejecutándose indefinidamente, procesando clics del ratón,
       pulsaciones de teclado, actualizaciones de pantalla, etc.
       Cuando el usuario cierra la ventana, app.exec() termina y
       sys.exit() devuelve el código de salida al sistema operativo.
    """
    
    # Paso 1: Crear la aplicación Qt
    # QApplication(sys.argv) le dice a Qt que procese los argumentos
    # de línea de comandos (por ejemplo, --style, --display, etc.)
    app = QApplication(sys.argv)
    
    # Paso 2: Estilo Fusion — aspecto moderno y uniforme
    # Este estilo se aplica a TODOS los widgets de la aplicación.
    # Luego, en gui.py, aplicaremos nuestras propias hojas de estilo
    # (QSS) para personalizar colores, bordes, etc.
    app.setStyle("Fusion")
    
    # Paso 3: Crear y mostrar la ventana principal
    # App() es nuestra clase personalizada que hereda de QMainWindow.
    # Dentro del constructor (__init__) se construye toda la interfaz:
    # la barra superior, las pestañas, los formularios, etc.
    window = App()
    
    # show() hace visible la ventana. Sin esto, la ventana existe
    # en memoria pero no se ve en pantalla.
    window.show()
    
    # Paso 4: Bucle de eventos
    # app.exec() se queda bloqueado hasta que el usuario cierra la app.
    # Cuando eso ocurre, devuelve un código de salida (0 = bien, > 0 = error)
    # sys.exit() termina el proceso con ese código.
    sys.exit(app.exec())


# ──────────────────────────────────────────────────────────────────────────────
# Este bloque es el punto de entrada estándar de Python.
# Cuando ejecutas "python main.py", Python asigna "__main__" a la variable
# __name__. Si el archivo se importara desde otro sitio (ej: "import main"),
# __name__ valdría "main" y este bloque no se ejecutaría.
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
