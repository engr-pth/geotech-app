import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Ultimate Geotech Suite", page_icon="🏗️", layout="wide")
st.title("🏗️ Enterprise Bearing Capacity & Settlement Suite")

# --- Layout Columns ---
col_in, col_res = st.columns([1, 1.2])

with col_in:
    st.header("1. Soil Parameters")
    c = st.number_input("Cohesion, c (kPa)", 0.0, 500.0, 15.0)
    phi = st.number_input("Friction Angle, φ (deg)", 0.0, 45.0, 28.0)
    gamma_dry = st.number_input("Dry/Moist γ (kN/m³)", 0.0, 30.0, 17.5)
    gamma_sat = st.number_input("Saturated γ_sat (kN/m³)", 0.0, 30.0, 19.5)
    Es = st.number_input("Soil Elastic Modulus, Es (MPa)", 1.0, 500.0, 25.0) # For settlement
    
    st.header("2. Footing Geometry & Eccentricity")
    B = st.number_input("Width, B (m)", 0.1, 20.0, 2.0)
    L = st.number_input("Length, L (m)", 0.1, 20.0, 2.0)
    Df = st.number_input("Depth, Df (m)", 0.0, 10.0, 1.5)
    ex = st.number_input("Eccentricity e_x (m)", 0.0, B/2, 0.1)
    ey = st.number_input("Eccentricity e_y (m)", 0.0, L/2, 0.0)
    
    st.header("3. Water Table & Seismic Inputs")
    Dw = st.number_input("Water Table Depth, Dw (m)", 0.0, 20.0, 1.0)
    kh = st.number_input("Horizontal Seismic Coeff, k_h", 0.0, 0.5, 0.05)
    FS = st.number_input("Factor of Safety", 1.0, 10.0, 3.0)

# --- Effective Dimensions Calculation ---
B_eff = B - (2 * ex)
L_eff = L - (2 * ey)

# --- Water Table Calculations ---
gamma_w = 9.81
if Dw <= Df:
    q = (Dw * gamma_dry) + ((Df - Dw) * (gamma_sat - gamma_w))
    gamma_eff = gamma_sat - gamma_w
elif Df < Dw <= (Df + B_eff):
    q = Df * gamma_dry
    gamma_eff = (gamma_sat - gamma_w) + ((Dw - Df) / B_eff) * (gamma_dry - (gamma_sat - gamma_w))
else:
    q = Df * gamma_dry
    gamma_eff = gamma_dry

# --- Hansen Bearing Capacity Theory ---
rad_phi = np.radians(phi)
if phi > 0:
    Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi/2)))**2
    Nc = (Nq - 1) / np.tan(rad_phi)
    Ng = 1.5 * (Nq - 1) * np.tan(rad_phi)
else:
    Nq, Nc, Ng = 1.0, 5.14, 0.0

# Shape Factors using B_eff and L_eff
sc = 1 + (Nq / Nc) * (B_eff / L_eff) if phi > 0 else 1 + 0.2 * (B_eff / L_eff)
sq = 1 + (B_eff / L_eff) * np.tan(rad_phi)
sg = 1 - 0.4 * (B_eff / L_eff)

q_ult = (c * Nc * sc) + (q * Nq * sq) + (0.5 * gamma_eff * B_eff * Ng * sg)
q_allow = q_ult / FS

# --- Elastic Settlement Calculation (Schmertmann / Elastic) ---
mu = 0.35 # Poisson's ratio
I_s = 0.88 # Shape Influence factor for square/rect
elastic_settlement_mm = (q_allow * B_eff * (1 - mu**2) * I_s / (Es * 1000)) * 1000 # in mm

# --- Results & Visualization ---
with col_res:
    st.header("📊 Analysis Output")
    
    m1, m2 = st.columns(2)
    m1.metric("Effective Dimensions (B' × L')", f"{B_eff:.2f} m × {L_eff:.2f} m")
    m2.metric("Allowable Bearing Capacity", f"{q_allow:.2f} kPa")
    
    m3, m4 = st.columns(2)
    m3.metric("Est. Elastic Settlement", f"{elastic_settlement_mm:.2f} mm")
    m4.metric("Ultimate Capacity (q_ult)", f"{q_ult:.2f} kPa")

    # --- 2D Footing Cross-Section Diagram Drawing ---
    st.subheader("🖼️ Cross-Section Profile")
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Ground & Footing
    ax.axhline(0, color='brown', lw=2, label="Ground Surface")
    ax.add_patch(plt.Rectangle((-B/2, -Df), B, Df, facecolor='gray', alpha=0.6, edgecolor='black', label="Footing"))
    
    # Water Table Line
    ax.axhline(-Dw, color='blue', linestyle='--', lw=1.5, label=f"Water Table (Dw={Dw}m)")
    
    # Set limits & labels
    ax.set_xlim(-B*1.5, B*1.5)
    ax.set_ylim(-max(Df+B, Dw+1), 1)
    ax.set_ylabel("Depth (m)")
    ax.set_xlabel("Width (m)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc="lower left")
    
    st.pyplot(fig)
