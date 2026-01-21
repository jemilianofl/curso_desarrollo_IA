import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from divergence_model import DivergenceAnalysis

st.set_page_config(page_title="Anális de divergencia MARL", layout="wide")

st.title("Análisis de Divergencia - Geopresiones. HECHO POR MARL") 
st.markdown("""
Esta aplicación permite realizar un análisis de geopresiones utilizando el método de divergencia.
Carga tu archivo Excel para comenzar.
""")

# Sidebar configuration
st.sidebar.header("Configuración de Parámetros")

# Input parameters
with st.sidebar.expander("Parámetros Generales", expanded=True):
    rkb = st.number_input("RKB (Mesa Rotaria)", value=30.2, step=0.1)
    ta = st.number_input("Tirante de Agua (TA)", value=3014.0, step=1.0)
    prf = st.number_input("Profundidad de Referencia (PRF)", value=3329.0, step=10.0)
    ms = st.number_input("Profundidad Cambio Calibración (MS)", value=1784.0, step=10.0)

with st.sidebar.expander("Modelo de Densidad (Trougott)", expanded=False):
    po = st.number_input("Po (Densidad sup)", value=1.95, step=0.01)
    k = st.number_input("k (Factor)", value=0.01, step=0.001, format="%.4f")
    c = st.number_input("c (Exponente)", value=0.5, step=0.1)

with st.sidebar.expander("Modelo de Athy (DTN)", expanded=False):
    dtco = st.number_input("DTCO (Tránsito inicial)", value=180.0, step=1.0)
    c1 = st.number_input("c1 (Factor exp)", value=-0.0004, step=0.0001, format="%.5f")

with st.sidebar.expander("Modelo de Eaton", expanded=False):
    ppn = st.number_input("Ppn (Normal)", value=1.03, step=0.01)
    exp_eaton = st.number_input("Exponente Eaton", value=0.5, step=0.1)

# File Uploader
uploaded_file = st.sidebar.file_uploader("Cargar archivo Excel (Pozo)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cache the analysis to avoid re-running on simple UI updates if params haven't changed
        # Note: In Streamlit, caching usually requires hashable args.
        # Since we have a class, we'll instantiate it inside the app flow or use a wrapper function.

        @st.cache_data
        def process_data(
            file, _rkb, _ta, _po, _k, _c, _dtco, _c1, _prf, _ppn, _exp, _ms
        ):
            model = DivergenceAnalysis(
                file,
                rkb=_rkb,
                ta=_ta,
                po=_po,
                k=_k,
                c=_c,
                dtco=_dtco,
                c1=_c1,
                prf=_prf,
                ppn=_ppn,
                exp_eaton=_exp,
                ms=_ms,
            )
            return model.run_analysis()

        # Run analysis
        with st.spinner("Procesando datos y calculando modelos..."):
            df_results = process_data(
                uploaded_file, rkb, ta, po, k, c, dtco, c1, prf, ppn, exp_eaton, ms
            )

        st.success("Cálculos completados exitosamente.")

        # TABS for visualizations
        tab1, tab2, tab3 = st.tabs(
            ["Densidades & Tránsito", "Área Divergente", "Ventana Operativa"]
        )

        # --- PLOT 1: DENSITIES & TRANSIT ---
        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Densidades: Gardner vs Trougott")
                fig_den = go.Figure()
                fig_den.add_trace(
                    go.Scatter(
                        x=df_results["Rho_Gardner"],
                        y=df_results["Depth"],
                        mode="lines",
                        name="Gardner",
                    )
                )
                fig_den.add_trace(
                    go.Scatter(
                        x=df_results["Rho_Trougott"],
                        y=df_results["Depth"],
                        mode="lines",
                        name="Trougott",
                    )
                )
                fig_den.update_layout(
                    xaxis_title="Densidad (g/cm³)",
                    yaxis_title="Profundidad (m)",
                    yaxis_autorange="reversed",
                    height=600,
                    template="plotly_white",
                )
                st.plotly_chart(fig_den, use_container_width=True)

            with col2:
                st.subheader("Tiempo de Tránsito: DTC vs DTN")
                fig_dt = go.Figure()
                fig_dt.add_trace(
                    go.Scatter(
                        x=df_results["DTC_Prom"],
                        y=df_results["Depth"],
                        mode="lines",
                        name="DTC Prom",
                    )
                )
                fig_dt.add_trace(
                    go.Scatter(
                        x=df_results["DTN"],
                        y=df_results["Depth"],
                        mode="lines",
                        name="DTN (Athy)",
                    )
                )
                fig_dt.update_layout(
                    xaxis_title="Tiempo de Tránsito (µs/ft)",
                    yaxis_title="Profundidad (m)",
                    yaxis_autorange="reversed",
                    xaxis_type="log",
                    height=600,
                    template="plotly_white",
                )
                st.plotly_chart(fig_dt, use_container_width=True)

        # --- PLOT 2: DIVERGENCE AREA ---
        with tab2:
            st.subheader("Área Divergente")
            fig_div = go.Figure()

            # Fill area
            fig_div.add_trace(
                go.Scatter(
                    x=df_results["DTN"],
                    y=df_results["Depth"],
                    mode="lines",
                    line=dict(width=0),
                    name="DTN",
                    showlegend=False,
                )
            )
            fig_div.add_trace(
                go.Scatter(
                    x=df_results["DTSH"],
                    y=df_results["Depth"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonextx",
                    fillcolor="rgba(255, 192, 203, 0.5)",  # Pink with alpha
                    name="Área Divergente",
                )
            )

            # Lines on top
            fig_div.add_trace(
                go.Scatter(
                    x=df_results["DTN"], y=df_results["Depth"], mode="lines", name="DTN"
                )
            )
            fig_div.add_trace(
                go.Scatter(
                    x=df_results["DTSH"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="DTSH",
                )
            )

            fig_div.update_layout(
                xaxis_title="Tiempo de Tránsito",
                yaxis_title="Profundidad (m)",
                yaxis_autorange="reversed",
                xaxis_type="log",
                height=700,
                template="plotly_white",
            )
            st.plotly_chart(fig_div, use_container_width=True)

        # --- PLOT 3: OPERATIONAL WINDOW ---
        with tab3:
            st.subheader("Ventana Operativa de Geopresiones")
            fig_win = go.Figure()

            fig_win.add_trace(
                go.Scatter(
                    x=df_results["GSV"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="Sobrecarga (GSV)",
                    line=dict(color="black"),
                )
            )
            fig_win.add_trace(
                go.Scatter(
                    x=df_results["Pp_Uncal"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="Pp Sin Calibrar",
                    line=dict(dash="dash", color="blue"),
                )
            )
            fig_win.add_trace(
                go.Scatter(
                    x=df_results["Pp_Cal"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="Pp Calibrada",
                    line=dict(color="blue"),
                )
            )
            fig_win.add_trace(
                go.Scatter(
                    x=df_results["Pf"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="Presión Fractura (Pf)",
                    line=dict(color="green"),
                )
            )
            fig_win.add_trace(
                go.Scatter(
                    x=df_results["MW"],
                    y=df_results["Depth"],
                    mode="lines",
                    name="Mud Weight (MW)",
                    line=dict(color="brown"),
                )
            )

            fig_win.update_layout(
                xaxis_title="Gradiente de Presión (g/cm³)",
                yaxis_title="Profundidad (m)",
                yaxis_autorange="reversed",
                height=800,
                template="plotly_white",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig_win, use_container_width=True)

        # Data Preview
        with st.expander("Ver Tabla de Resultados"):
            st.dataframe(df_results)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info(
        "Por favor, sube un archivo Excel con la estructura requerida (Profundidad, DTC, MW) para ver el análisis."
    )
