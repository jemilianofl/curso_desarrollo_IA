# Sistema de Modelado IPR (Arquitectura Streamlit)

1. Visión del Proyecto
Crear una aplicación web reproducible, mantenible y modular utilizando Streamlit. La aplicación debe calcular, tabular y graficar curvas IPR (Inflow Performance Relationship) basándose en modelos de Vogel/Standing, respetando estrictamente la lógica de interpolación lineal y cálculo vectorizado definida en los scripts originales (CURVAS IPR.py).

Todo el codigo esta almacenado en la carpeta Dia_4 y ahi tenemos que almacenar el nuevo codigo.

2. Stack Tecnológico
- Frontend: Streamlit (UI/UX), Plotly (Gráficos interactivos).

- Backend: Python 3.9+, Pandas (Procesamiento vectorizado), Numpy (Interpolación).

- Datos: Excel (openpyxl).

3. Arquitectura de Agentes (Backend & Frontend)
El sistema se divide en tres "Agentes" (Clases) que separan la lógica de la interfaz.

🤖 Agente 1: El Ingestor (Backend - Data)
Responsabilidad: Leer el Excel, limpiar nombres de columnas y realizar los cálculos masivos (vectorizados) antes de cualquier filtrado. Clase Sugerida: ProcesadorExcel

Reglas de Negocio Estrictas:

Carga: Intentar leer Hoja1 primero. Si falla, leer la primera hoja disponible.

Limpieza: Aplicar .strip() a todos los nombres de columnas para evitar errores de espacios ('x1 ' -> 'x1').

Cálculo Vectorizado (Pre-Filtro):

Calcular Intervalo medio = (a1 + a2) / 2 para toda la columna.

Calcular Pws @ 2010 usando la fórmula de tres puntos: (((y2 - y1) * (x3 - x2)) / (x2 - x1)) + y2.

Calcular Pws Final = Pws @ 2010 + (Gradiente * años).

Calcular Pwf Final interpolando entre (X1, Y1) y (X2, Y2) usando el Intervalo medio.

Selección de Datos:

No buscar fila por fila con un loop.

Filtrar el DataFrame eliminando filas donde Pws, Pwf o Qo sean NaN.

Seleccionar automáticamente la última fila válida encontrada.

🧠 Agente 2: El Físico (Backend - Logic)
Responsabilidad: Contener las curvas digitalizadas y realizar la matemática de interpolación np.interp. Clases Sugeridas: BaseDatosCurvas y CalculadoraIPR

Reglas de Negocio Estrictas:

Base de Datos: Debe contener el diccionario CURVAS hardcodeado (0.5, 0.6, 0.75, 0.85, 1.0) con sus pares (Pwf/Pws, Qo/Qmax).

Cálculo de Z:

Calcular Ratio = Pwf_real / Pws_real.

Ordenar los arrays de la curva base para que X sea creciente (requisito de np.interp).

Interpolar Z (Qo/Qmax actual).

Calcular Qmax_teorico = Qo_test / Z.

Generación de Tabla:

Usar pasos fijos de presión: [137.5, 120.0, 100.0, 80.0, 60.0, 40.0, 0.0].

Calcular qo/qomax para cada paso interpolando en la curva base.

Forzado de Intersección: El valor de qo/qomax cuando Pwf=0 debe forzarse al valor máximo Y de la curva digitalizada (para cerrar la curva perfectamente).

🎨 Agente 3: El Diseñador (Frontend - Streamlit)
Responsabilidad: Renderizar la interfaz, manejar el estado y mostrar gráficas. Clase Sugerida: StreamlitApp

Requerimientos de UI:

Sidebar: Carga de archivo y SelectBox para elegir la curva (0.5, 0.85, 1.0, etc.).

Métricas: Mostrar en columnas grandes: Fecha, Intervalo Medio, Pws, Pwf y Qo Test.

Tabs: Separar "Resultados Numéricos" (Tabla formateada) de "Gráficas".

Gráficos (Plotly):

Gráfico 1 (Adimensional): Mostrar todas las curvas en gris tenue y la curva seleccionada en color fuerte. Marcar el punto operativo (Test) en rojo. Importante: Invertir el eje X (1 a 0).

Gráfico 2 (IPR Real): Pwf vs Qo.

4. Requerimientos de Código y Estilo
Modularidad: Cada agente debe vivir en su propio archivo (ej. backend.py, frontend.py).

Nomenclatura: Seguir el estilo de los scripts originales (nombres en español, mayúsculas para constantes).

Eficiencia: Prohibido usar loops for para cálculos matemáticos. Todo debe ser vectorizado con Pandas/Numpy.

Manejo de Errores: El frontend debe mostrar mensajes amigables si el Excel está vacío o si faltan columnas críticas.

5. Entregables
Archivo app.py: El punto de entrada principal que orquesta la carga de datos y la ejecución de los agentes.

Archivo backend.py: Contiene las clases ProcesadorExcel y CalculadoraIPR.

Archivo frontend.py: Contiene la lógica de Streamlit y visualización.

Archivo requirements.txt: Lista de dependencias (streamlit, pandas, numpy, openpyxl, plotly).

Instrucciones de Ejecución: Un pequeño README con el comando: streamlit run app.py.

6. Criterios de Validación (Checklist)
Al finalizar, el código debe cumplir:

✅ Carga de Datos: ¿Se lee el Excel y se limpian las columnas automáticamente?

✅ Cálculos Vectorizados: ¿Se calculan Pws, Pwf y Gradiente para todas las filas sin usar loops for?

✅ Selección Automática: ¿El sistema encuentra la última fila válida sin intervención manual?

✅ Interpolación: ¿Se usa np.interp correctamente y se fuerza el cierre de la curva en Pwf=0?

✅ UI/UX: ¿La interfaz es limpia, las gráficas son interactivas y los datos se muestran en tablas formateadas?

✅ Modularidad: ¿El código está dividido en clases lógicas y archivos separados?
