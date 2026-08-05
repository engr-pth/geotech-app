import streamlit as st
import numpy as np

st.set_page_config(page_title="Bearing Capacity Suite", page_icon="🏗️")
st.title("🏗️ Advanced Bearing Capacity Calculator")
st.caption("Includes Water Table, Inclined Loads, and Seismic Effects")

# --- Sidebar Inputs ---
st.sidebar.header("1. Soil Parameters")
c = st.sidebar.number_input("Cohesion, c (kPa)", min_value=0.0, value=20.0)
phi = st.sidebar.number_input("Friction Angle, φ (deg)", min_value=0.0, max_value=45.0, value=25.0)
gamma_dry = st.sidebar.number_input("Moist/Dry Unit Weight, γ_dry (kN/m³)", min_value=0.0, value=18.0)
gamma_sat = st.sidebar.number_input("Saturated Unit Weight, γ_sat (kN/m³)", min_value=0.0, value=20.0)
gamma_w = 9.81

st.sidebar.header("2. Footing Geometry")
B = st.sidebar.number_input("Width, B (m)", min_value=0.1, value=1.5)
L = st.sidebar.number_input("Length, L (m)", min_value=0.1, value=1.5)
Df = st.sidebar.number_input("Depth, Df (m)", min_value=0.0, value=1.0)
FS = st.sidebar.number_input("Factor of Safety (FS)", min_value=1.0, value=3.0)
Dw = st.sidebar.number_input("Water Table Depth, Dw (m)", min_value=0.0, value=2.0)

st.sidebar.header("3. Inclined Load (V & H Forces)")
V = st.sidebar.number_input("Vertical Load, V (kN)", min_value=1.0, value=100.0)
H = st.sidebar.number_input("Horizontal Load, H (kN)", min_value=0.0, value=15.0)

st.sidebar.header("4. Seismic Coefficients (Pseudo-static)")
kh = st.sidebar.number_input("Horizontal Coefficient (k_h)", min_value=0.0, max_value=0.5, value=0.1)
kv = st.sidebar.number_input("Vertical Coefficient (k_v)", min_value=0.0, max_value=0.5, value=0.0)

method = st.sidebar.selectbox("5. Select Method", ["Meyerhof", "Hansen"])

# --- Calculations ---
# Water Table Corrections
if Dw <= Df:
    q = (Dw * gamma_dry) + ((Df - Dw) * (gamma_sat - gamma_w))
    gamma_eff = gamma_sat - gamma_w
elif Df < Dw <= (Df + B):
    q = Df * gamma_dry
    gamma_eff = (gamma_sat - gamma_w) + ((Dw - Df) / B) * (gamma_dry - (gamma_sat - gamma_w))
else:
    q = Df * gamma_dry
    gamma_eff = gamma_dry

# Seismic Modification on Soil Unit Weight & Effective Load
gamma_eff = gamma_eff * (1 - kv)
q = q * (1 - kv)

# Inclination Angle (Alpha) combined with Seismic Horizontal Force
# Total Horizontal Effect = H + (V * k_h)
H_total = H + (V * kh)
alpha_rad = np.arctan(H_total / V) if V > 0 else 0
alpha_deg = np.degrees(alpha_rad)

# Bearing Capacity Factors
rad_phi = np.radians(phi)
if phi > 0:
    Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi/2)))**2
    Nc = (Nq - 1) / np.tan(rad_phi)
else:
    Nq = 1.0
    Nc = 5.14

# Shape & Inclination Factors
if method == "Meyerhof":
    Ng = (Nq - 1) * np.tan(1.4 * rad_phi) if phi > 0 else 0.0
    Kp = (np.tan(np.radians(45 + phi/2)))**2
    sc = 1 + 0.2 * Kp * (B / L)
    sq = 1 + 0.1 * Kp * (B / L) if phi > 10 else 1.0
    sg = sq
    
    # Meyerhof Inclination Factors
    ic = (1 - (alpha_deg / 90))**2
    iq = (1 - (alpha_deg / 90))**2
    ig = (1 - (alpha_deg / phi))**2 if phi > 0 else 1.0

elif method == "Hansen":
    Ng = 1.5 * (Nq - 1) * np.tan(rad_phi) if phi > 0 else 0.0
    sc = 1 + (Nq / Nc) * (B / L) if phi > 0 else 1 + 0.2 * (B / L)
    sq = 1 + (B / L) * np.tan(rad_phi)
    sg = 1 - 0.4 * (B / L)
    
    # Hansen Inclination Factors
    iq = (1 - (0.5 * H_total) / (V + B * L * c * (1/np.tan(rad_phi))))**5 if phi > 0 else 1.0
    ic = iq - ((1 - iq) / (Nq - 1)) if phi > 0 else 1 - (0.5 * H_total / (B * L * c))
    ig = (1 - (0.7 * H_total) / (V + B * L * c * (1/np.tan(rad_phi))))**5 if phi > 0 else 1.0

# Ultimate and Allowable Calculation
q_ult = (c * Nc * sc * ic) + (q * Nq * sq * iq) + (0.5 * gamma_eff * B * Ng * sg * ig)
q_allow = q_ult / FS

# --- Results UI ---
st.subheader("📊 Calculation Results")

col1, col2, col3 = st.columns(3)
col1.metric("Load Angle (α)", f"{alpha_deg:.2f}°")
col2.metric("Total Horiz. Force (H_tot)", f"{H_total:.1f} kN")
col3.metric("Allowable Capacity (q_allow)", f"{q_allow:.2f} kPa")

st.markdown("---")
st.write("**Correction Factors Used:**")
st.json({
    "Shape Factors (sc, sq, sg)": [round(sc, 3), round(sq, 3), round(sg, 3)],
    "Inclination Factors (ic, iq, ig)": [round(ic, 3), round(iq, 3), round(ig, 3)],
    "Seismic Adjustments": f"kh = {kh}, kv = {kv}"
})
