import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ReportLab Imports for PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Bearing Capacity Suite", page_icon="🏗️", layout="wide")
st.title("🏗️ Bearing Capacity & Settlement Suite")
st.caption("Supports Terzaghi, Hansen, Meyerhof, Vesić, IS 6403, SPT N-Value, and IBC Presumptive Load Standards")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    st.header("1. Select Calculation Method")
    method = st.selectbox(
        "Design Method / Standard",
        [
            "Terzaghi Method", 
            "Hansen Method", 
            "Meyerhof Method", 
            "Vesić Method",
            "SPT N-Value Method (Bowles)",
            "IS 6403: 1981 (Indian Standard)", 
            "IBC Presumptive Values"
        ]
    )

    if method == "SPT N-Value Method (Bowles)":
        st.header("2. Field Testing Inputs")
        N60 = st.number_input("Corrected SPT Blow Count (N60)", 1, 100, 15)
        B = st.number_input("Width, B (m)", 0.1, 20.0, 1.5)
        Df = st.number_input("Depth, Df (m)", 0.0, 10.0, 1.0)
        settlement_limit_mm = st.number_input("Allowable Settlement Limit (mm)", 10.0, 100.0, 25.0)
        FS = st.number_input("Factor of Safety (FS)", 1.0, 10.0, 3.0)
        ex, ey = 0.0, 0.0
        Dw = 2.0
        
    elif method != "IBC Presumptive Values":
        st.header("2. Soil Parameters")
        c = st.number_input("Cohesion, c (kPa)", 0.0, 500.0, 15.0)
        phi = st.number_input("Friction Angle, φ (deg)", 0.0, 45.0, 28.0)
        gamma_dry = st.number_input("Dry/Moist γ (kN/m³)", 0.0, 30.0, 18.0)
        gamma_sat = st.number_input("Saturated γ_sat (kN/m³)", 0.0, 30.0, 20.0)
        Es = st.number_input("Soil Elastic Modulus, Es (MPa)", 1.0, 500.0, 25.0)
        
        st.header("3. Footing Geometry & Shape")
        footing_shape = st.selectbox("Footing Shape", ["Strip / Continuous", "Square", "Rectangle", "Circular"])
        B = st.number_input("Width / Diameter, B (m)", 0.1, 20.0, 1.5)
        L = st.number_input(
    "Length, L (m)", 
    min_value=0.1, 
    max_value=100.0, 
    value=1.5 if footing_shape != "Strip / Continuous" else 100.0
)
        Df = st.number_input("Depth, Df (m)", 0.0, 10.0, 1.0)
        ex = st.number_input("Eccentricity e_x (m)", 0.0, B/2, 0.0)
        ey = st.number_input("Eccentricity e_y (m)", 0.0, L/2, 0.0)
        
        st.header("4. Water Table & Seismic Inputs")
        Dw = st.number_input("Water Table Depth, Dw (m)", 0.0, 20.0, 0.5)
        kh = st.number_input("Horizontal Seismic Coeff (k_h)", 0.0, 0.5, 0.0)
        kv = st.number_input("Vertical Seismic Coeff (k_v)", 0.0, 0.5, 0.0)
        FS = st.number_input("Factor of Safety (FS)", 1.0, 10.0, 3.0)

    else:
        st.header("2. IBC Table 1806.2 Material Selection")
        soil_type = st.selectbox("Material Class", [
            "1. Crystalline Bedrock (12,000 psf / ~575 kPa)",
            "2. Sedimentary & Foliated Rock (4,000 psf / ~190 kPa)",
            "3. Sandy Gravel and/or Gravel (3,000 psf / ~140 kPa)",
            "4. Sand, Silty Sand, Clayey Sand (2,000 psf / ~95 kPa)",
            "5. Clay, Sandy Clay, Silty Clay (1,500 psf / ~70 kPa)"
        ])
        B = st.number_input("Width, B (m)", 0.1, 20.0, 1.5)
        Df = st.number_input("Depth, Df (m)", 0.0, 10.0, 1.0)
        Dw = 2.0
        ex, ey = 0.0, 0.0

# --- Calculations ---
if method not in ["IBC Presumptive Values", "SPT N-Value Method (Bowles)"]:
    B_eff = max(0.01, B - (2 * ex))
    L_eff = max(0.01, L - (2 * ey))

    # Water Table Adjustment
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

    # Seismic Coefficients
    gamma_eff = gamma_eff * (1 - kv)
    q = q * (1 - kv)

    rad_phi = np.radians(phi)
    
    # Terzaghi Specific Bearing Capacity Factors
    if method == "Terzaghi Method":
        if phi > 0:
            a = np.exp((0.75 * np.pi - rad_phi / 2) * np.tan(rad_phi))
            Nq = (a**2) / (2 * (np.cos(np.radians(45 + phi / 2)))**2)
            Nc = (Nq - 1) / np.tan(rad_phi)
            Ng = (np.tan(rad_phi) / 2) * ((Kp_terzaghi := (np.tan(np.radians(45 + phi/2)))**2) / (np.cos(rad_phi))**2 - 1)
        else:
            Nc, Nq, Ng = 5.7, 1.0, 0.0

        # Terzaghi Shape Factors
        if footing_shape == "Square":
            sc, sg = 1.3, 0.8
        elif footing_shape == "Circular":
            sc, sg = 1.3, 0.6
        else:  # Strip or Rectangular approximation
            sc, sg = 1.0, 1.0
            
        q_ult = (c * Nc * sc) + (q * Nq) + (0.5 * gamma_eff * B_eff * Ng * sg)
        q_allow = q_ult / FS

    # General Nq, Nc for Hansen, Meyerhof, Vesic
    else:
        if phi > 0:
            Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi/2)))**2
            Nc = (Nq - 1) / np.tan(rad_phi)
        else:
            Nq, Nc = 1.0, 5.14

        if method == "Hansen Method":
            Ng = 1.5 * (Nq - 1) * np.tan(rad_phi) if phi > 0 else 0.0
            sc = 1 + (Nq / Nc) * (B_eff / L_eff) if phi > 0 else 1 + 0.2 * (B_eff / L_eff)
            sq = 1 + (B_eff / L_eff) * np.tan(rad_phi)
            sg = 1 - 0.4 * (B_eff / L_eff)
            q_ult = (c * Nc * sc) + (q * Nq * sq) + (0.5 * gamma_eff * B_eff * Ng * sg)
            q_allow = q_ult / FS

        elif method == "Meyerhof Method":
            Ng = (Nq - 1) * np.tan(1.4 * rad_phi) if phi > 0 else 0.0
            Kp = (np.tan(np.radians(45 + phi/2)))**2
            sc = 1 + 0.2 * Kp * (B_eff / L_eff)
            sq = 1 + 0.1 * Kp * (B_eff / L_eff) if phi > 10 else 1.0
            sg = sq
            q_ult = (c * Nc * sc) + (q * Nq * sq) + (0.5 * gamma_eff * B_eff * Ng * sg)
            q_allow = q_ult / FS

        elif method == "Vesić Method":
            Ng = 2 * (Nq + 1) * np.tan(rad_phi) if phi > 0 else 0.0
            sc = 1 + (Nq / Nc) * (B_eff / L_eff)
            sq = 1 + (B_eff / L_eff) * np.tan(rad_phi)
            sg = 1 - 0.4 * (B_eff / L_eff)
            q_ult = (c * Nc * sc) + (q * Nq * sq) + (0.5 * gamma_eff * B_eff * Ng * sg)
            q_allow = q_ult / FS

        elif method == "IS 6403: 1981 (Indian Standard)":
            Ng = 2 * (Nq + 1) * np.tan(rad_phi) if phi > 0 else 0.0
            sc = 1 + 0.2 * (B_eff / L_eff)
            sq = 1 + 0.2 * (B_eff / L_eff)
            sg = 1 - 0.4 * (B_eff / L_eff)
            dc = 1 + 0.2 * (Df / B_eff) * np.sqrt(max(1.0, (1 + np.sin(rad_phi))/(1 - np.sin(rad_phi))))
            dq = dg = 1 + 0.1 * (Df / B_eff) * np.tan(rad_phi) if phi > 10 else 1.0
            
            q_net_ult = (c * Nc * sc * dc) + (q * (Nq - 1) * sq * dq) + (0.5 * gamma_eff * B_eff * Ng * sg * dg)
            q_ult = q_net_ult + q
            q_allow = (q_net_ult / FS) + q

    # Elastic Settlement Calculation
    mu = 0.35
    I_s = 0.88
    elastic_settlement_mm = (q_allow * B_eff * (1 - mu**2) * I_s / (Es * 1000)) * 1000

elif method == "SPT N-Value Method (Bowles)":
    B_eff = B
    # Bowles (1996) Empirical Equations for 25mm settlement
    Fd = 1 + 0.33 * (Df / B)
    Fd = min(Fd, 1.33)
    
    if B <= 1.2:
        q_net_25 = (N60 / 0.05) * Fd  # kPa for 25mm settlement
    else:
        q_net_25 = (N60 / 0.08) * ((B + 0.3) / B)**2 * Fd
        
    # Scale for user-defined allowable settlement
    q_allow = q_net_25 * (settlement_limit_mm / 25.0)
    q_ult = q_allow * FS
    elastic_settlement_mm = settlement_limit_mm

else:  # IBC Table 1806.2
    ibc_values = {
        "1. Crystalline Bedrock (12,000 psf / ~575 kPa)": 575.0,
        "2. Sedimentary & Foliated Rock (4,000 psf / ~190 kPa)": 190.0,
        "3. Sandy Gravel and/or Gravel (3,000 psf / ~140 kPa)": 140.0,
        "4. Sand, Silty Sand, Clayey Sand (2,000 psf / ~95 kPa)": 95.0,
        "5. Clay, Sandy Clay, Silty Clay (1,500 psf / ~70 kPa)": 70.0
    }
    B_eff = B
    q_allow = ibc_values[soil_type]
    q_ult = q_allow * 3.0
    elastic_settlement_mm = 0.0

# --- Results UI ---
with col_res:
    st.header("📊 Analysis Output")
    
    m1, m2 = st.columns(2)
    m1.metric("Effective Width (B')", f"{B_eff:.2f} m")
    m2.metric("Allowable Capacity (q_allow)", f"{q_allow:.2f} kPa")
    
    m3, m4 = st.columns(2)
    m3.metric("Est. Elastic Settlement", f"{elastic_settlement_mm:.2f} mm" if method != "IBC Presumptive Values" else "N/A")
    m4.metric("Ultimate Capacity (q_ult)", f"{q_ult:.2f} kPa")

    # Foundation Profile Diagram
    st.subheader("🖼️ Foundation Cross-Section")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.axhline(0, color='brown', lw=2, label="Ground Surface")
    ax.add_patch(plt.Rectangle((-B/2, -Df), B, Df, facecolor='gray', alpha=0.6, edgecolor='black', label="Footing"))
    ax.axhline(-Dw, color='blue', linestyle='--', lw=1.5, label=f"Water Table (Dw={Dw}m)")
    ax.set_xlim(-B*1.5, B*1.5)
    ax.set_ylim(-max(Df+B, Dw+1), 1)
    ax.set_ylabel("Depth (m)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc="lower left")
    st.pyplot(fig)

# --- PDF Generator ---
def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1E3A8A"))
    
    story.append(Paragraph("<b>Geotechnical Calculation Summary</b>", title_style))
    story.append(Spacer(1, 10))
    
    data = [
        ["Parameter", "Value", "Unit"],
        ["Calculation Method", method, "-"],
        ["Effective Width (B')", f"{B_eff:.2f}", "m"],
        ["Ultimate Bearing Capacity (q_ult)", f"{q_ult:.2f}", "kPa"],
        ["Allowable Bearing Capacity (q_allow)", f"{q_allow:.2f}", "kPa"],
        ["Estimated Elastic Settlement", f"{elastic_settlement_mm:.2f}", "mm"]
    ]
    
    t = Table(data, colWidths=[200, 120, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
    ]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

st.markdown("---")
st.download_button(
    label="📥 Download Summary Report (PDF)",
    data=generate_pdf(),
    file_name="bearing_capacity_summary.pdf",
    mime="application/pdf"
)
