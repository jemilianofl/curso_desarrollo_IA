import pandas as pd
import numpy as np


# =============================================================================
# AGENTE 2: EL FÍSICO (Lógica y Datos)
# =============================================================================
class DatosCurvas:
    """
    Base de datos de curvas adimensionales IPR.
    Contiene los pares (Pwf/Pws, Qo/Qmax) para diferentes modelos de Vogel/Standing.
    """

    CURVAS = {
        "curva 0.5": [
            (0.6739349, 5.20e-04),
            (0.6041, 0.18117839),
            (0.49477935, 0.37965602),
            (0.35427386, 0.60046196),
            (0.22216843, 0.75701785),
            (6.43e-04, 0.99402404),
        ],
        "curva 0.6": [
            (0.7580445, 0.002266205),
            (0.6101795, 0.28583047),
            (0.51651496, 0.4290484),
            (0.40416315, 0.5692209),
            (0.24604554, 0.76157355),
            (0.00168109, 0.99402714),
        ],
        "Curva 0.75": [
            (0.88162, 0),
            (0.720243, 0.292139),
            (0.547549, 0.511354),
            (0.434189, 0.630596),
            (0.266775, 0.7618188),
            (0.004796, 0.994037),
        ],
        "Curva 0.85": [
            (0.9376863, 0.00579279),
            (0.8730867, 0.15657145),
            (0.7534185, 0.32960704),
            (0.55995375, 0.55025464),
            (0.3280805, 0.7618188),
            (0.007913752, 0.992551),
        ],
        "Curva 1": [
            (0.9968761, 0.00596974),
            (0.880196, 0.2672057),
            (0.7407785, 0.45363516),
            (0.5733799, 0.60111696),
            (0.41328245, 0.72619903),
            (0.00479419, 0.9955312),
        ],
    }


class CalculadoraIPR:
    """
    Realiza los cálculos matemáticos de interpolación y generación de tablas IPR.
    """

    @staticmethod
    def generar_tabla(datos_fila, nombre_curva="Curva 0.85"):
        """
        Genera la tabla final con los pasos de presión fijos y la interpolación.
        Retorna la tabla (DataFrame), el valor Z calculado y el ratio actual.
        """
        pws = datos_fila["Pws_Final"]
        pwf = datos_fila["Pwf_Final"]
        qo_test = datos_fila["Qo (BPD)"]

        # 1. Calcular Z actual (Punto de aforo de referencia)
        pwf_pws_ratio = pwf / pws

        # Obtener curva y ordenar (X creciente para np.interp)
        # La clave en el dict puede no coincidir exactamente si el usuario selecciona desde UI,
        # pero asumimos que el frontend envía una clave válida.
        curva = DatosCurvas.CURVAS.get(nombre_curva)
        if not curva:
            raise ValueError(f"Curva '{nombre_curva}' no encontrada.")

        curva_ord = sorted(curva, key=lambda p: p[0])
        x_ref = np.array([p[0] for p in curva_ord])  # Eje X: Pwf/Pws
        y_ref = np.array([p[1] for p in curva_ord])  # Eje Y: Qo/Qmax

        # Z interpolado (Qo/Qmax actual para las condiciones del test)
        z_calc = np.interp(pwf_pws_ratio, x_ref, y_ref)

        # Qmax teórico del pozo basado en el test
        # Qmax = Qo_test / (Qo/Qmax)_interpolado
        qo_z = qo_test / z_calc if z_calc != 0 else 0

        # 2. Construir Tabla con pasos fijos de presión
        pasos_presion = [137.5, 120.0, 100.0, 80.0, 60.0, 40.0, 0.0]
        tabla = pd.DataFrame({"Pwf": pasos_presion})

        # Relación Pwf/Pws para cada paso
        tabla["Pwf/Pws"] = tabla["Pwf"] / pws

        # Interpolación sobre la curva seleccionada para obtener Qo/Qmax en cada paso
        tabla["qo/qomax"] = np.interp(tabla["Pwf/Pws"], x_ref, y_ref)

        # 3. Lógica de "Intersección Forzada"
        # Cuando Pwf=0 (último paso), forzamos que Qo/Qmax sea exactamente el máximo de la curva digitalizada.
        # Esto sirve para cerrar la curva visualmente incluso si la interpolación lineal varía un poco.
        valor_interseccion = y_ref[
            -1
        ]  # Valor Y cuando X (Pwf/Pws) es ~0 (final de la curva ordenada)

        # Asumiendo que 0.0 es el último elemento en pasos_presion
        tabla.at[tabla.index[-1], "qo/qomax"] = valor_interseccion

        # Calcular Qo Final (BPD)
        tabla["Qo (BPD)"] = tabla["qo/qomax"] * qo_z

        return tabla, z_calc, pwf_pws_ratio


# =============================================================================
# AGENTE 1: EL INGESTOR (Procesamiento de Datos)
# =============================================================================
class ProcesadorExcel:
    """
    Encargado de leer, limpiar y transformar los datos brutos del Excel.
    """

    def __init__(self, archivo):
        """
        :param archivo: Ruta al archivo o objeto UploadedFile de Streamlit.
        """
        self.archivo = archivo
        self.df = None

    def cargar_y_calcular(self):
        """
        Lee el Excel, ejecuta cálculos vectorizados y retorna la última fila válida.
        """
        # Intentar leer Hoja1, fallback a la primera hoja
        try:
            self.df = pd.read_excel(self.archivo, sheet_name="Hoja1", engine="openpyxl")
        except:
            try:
                self.df = pd.read_excel(self.archivo, engine="openpyxl")
            except Exception as e:
                raise ValueError(f"Error al leer el archivo Excel: {e}")

        # 1. Limpieza: Normalizar nombres de columnas (strip)
        self.df.columns = [str(col).strip() for col in self.df.columns]

        # Validación de columnas requeridas básicas
        cols_necesarias = [
            "a1",
            "a2",
            "x1",
            "x2",
            "x3",
            "y1",
            "y2",
            "Gradiente (kg/cm^2)",
            "años",
            "X1",
            "X2",
            "Y1",
            "Y2",
            "Qo (BPD)",
        ]
        faltantes = [c for c in cols_necesarias if c not in self.df.columns]
        # Nota: Podríamos ser más flexibles, pero el requerimiento pide cálculos específicos.
        # Si faltan columas de cálculo intermedio, fallará el bloque try/except de abajo.

        # 2. CÁLCULOS MASIVOS (Vectorizados)
        try:
            # A. Intervalo Medio
            self.df["Intervalo medio"] = (self.df["a1"] + self.df["a2"]) / 2

            # B. Pws kg/cm2 @2010 (Fórmula de tres puntos)
            # (((y2 - y1) * (x3 - x2)) / (x2 - x1)) + y2
            self.df["pws_2010"] = (
                ((self.df["y2"] - self.df["y1"]) * (self.df["x3"] - self.df["x2"]))
                / (self.df["x2"] - self.df["x1"])
            ) + self.df["y2"]

            # C. Gradiente * Años y Pws Final
            self.df["Gradiente_Anos"] = self.df["Gradiente (kg/cm^2)"] * self.df["años"]
            self.df["Pws_Final"] = self.df["pws_2010"] + self.df["Gradiente_Anos"]

            # D. Pwf (Interpolación lineal usando X1, Y1, X2, Y2 para profundidad)
            # Pendiente m = (Y2 - Y1) / (X2 - X1)
            # Y = Y1 + m * (x - X1)
            m = (self.df["Y2"] - self.df["Y1"]) / (self.df["X2"] - self.df["X1"])
            self.df["Pwf_Final"] = self.df["Y1"] + m * (
                self.df["Intervalo medio"] - self.df["X1"]
            )

        except KeyError as e:
            # Capturamos error si alguna columna específica falta durante el cálculo
            raise ValueError(f"Falta una columna necesaria para los cálculos: {e}")

        # 3. FILTRADO AUTOMÁTICO
        # Eliminar filas donde Pws, Pwf o Qo sean NaN
        df_validos = self.df.dropna(subset=["Pws_Final", "Pwf_Final", "Qo (BPD)"])

        if df_validos.empty:
            return None

        # Seleccionar la última fila válida (comportamiento solicitado)
        fila_seleccionada = df_validos.iloc[-1]

        return fila_seleccionada
