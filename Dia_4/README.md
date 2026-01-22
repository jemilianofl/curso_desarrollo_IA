# Sistema de Modelado IPR (Agentes)

Esta aplicación implementa el cálculo de curvas IPR utilizando una arquitectura modular de agentes.

## Estructura del Proyecto

- `app.py`: Punto de entrada de la aplicación.
- `backend.py`: Contiene la lógica de negocio y procesamiento de datos (Agentes "Ingestor" y "Físico").
- `frontend.py`: Contiene la interfaz de usuario con Streamlit (Agente "Diseñador").
- `requirements.txt`: Dependencias del proyecto.

## Instalación

1.  Asegúrate de tener Python instalado.
2.  Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

Para iniciar la aplicación, ejecuta el siguiente comando en la terminal:

```bash
streamlit run app.py
```

## Uso

1.  Sube un archivo Excel con los datos del pozo (formato compatible con `RPM.xlsx`).
2.  Selecciona la curva IPR deseada en la barra lateral.
3.  Visualiza los resultados numéricos y las gráficas interactivas.
