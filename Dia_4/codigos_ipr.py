import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# =============================================================================
# 1. BASE DE DATOS DE CURVAS (COPIADO EXACTAMENTE DE TUS SCRIPTS)
# =============================================================================
class DatosCurvas:
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


# =============================================================================
# 2. PROCESADOR ESTILO ORIGINAL (CALCULA COLUMNAS COMPLETAS)
# =============================================================================
class ProcesadorExcel:
    def __init__(self, ruta_archivo):
        self.ruta = ruta_archivo
        self.df = None

    def cargar_y_calcular(self):
        """
        Replica exactamente los pasos de 'CURVAS IPR-1.py':
        Carga -> Limpia Columnas -> Crea Columnas Calculadas para TODO el archivo.
        """
        print("--> Leyendo archivo Excel...")
        # Intentamos leer Hoja1 que es la que usa tu script original
        try:
            self.df = pd.read_excel(self.ruta, sheet_name="Hoja1", engine="openpyxl")
        except:
            # Fallback a la primera hoja si 'Hoja1' no existe
            self.df = pd.read_excel(self.ruta, engine="openpyxl")

        # 1. Normalizar nombres de columnas (strip)
        self.df.columns = [str(col).strip() for col in self.df.columns]

        print(f"--> Columnas encontradas: {list(self.df.columns[:10])}...")

        # 2. CÁLCULOS MASIVOS (Vectorizados, como en tu script original)
        # Esto calcula para todas las filas, tengan datos o no (pandas maneja los NaNs)

        # A. Intervalo Medio
        self.df["Intervalo medio"] = (self.df["a1"] + self.df["a2"]) / 2

        # B. Pws kg/cm2 @2010 (Fórmula exacta de tu script)
        # (((y2 - y1) * (x3 - x2)) / (x2 - x1)) + y2
        try:
            self.df["pws_2010"] = (
                ((self.df["y2"] - self.df["y1"]) * (self.df["x3"] - self.df["x2"]))
                / (self.df["x2"] - self.df["x1"])
            ) + self.df["y2"]
        except KeyError:
            print("Error: Faltan columnas x1,x2,x3,y1,y2 para cálculo de Pws.")
            self.df["pws_2010"] = np.nan

        # C. Gradiente * Años y Pws Final
        try:
            self.df["Gradiente_Anos"] = self.df["Gradiente (kg/cm^2)"] * self.df["años"]
            self.df["Pws_Final"] = self.df["pws_2010"] + self.df["Gradiente_Anos"]
        except KeyError:
            self.df["Pws_Final"] = np.nan

        # D. Pwf (Interpolación lineal usando X1, Y1, X2, Y2 mayúsculas)
        # Asumimos interpolación lineal estándar para la profundidad del intervalo medio
        try:
            # Pendiente m = (Y2 - Y1) / (X2 - X1)
            # Y = Y1 + m * (x - X1)
            m = (self.df["Y2"] - self.df["Y1"]) / (self.df["X2"] - self.df["X1"])
            self.df["Pwf_Final"] = self.df["Y1"] + m * (
                self.df["Intervalo medio"] - self.df["X1"]
            )
        except KeyError:
            # Si faltan columnas, intentamos inferir o dejar NaN
            self.df["Pwf_Final"] = np.nan

        # 3. FILTRADO: Devolver solo la fila que tenga Pws, Pwf y Qo válidos
        df_validos = self.df.dropna(subset=["Pws_Final", "Pwf_Final", "Qo (BPD)"])

        if not df_validos.empty:
            # Retornamos la primera fila válida encontrada (similar a buscar en el Excel)
            # Usualmente es la última fila de datos agregada
            fila_seleccionada = df_validos.iloc[-1]
            print(
                f"--> Fila válida encontrada con Fecha: {fila_seleccionada.get('Fecha', 'Desconocida')}"
            )
            return fila_seleccionada
        else:
            print(
                "--> ERROR: Se realizaron los cálculos, pero ninguna fila tiene todos los datos (Pws, Pwf, Qo) completos."
            )
            return None


# =============================================================================
# 3. GENERADOR DE TABLA IPR (Lógica de tus scripts)
# =============================================================================
class CalculadoraIPR:
    @staticmethod
    def generar_tabla(datos_fila, nombre_curva="Curva 0.85"):
        """
        Genera la tabla final con los pasos de presión fijos y la interpolación.
        """
        pws = datos_fila["Pws_Final"]
        pwf = datos_fila["Pwf_Final"]
        qo_test = datos_fila["Qo (BPD)"]

        # 1. Calcular Z actual (Punto de aforo)
        pwf_pws_ratio = pwf / pws

        # Obtener curva y ordenar (X creciente para np.interp)
        curva = DatosCurvas.CURVAS[nombre_curva]
        curva_ord = sorted(curva, key=lambda p: p[0])
        x_ref = np.array([p[0] for p in curva_ord])  # Pwf/Pws
        y_ref = np.array([p[1] for p in curva_ord])  # Qo/Qmax

        # Z interpolado
        z_calc = np.interp(pwf_pws_ratio, x_ref, y_ref)

        # Qo / Z (Máximo teórico basado en el test)
        qo_z = qo_test / z_calc if z_calc != 0 else 0

        # 2. Construir Tabla con pasos fijos
        pasos_presion = [137.5, 120.0, 100.0, 80.0, 60.0, 40.0, 0.0]
        tabla = pd.DataFrame({"Pwf": pasos_presion})

        tabla["Pwf/Pws"] = tabla["Pwf"] / pws

        # Interpolación sobre la curva seleccionada
        tabla["qo/qomax"] = np.interp(tabla["Pwf/Pws"], x_ref, y_ref)

        # 3. Lógica de "Intersección Forzada" (De tu script 0.85.py)
        # Fijar el último valor (Pwf=0) al máximo de la curva para cerrar bien
        valor_interseccion = y_ref[-1]  # El valor Y cuando X (Pwf/Pws) es ~0
        tabla.at[tabla.index[-1], "qo/qomax"] = valor_interseccion

        # Calcular Qo Final
        tabla["Qo (BPD)"] = tabla["qo/qomax"] * qo_z

        # Forzar el cálculo exacto en el último punto (opcional, como en tu script)
        # tabla.at[tabla.index[-1], 'Qo (BPD)'] = valor_interseccion * qo_z

        return tabla, z_calc, pwf_pws_ratio


# =============================================================================
# 4. GRAFICADOR (MATPLOTLIB)
# =============================================================================
def graficar(tabla, datos, z_val, ratio_val, curva_nombre):
    # Gráfica 1: Curvas Adimensionales
    plt.figure(figsize=(10, 6))

    # Pintar todas las curvas de fondo
    for nombre, puntos in DatosCurvas.CURVAS.items():
        pts = sorted(puntos, key=lambda x: x[0])
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        estilo = "-" if nombre == curva_nombre else "--"
        grosor = 2 if nombre == curva_nombre else 1
        alpha = 1 if nombre == curva_nombre else 0.5
        plt.plot(x, y, linestyle=estilo, linewidth=grosor, alpha=alpha, label=nombre)

    # Punto operativo
    plt.scatter([ratio_val], [z_val], color="red", s=100, zorder=5, label="Punto Test")

    plt.gca().invert_xaxis()  # Pwf/Pws va de 1 a 0
    plt.title(f"Curvas IPR Adimensionales - {datos['Fecha']}")
    plt.xlabel("Pwf / Pws")
    plt.ylabel("Qo / Qmax")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

    # Gráfica 2: IPR Real (Resultados Tabla)
    plt.figure(figsize=(10, 6))
    plt.plot(
        tabla["Qo (BPD)"], tabla["Pwf"], "b-o", linewidth=2, label=f"IPR {curva_nombre}"
    )

    # Punto de aforo original
    plt.scatter(
        [datos["Qo (BPD)"]],
        [datos["Pwf_Final"]],
        color="green",
        s=100,
        label="Dato Aforo",
        zorder=5,
    )

    plt.title(f"Curva IPR Real Calculada - {datos['Fecha']}")
    plt.xlabel("Caudal Qo (BPD)")
    plt.ylabel("Presión Pwf (kg/cm²)")
    plt.grid(True)
    plt.legend()
    plt.show()


# =============================================================================
# MAIN
# =============================================================================
def main():
    archivo = "RPM.xlsx"
    curva_objetivo = "Curva 0.85"

    # 1. Cargar y procesar estilo "script original"
    procesador = ProcesadorExcel(archivo)
    fila_datos = procesador.cargar_y_calcular()

    if fila_datos is not None:
        print("\n=== DATOS DEL POZO ===")
        print(f"Fecha: {fila_datos.get('Fecha')}")
        print(f"Intervalo Medio: {fila_datos['Intervalo medio']:.2f} m")
        print(f"Pws Calculada:   {fila_datos['Pws_Final']:.2f} kg/cm²")
        print(f"Pwf Calculada:   {fila_datos['Pwf_Final']:.2f} kg/cm²")
        print(f"Qo Test:         {fila_datos['Qo (BPD)']:.2f} BPD")

        # 2. Generar Tabla IPR
        tabla, z, ratio = CalculadoraIPR.generar_tabla(fila_datos, curva_objetivo)

        print("\n=== TABLA GENERAL GENERADA ===")
        # Formato bonito para consola
        pd.options.display.float_format = "{:.4f}".format
        print(tabla[["Pwf", "Pwf/Pws", "qo/qomax", "Qo (BPD)"]].to_string(index=False))

        # 3. Graficar
        print("\nGenerando gráficas...")
        graficar(tabla, fila_datos, z, ratio, curva_objetivo)

    else:
        print("No se pudo generar la IPR por falta de datos válidos.")


if __name__ == "__main__":
    main()
