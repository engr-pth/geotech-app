import streamlit as st
import numpy as np

st.set_page_config(page_title="Bearing Capacity Suite", page_icon="🏗️")
st.title("🏗️ Shallow Foundation Bearing Capacity Calculator")

# --- Sidebar Inputs ---
st.sidebar.header("1. Soil Parameters")
c = st.sidebar.number_input("Cohesion, c (kPa)", min_value=0.0, value=20.0)
phi = st.sidebar.number_input("Friction Angle, φ (deg)", min_value=0.0, max_value=45.0, value=25.0)
gamma = st.sidebar.number_input("Unit Weight, γ (kN/m³)", min_value=0.0, value=18.0)

st.sidebar.header("2. Footing Geometry")
B = st.sidebar.number_input("Width, B (m)", min_value=0.1, value=1.5)
L = st.sidebar.number_input("Length, L (m)", min_value=0.1, value=1.5)
Df = st.sidebar.number_input("Depth, Df (m)", min_value=0.0, value=1.0)
FS = st.sidebar.number_input("Factor of Safety (FS)", min_value=1.0, value=3.0)

# Method Selection
method = st.sidebar.selectbox(
    "3. Select Calculation Method",
    ["Terzaghi", "Meyerhof", "Hansen"]
)

# --- Calculation Logic ---
rad_phi = np.radians(phi)

if phi > 0:
    Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi/2)))**2
    Nc = (Nq - 1) / np.tan(rad_phi)
else:
    Nq = 1.0
    Nc = 5.14

# Method Specific Bearing Capacity Factors & Shape Factors
if method == "Terzaghi":
    Ng = 2 * (Nq + 1) * np.tan(rad_phi) if phi > 0 else 0.0
    # Shape factors for square/rectangular approximations
    sc, sq, sg = 1.3, 1.0, 0.8  # Continuous vs Square shape adjustment
    q_ult = (sc * c * Nc) + (sq * gamma * Df * Nq) + (sg * 0.5 * gamma * B * Ng)

elif method == "Meyerhof":
    Ng = (Nq - 1) * np.tan(1.4 * rad_phi) if phi > 0 else 0.0
    # Shape Factors
    Kp = (np.tan(np.radians(45 + phi/2)))**2
    sc = 1 + 0.2 * Kp * (B / L)
    sq = 1 + 0.1 * Kp * (B / L) if phi > 10 else 1.0
    sg = sq
    q_ult = (c * Nc * sc) + (gamma * Df * Nq * sq) + (0.5 * gamma * B * Ng * sg)

elif method == "Hansen":
    Ng = 1.5 * (Nq - 1) * np.tan(rad_phi) if phi > 0 else 0.0
    # Shape Factors
    sc = 1 + (Nq / Nc) * (B / L) if phi > 0 else 1 + 0.2 * (B / L)
    sq = 1 + (B / L) * np.tan(rad_phi)
    sg = 1 - 0.4 * (B / L)
    q_ult = (c * Nc * sc) + (gamma * Df * Nq * sq) + (0.5 * gamma * B * Ng * sg)

q_allow = q_ult / FS

# --- Output Results ---
st.subheader(f"Results using **{method} Method**")

col1, col2, col3 = st.columns(3)
col1.metric("Nc / Nq / Nγ", f"{Nc:.2f} / {Nq:.2f} / {Ng:.2f}")
col2.metric("Ultimate Capacity (q_ult)", f"{q_ult:.2f} kPa")
col3.metric("Allowable Capacity (q_allow)", f"{q_allow:.2f} kPa")

st.info(f"💡 **Note:** Calculated for B = {B}m, L = {L}m, Depth = {Df}m with Factor of Safety = {FS}.")
