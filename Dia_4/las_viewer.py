import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from las_loader import LASHandler

# Page Configuration
st.set_page_config(layout="wide", page_title="LAS Log Viewer", page_icon="📈")

# Initialize Handler
if "las_handler" not in st.session_state:
    st.session_state.las_handler = LASHandler()

las_handler = st.session_state.las_handler


def main():
    st.title("🛢️ Modern LAS Log Viewer")

    try:
        # --- Sidebar: File & Curve Selection ---
        with st.sidebar:
            st.header("Configuration")

            # File Selection
            uploaded_file = st.file_uploader("Upload LAS File")

            if uploaded_file:
                # Load file if not already loaded or if a new file is uploaded
                if las_handler.filepath != uploaded_file.name:
                    success, msg = las_handler.load_file(uploaded_file)
                    if success:
                        st.success(f"Loaded: {uploaded_file.name}")
                    else:
                        st.error(msg)
                        return

                # Curve Selection
                curves = las_handler.get_curve_names()
                if "DEPTH" in curves:
                    curves.remove("DEPTH")

                # Default selection suggestion
                default_curves = [
                    c for c in ["GR", "NPHI", "RHOB", "DT"] if c in curves
                ]
                if not default_curves:
                    default_curves = curves[:3]  # Fallback to first 3

                selected_curves = st.multiselect(
                    "Select Curves to Plot", curves, default=default_curves
                )
            else:
                st.info("Please upload a LAS file to begin.")
                return

        # --- Main Content ---
        if las_handler.las and selected_curves:
            # Well Info Expander
            with st.expander("ℹ️ Well Information", expanded=False):
                well_info = las_handler.get_well_info()
                # Display well info in a grid
                cols = st.columns(4)
                for i, (key, value) in enumerate(well_info.items()):
                    cols[i % 4].metric(label=key, value=str(value))

            # Data Preparation
            df = las_handler.get_log_data()

            # Plotting with Plotly
            st.subheader("Log Visualization")

            num_tracks = len(selected_curves)
            if num_tracks > 0:
                fig = make_subplots(
                    rows=1,
                    cols=num_tracks,
                    shared_yaxes=True,
                    horizontal_spacing=0.02,
                    subplot_titles=selected_curves,
                )

                for i, curve in enumerate(selected_curves):
                    fig.add_trace(
                        go.Scatter(
                            x=df[curve], y=df["DEPTH"], mode="lines", name=curve
                        ),
                        row=1,
                        col=i + 1,
                    )
                    # Add individual x-axes if needed, or customize per track
                    fig.update_xaxes(title_text=curve, row=1, col=i + 1)

                # Common Y-axis configuration (Depth)
                # FIX: use autorange="reversed" instead of reversed=True
                fig.update_yaxes(
                    title_text="Depth (m)", autorange="reversed", row=1, col=1
                )  # Only first col needs label
                fig.update_yaxes(autorange="reversed")  # All y-axes reversed

                # Layout customization for "Modern" look
                fig.update_layout(
                    height=1000,
                    showlegend=False,
                    template="plotly_dark",  # Dark theme
                    margin=dict(l=50, r=50, t=50, b=50),
                    hovermode="y unified",  # Hover shows all values at that depth
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("Please select at least one curve to plot.")

        elif not selected_curves:
            st.info("Select curves from the sidebar to visualize data.")

    except Exception as e:
        st.error("An unexpected error occurred.")
        with st.expander("See error details"):
            st.exception(e)


if __name__ == "__main__":
    main()
