import streamlit as st
from frontend import StreamlitApp

# Configuración básica de página (debe ser la primera llamada a Streamlit)
# Nota: StreamlitApp.__init__ ya tiene set_page_config, así que instanciamos primero.

if __name__ == "__main__":
    # Instanciar el Agente Diseñador
    app = StreamlitApp()

    # Ejecutar la aplicación
    app.run()
