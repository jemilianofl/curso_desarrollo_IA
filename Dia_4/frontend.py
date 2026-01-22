import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from backend import ProcesadorExcel, CalculadoraIPR, DatosCurvas


# =============================================================================
# AGENTE 3: EL DISEÑADOR (Frontend & Visualización)
# =============================================================================
class StreamlitApp:
    """
    Gestiona la interfaz de usuario y la orquestación de la aplicación.
    """

    def __init__(self):
        st.set_page_config(
            page_title="IPR Modeling System", layout="wide", page_icon="📈"
        )

    def render_sidebar(self):
        """
        Renderiza la barra lateral para configurar la aplicación.
        Retorna el archivo subido y la curva seleccionada.
        """
        st.sidebar.header("Configuración")

        # Carga de archivo
        uploaded_file = st.sidebar.file_uploader(
            "Cargar Excel con datos de Pozo", type=["xlsx", "xls"]
        )

        # Selector de Curva
        # Obtenemos las claves del diccionario de curvas
        opciones_curvas = list(DatosCurvas.CURVAS.keys())
        # Buscamos "Curva 0.85" por defecto si existe, si no la primera
        idx_defecto = 0
        if "Curva 0.85" in opciones_curvas:
            idx_defecto = opciones_curvas.index("Curva 0.85")

        curva_seleccionada = st.sidebar.selectbox(
            "Seleccionar Curva IPR Base", opciones_curvas, index=idx_defecto
        )

        return uploaded_file, curva_seleccionada

    def render_metrics(self, fila_datos):
        """
        Muestra las métricas principales del pozo seleccionado en la parte superior.
        """
        st.subheader(f"Datos del Pozo ({fila_datos.get('Fecha', 'Fecha desconocida')})")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Intervalo Medio", f"{fila_datos['Intervalo medio']:.2f} m")
        col2.metric("Pws (Calculada)", f"{fila_datos['Pws_Final']:.2f} kg/cm²")
        col3.metric("Pwf (Calculada)", f"{fila_datos['Pwf_Final']:.2f} kg/cm²")
        col4.metric("Qo Test", f"{fila_datos['Qo (BPD)']:.2f} BPD")

        # Calculamos el Drawdown rápido para mostrar
        drawdown = fila_datos["Pws_Final"] - fila_datos["Pwf_Final"]
        col5.metric("Drawdown", f"{drawdown:.2f} kg/cm²")

        st.markdown("---")

    def render_charts(self, tabla, fila_datos, z_val, ratio_val, curva_nombre):
        """
        Genera y muestra las gráficas con Plotly.
        """
        col_graf1, col_graf2 = st.columns(2)

        # --- Gráfico 1: Adimensional ---
        with col_graf1:
            fig1 = go.Figure()

            # Pintar todas las curvas de fondo
            for nombre, puntos in DatosCurvas.CURVAS.items():
                pts = sorted(puntos, key=lambda x: x[0])
                x = [p[0] for p in pts]  # Pwf/Pws
                y = [p[1] for p in pts]  # Qo/Qmax

                es_seleccionada = nombre == curva_nombre
                color = "blue" if es_seleccionada else "gray"
                opacity = 1.0 if es_seleccionada else 0.3
                width = 3 if es_seleccionada else 1

                fig1.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        mode="lines",
                        name=nombre,
                        line=dict(color=color, width=width),
                        opacity=opacity,
                    )
                )

            # Punto operativo
            fig1.add_trace(
                go.Scatter(
                    x=[ratio_val],
                    y=[z_val],
                    mode="markers",
                    name="Punto Test",
                    marker=dict(color="red", size=12, symbol="circle"),
                )
            )

            # Layout
            fig1.update_scenes(
                xaxis_autorange="reversed"
            )  # No funciona en 2D, usar update_xaxes
            fig1.update_xaxes(autorange="reversed", title="Pwf / Pws")
            fig1.update_yaxes(title="Qo / Qmax")
            fig1.update_layout(
                title="Curvas IPR Adimensionales",
                legend=dict(x=0.01, y=0.01),
                margin=dict(l=20, r=20, t=40, b=20),
            )

            st.plotly_chart(fig1, use_container_width=True)

        # --- Gráfico 2: IPR Real ---
        with col_graf2:
            fig2 = go.Figure()

            # Curva calculada
            fig2.add_trace(
                go.Scatter(
                    x=tabla["Qo (BPD)"],
                    y=tabla["Pwf"],
                    mode="lines+markers",
                    name=f"IPR {curva_nombre}",
                    line=dict(color="royalblue", width=3),
                )
            )

            # Punto de aforo original
            fig2.add_trace(
                go.Scatter(
                    x=[fila_datos["Qo (BPD)"]],
                    y=[fila_datos["Pwf_Final"]],
                    mode="markers",
                    name="Dato Aforo",
                    marker=dict(color="green", size=12, symbol="diamond"),
                )
            )

            fig2.update_layout(
                title="Curva IPR Real Calculada",
                xaxis_title="Caudal Qo (BPD)",
                yaxis_title="Presión Pwf (kg/cm²)",
                margin=dict(l=20, r=20, t=40, b=20),
            )

            st.plotly_chart(fig2, use_container_width=True)

    def run(self):
        st.title("Sistema de Modelado IPR")
        st.markdown(
            "*Generación automática de curvas IPR usando Modelos de Vogel/Standing*"
        )

        uploaded_file, curva_seleccionada = self.render_sidebar()

        if uploaded_file is not None:
            try:
                # 1. Procesamiento (Backend)
                procesador = ProcesadorExcel(uploaded_file)
                fila_datos = procesador.cargar_y_calcular()

                if fila_datos is not None:
                    # Renderizar Métricas
                    self.render_metrics(fila_datos)

                    # 2. Cálculos IPR (Backend)
                    tabla, z, ratio = CalculadoraIPR.generar_tabla(
                        fila_datos, curva_seleccionada
                    )

                    # 3. Visualización (Tabs)
                    tab1, tab2 = st.tabs(
                        ["📊 Gráficas y Análisis", "🔢 Resultados Numéricos"]
                    )

                    with tab1:
                        self.render_charts(
                            tabla, fila_datos, z, ratio, curva_seleccionada
                        )

                    with tab2:
                        st.dataframe(
                            tabla[
                                ["Pwf", "Pwf/Pws", "qo/qomax", "Qo (BPD)"]
                            ].style.format("{:.4f}")
                        )

                        # Opción de descargar CSV
                        csv = tabla.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "Descargar Tabla CSV",
                            csv,
                            "tabla_ipr.csv",
                            "text/csv",
                            key="download-csv",
                        )
                else:
                    st.error(
                        "No se encontraron filas con datos completos (Pws, Pwf, Qo) en el archivo."
                    )

            except Exception as e:
                st.error(f"Ocurrió un error al procesar el archivo: {e}")
                st.exception(e)  # Mostrar stacktrace para debugging si es necesario
        else:
            st.info(
                "👈 Por favor, carga un archivo Excel en la barra lateral para comenzar."
            )


if __name__ == "__main__":
    # Esto permite probar frontend.py directamente si se desea,
    # aunque lo ideal es correr app.py
    app = StreamlitApp()
    app.run()
