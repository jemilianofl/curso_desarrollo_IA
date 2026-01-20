import pandas as pd
import numpy as np


class DivergenceAnalysis:
    def __init__(
        self,
        data_file,
        rkb=30.2,
        ta=3014,
        po=1.95,
        k=0.01,
        c=0.5,
        dtco=180,
        c1=-0.0004,
        prf=3329,
        ppn=1.03,
        exp_eaton=0.5,
        ms=1784,
    ):
        """
        Initializes the DivergenceAnalysis class with data and parameters.
        """
        self.rkb = rkb
        self.ta = ta
        self.z = ta + rkb
        self.po = po
        self.k = k
        self.c = c
        self.dtco = dtco
        self.c1 = c1
        self.prf = prf
        self.ppn = ppn
        self.exp_eaton = exp_eaton
        self.ms = ms

        # Load data
        # Expecting 'Pozo_L2DL.xlsx' structure: Col A=Depth, Col B=DTC, Col C=MW
        # The user request said: Col 1: Depth, Col 2: P-wave velocity (or DTC?), Col 3: MW
        # Looking at original script:
        # df_depth uses col A (iloc[:,0]) -> depth
        # df_dtc uses col B? No, script says usecols="B" but assigns to dtc.
        # Wait, the script reads 'Pozo_L2DL.xlsx' for depth, but commented out lines for 'Pozo_M1D.xlsx' for dtc and MW.
        # But later it loops over 'dtc'.
        # I will assume the uploaded file has all 3 columns in the first sheet.
        self.df = pd.read_excel(data_file)
        # Standardize column access by index to be safe
        self.depth = self.df.iloc[:, 0].values  # Array for faster ops
        self.dtc = self.df.iloc[:, 1].values
        self.mw = self.df.iloc[:, 2].values

        # Determine if Col 2 is Velocity or DTC.
        # Script calculated Vp = 304878.05 / i  (where i is in dtc list).
        # So input is DTC (transit time).

        self.results = pd.DataFrame(
            {"Depth": self.depth, "DTC": self.dtc, "MW": self.mw}
        )

    def run_analysis(self):
        """Executes the full analysis pipeline."""
        self._calculate_vp()
        self._calculate_gardner_density()
        self._calculate_trougott_density()
        self._calculate_overburden()
        self._calculate_trends()
        self._calculate_divergence()
        self._calculate_pore_pressure()
        self._calculate_fracture_pressure()
        return self.results

    def _calculate_vp(self):
        # VP = 304878.05 / DTC
        self.results["Vp"] = 304878.05 / self.results["DTC"]

    def _calculate_gardner_density(self):
        # Gardner = 0.31 * Vp^0.25
        self.results["Rho_Gardner"] = 0.31 * (self.results["Vp"] ** 0.25)

    def _calculate_trougott_density(self):
        # Trougott = po + k * (depth - z)^c
        # Note: if depth < z, this might be invalid (negative base).
        # Script does not handle this check explicitly, just runs loop.
        # Assuming depths provided are valid.
        # self.depth is numpy array.

        # To match script behavior exactly:
        # for i in depth: ptrougott = po + (k * (i - z) ** c)
        # If i < z, (i-z)**c will be nan for fractional c.
        # We'll use numpy handling.

        term = self.results["Depth"] - self.z
        # Avoid warning/error for negative base if c is float
        term = np.where(
            term < 0, 0, term
        )  # Safety, though logic implies z is water depth+rkb
        # If samples start at 0, they are < z.
        # Original script: z = 3044.2. Depth likely starts deep.

        self.results["Rho_Trougott"] = self.po + (self.k * (term**self.c))

    def _calculate_overburden(self):
        # SV formula from script (approx integration?)
        # SV = 0.145 * (po * 9.81 * i + k * 9.81 * i ** (c + 1) / (c + 1))
        # GSV = SV / (i * 1.422)

        depths = self.results["Depth"]

        # Vectorized calculation
        sv = 0.145 * (
            self.po * 9.81 * depths
            + self.k * 9.81 * (depths ** (self.c + 1)) / (self.c + 1)
        )

        self.results["SV"] = sv
        self.results["GSV"] = sv / (depths * 1.422)

    def _calculate_trends(self):
        # DTC Prom: Moving average window of ~100 size forward looking?
        # Script: range(len), end = min(i + 101, len), mean

        dtc = self.results["DTC"].values
        dtc_prom = []
        n = len(dtc)
        for i in range(n):
            end = min(i + 101, n)
            dtc_prom.append(np.mean(dtc[i:end]))
        self.results["DTC_Prom"] = dtc_prom

        # DTN (Athy)
        # dtn = dtco * exp(c1 * (i - z))
        self.results["DTN"] = self.dtco * np.exp(
            self.c1 * (self.results["Depth"] - self.z)
        )

    def _calculate_divergence(self):
        # Logic:
        # lista_divdt = [dtc_prom[0]/dtn[0]]
        # for i... if current_ratio > prev_ratio: append(current) else: append(prev)

        dtc_prom = self.results["DTC_Prom"].values
        dtn = self.results["DTN"].values
        depths = self.results["Depth"].values

        ratios = dtc_prom / dtn
        div_dt = [ratios[0]]
        for i in range(1, len(ratios)):
            if ratios[i] > div_dt[-1]:
                div_dt.append(ratios[i])
            else:
                div_dt.append(div_dt[-1])

        self.results["Div_DT_Ratio"] = div_dt

        # Divergence Factor
        # if depth > prf: div = div_dt else: 1
        self.results["Div_Factor"] = np.where(
            self.results["Depth"] > self.prf, self.results["Div_DT_Ratio"], 1.0
        )

        # DTSH
        # dtsh = div * dtn
        self.results["DTSH"] = self.results["Div_Factor"] * self.results["DTN"]

    def _calculate_pore_pressure(self):
        # Pp uncalibrated
        # Pp = GSV - (GSV - ppn) * (DTN / DTSH) ** exp_eaton
        gsv = self.results["GSV"]
        dtn = self.results["DTN"]
        dtsh = self.results["DTSH"]

        pp_div = gsv - (gsv - self.ppn) * ((dtn / dtsh) ** self.exp_eaton)
        self.results["Pp_Uncal"] = pp_div

        # Pp calibrated
        # if depth < ms: Pp_uncal else: MW - 0.03
        self.results["Pp_Cal"] = np.where(
            self.results["Depth"] < self.ms,
            self.results["Pp_Uncal"],
            self.results["MW"] - 0.03,
        )

    def _calculate_fracture_pressure(self):
        # Parameter V
        # v = 0.0645 * ln(depth) - 0.067
        # Pf = Pp + (v / (1-v)) * (GSV - Pp)
        # Note: Script uses Pp_uncal (lista_ppdiv) for Pf calculation!

        depths = self.results["Depth"]
        pp_uncal = self.results["Pp_Uncal"]
        gsv = self.results["GSV"]

        v = 0.0645 * np.log(depths) - 0.067
        self.results["Param_V"] = v

        pf = pp_uncal + (v / (1 - v)) * (gsv - pp_uncal)
        self.results["Pf"] = pf
