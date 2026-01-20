import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# datos de inicio
# altura de la mesa rotaria
rkb = 30.2
# tirante de agua
TA = 3014
z = TA + rkb
# paso 1 extraccion de datos
# en esta seccion del codigo vamos a extraer los datos del registros
df_depth = pd.read_excel(r"D", sheet_name="Hoja1", usecols="A")
depth = df_depth.iloc[:, 0].tolist()
# df_dtc = pd.read_excel(r"C:\Users\HP\Desktop\curso phyton\Pozo_M1D.xlsx", sheet_name="Hoja1", usecols="B")
dtc = df_dtc.iloc[:, 0].tolist()
# df_MW = pd.read_excel(r"C:\Users\HP\Desktop\curso phyton\Pozo_M1D.xlsx", sheet_name="Hoja1", usecols="C")
MW = df_MW.iloc[:, 0].tolist()
# paso 2 cacular la velocidad de la onda p en m/s
lista_vp = []
for i in dtc:
    vp = 304878.05 / i
    lista_vp.append(vp)
# paso 3 calcular la densidad con el modelo de gardner
lista_pgar = []
for i in lista_vp:
    pgar = 0.31 * i**0.25
    lista_pgar.append(pgar)
# paso 4 calcular la densidad de trougott
# definimos constantes para el modelo de trougoot
po = 1.95
k = 0.01
c = 0.5
lista_ptrougott = []
for i in depth:
    ptrougott = po + (k * (i - z) ** c)
    lista_ptrougott.append(ptrougott)


# paso 5 grficar modelo de gardner y trougott
# curva gardner
plt.plot(lista_pgar, depth, label="densidad de gardner")
# curva trougott
plt.plot(lista_ptrougott, depth, label="densidad de trougott")
plt.title("densidades")
plt.xlabel("densidad en g/cm^3")
plt.ylabel("profundidad en metros")
plt.legend()
plt.gca().invert_yaxis()
plt.show()


# paso 6 calcular la sobrecarga con el metodo DVC en pso
lista_sv = []
for i in depth:
    SV = 0.145 * (po * 9.81 * i + k * 9.81 * i ** (c + 1) / (c + 1))
    lista_sv.append(SV)
# paso 7 calcular el gradiente de sobrecarga expresado en densidad
lista_gsv = []
for x, y in zip(depth, lista_sv):
    gsv = y / (x * 1.422)
    lista_gsv.append(gsv)
# paso 8 calcular la dtc promedio
lista_dtcprom = []
for i in range(len(depth)):
    end = min(i + 101, len(depth))
    dtc_prom = np.mean(dtc[i:end])
    lista_dtcprom.append(dtc_prom)
# paso 9 calcular dtn con modelo de athy
# constantes para el modelo de athy
c1 = -0.0004
dtco = 180
lista_dtn = []
for i in depth:
    dtn = dtco * (np.exp(c1 * (i - z)))
    lista_dtn.append(dtn)


# paso 10
# curva dtcprom
plt.plot(lista_dtcprom, depth, label="dtc promedio")
# curva dtn
plt.plot(lista_dtn, depth, label="dtn")
plt.title("dt")
plt.xlabel("tiempo de transito")
plt.ylabel("profundidad en metros")
plt.legend()
plt.gca().invert_yaxis()
plt.xscale("log")
plt.show()

# paso 11 obtener la divicion de dtc pro /dtn
lista_divdt = [lista_dtcprom[0] / lista_dtn[0]]
for i in range(len(depth)):
    if lista_dtcprom[i] / lista_dtn[i] > lista_divdt[i - 1]:
        lista_divdt.append(lista_dtcprom[i] / lista_dtn[i])
    else:
        lista_divdt.append(lista_divdt[i - 1])

# paso 12 calcular la divergencia
# definimos prf
prf = 3329
lista_div = []
for i in range(len(depth)):
    if depth[i] > prf:
        div = lista_divdt[i]
    else:
        div = 1
    lista_div.append(div)

# paso 13 calcular la dtsh
lista_dtsh = []
for i in range(len(depth)):
    dtsh = lista_div[i] * lista_dtn[i]
    lista_dtsh.append(dtsh)
# paso 14 graficar
plt.plot(lista_dtsh, depth, label="dtsh")
# curva dtn
plt.plot(lista_dtn, depth, label="dtn")
plt.title("area divergente")
plt.xlabel("tiempo de transito")
plt.ylabel("profundidad en metros")
plt.legend()
plt.gca().invert_yaxis()
plt.xscale("log")
plt.fill_betweenx(
    depth, lista_dtn, lista_dtsh, color="pink", alpha=0.5, label="area entre curvas"
)
plt.show()

# paso 15 calcular la pp sin calibrar
# constantes de ethon
exp_eathon = 0.5
ppn = 1.03
lista_ppdiv = []
for i in range(len(depth)):
    Pp_div = (
        lista_gsv[i]
        - (lista_gsv[i] - ppn) * (lista_dtn[i] / lista_dtsh[i]) ** exp_eathon
    )
    lista_ppdiv.append(Pp_div)
# Paso 16 Presion de poro divergencia calibrada
# Definimos el tiempo geológico de zona anormal
ms = 1784
lista_ppdivcal = []
for i in range(len(depth)):
    if depth[i] < ms:
        ppdivcal = (
            lista_gsv[i]
            - (lista_gsv[i] - ppn) * (lista_dtn[i] / lista_dtsh[i]) ** exp_eathon
        )
    else:
        ppdivcal = MW[i] - 0.03
    lista_ppdivcal.append(ppdivcal)
# paso 17 presion de fractura
# calculamos parametro v
lista_v = []
for i in depth:
    v = 0.0645 * np.log(i) - 0.067
    lista_v.append(v)
lista_pf = []
for i in range(len(depth)):
    pf = lista_ppdiv[i] + (lista_v[i] / (1 - lista_v[i])) * (
        lista_gsv[i] - lista_ppdiv[i]
    )
    lista_pf.append(pf)
# Paso 18 graficar ventana operativa geopresiones
# sobrecarga
plt.plot(lista_gsv, depth, label="Sobrecarga")
# pp
plt.plot(lista_ppdiv, depth, label="Pp sin calibrar")
# pp calibrada
plt.plot(lista_ppdivcal, depth, label="PP calibrada")
# pf
plt.plot(lista_pf, depth, label="Pf")
# mw
plt.plot(MW, depth, label="mw")
plt.title("Ventana operativa ")
plt.xlabel("Gradiente de presión en gr/cm3")
plt.ylabel("Profundidad en metros")
plt.legend()
plt.gca().invert_yaxis()
plt.show()
