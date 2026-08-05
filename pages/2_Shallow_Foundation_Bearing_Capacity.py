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

col_in, col_res = st.columns([1, 1.2])

with col_in:
    # --- 1. Unit System Selection ---
    st.header("1. Select Unit System & Standard")
    unit_system = st.radio("Unit System", ["SI Units (m, kN, kPa)", "FPS / Imperial (ft, kips, ksf)"])
    
    # Define Labels & Units dynamically
    is_si = (unit_system == "SI Units (m, kN, kPa)")
    u_len = "m" if is_si else "ft"
    u_stress = "kPa" if is_si else "ksf"
    u_gamma = "kN/m³" if is_si else "pcf"
    u_settle = "mm" if is_si else "in"

    method = st.selectbox(
        "Design Method / Standard",
        ["Terzaghi Method", "Hansen Method", "Meyerhof Method", "Vesić Method"]
    )

    st.header("2. Soil Parameters")
    c = st.number_input(f"Cohesion, c ({u_stress})", 0.0, 5000.0, 15.0 if is_si else 0.3)
    phi = st.number_input("Friction Angle, φ (deg)", 0.0, 45.0, 28.0)
    gamma_dry = st.number_input(f"Dry/Moist γ ({u_gamma})", 0.0, 300.0, 18.0 if is_si else 115.0)
    gamma_sat = st.number_input(f"Saturated γ_sat ({u_gamma})", 0.0, 300.0, 20.0 if is_si else 125.0)
    
    st.header("3. Footing Geometry & Shape")
    footing_shape = st.selectbox("Footing Shape", ["Strip / Continuous", "Square", "Rectangle"])
    B = st.number_input(f"Width, B ({u_len})", 0.1, 100.0, 1.5 if is_si else 5.0)
    
    max_L = 500.0 if footing_shape == "Strip / Continuous" else 100.0
    default_L = 500.0 if footing_shape == "Strip / Continuous" else (1.5 if is_si else 5.0)
    L = st.number_input(f"Length, L ({u_len})", min_value=0.1, max_value=max_L, value=default_L)
    
    Df = st.number_input(f"Depth, Df ({u_len})", 0.0, 50.0, 1.0 if is_si else 3.0)
    ex = st.number_input(f"Eccentricity e_x ({u_len})", 0.0, B/2, 0.0)
    ey = st.number_input(f"Eccentricity e_y ({u_len})", 0.0, L/2, 0.0)
    
    st.header("4. Water Table & Factor of Safety")
    Dw = st.number_input(f"Water Table Depth, Dw ({u_len})", 0.0, 100.0, 0.5 if is_si else 2.0)
    FS = st.number_input("Factor of Safety (FS)", 1.0, 10.0, 3.0)

# --- Calculation Engine ---
B_eff = max(0.01, B - (2 * ex))
L_eff = max(0.01, L - (2 * ey))

# Water Table Correction
gamma_w = 9.81 if is_si else 62.4
if Dw <= Df:
    q = (Dw * gamma_dry) + ((Df - Dw) * (gamma_sat - gamma_w))
    gamma_eff = gamma_sat - gamma_w
elif Df < Dw <= (Df + B_eff):
    q = Df * gamma_dry
    gamma_eff = (gamma_sat - gamma_w) + ((Dw - Df) / B_eff) * (gamma_dry - (gamma_sat - gamma_w))
else:
    q = Df * gamma_dry
    gamma_eff = gamma_dry

rad_phi = np.radians(phi)

# Bearing Capacity Factors Logic
if method == "Terzaghi Method":
    if phi > 0:
        a = np.exp((0.75 * np.pi - rad_phi / 2) * np.tan(rad_phi))
        Nq = (a**2) / (2 * (np.cos(np.radians(45 + phi / 2)))**2)
        Nc = (Nq - 1) / np.tan(rad_phi)
        Kp_terzaghi = (np.tan(np.radians(45 + phi/2)))**2
        Ng = (np.tan(rad_phi) / 2) * (Kp_terzaghi / (np.cos(rad_phi))**2 - 1)
    else:
        Nc, Nq, Ng = 5.7, 1.0, 0.0

    if footing_shape == "Square":
        sc, sg = 1.3, 0.8
    else:
        sc, sg = 1.0, 1.0
    sq = 1.0
    q_ult = (c * Nc * sc) + (q * Nq) + (0.5 * gamma_eff * B_eff * Ng * sg)

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
    elif method == "Meyerhof Method":
        Ng = (Nq - 1) * np.tan(1.4 * rad_phi) if phi > 0 else 0.0
        Kp = (np.tan(np.radians(45 + phi/2)))**2
        sc = 1 + 0.2 * Kp * (B_eff / L_eff)
        sq = 1 + 0.1 * Kp * (B_eff / L_eff) if phi > 10 else 1.0
        sg = sq
    elif method == "Vesić Method":
        Ng = 2 * (Nq + 1) * np.tan(rad_phi) if phi > 0 else 0.0
        sc = 1 + (Nq / Nc) * (B_eff / L_eff)
        sq = 1 + (B_eff / L_eff) * np.tan(rad_phi)
        sg = 1 - 0.4 * (B_eff / L_eff)

    q_ult = (c * Nc * sc) + (q * Nq * sq) + (0.5 * gamma_eff * B_eff * Ng * sg)

q_allow = q_ult / FS

# --- Results UI ---
with col_res:
    st.header("📊 Calculation Summary")
    m1, m2 = st.columns(2)
    m1.metric(f"Effective Width (B')", f"{B_eff:.2f} {u_len}")
    m2.metric(f"Effective Overburden (q)", f"{q:.2f} {u_stress}")
    
    m3, m4 = st.columns(2)
    m3.metric(f"Ultimate Bearing Capacity (q_ult)", f"{q_ult:.2f} {u_stress}")
    m4.metric(f"Allowable Capacity (q_allow)", f"{q_allow:.2f} {u_stress}")

# --- PDF Generator WITH STEP-BY-STEP CALCULATION ---
def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1E3A8A"), spaceAfter=12)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2563EB"), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, leading=13)

    # Title
    story.append(Paragraph("<b>Geotechnical Design Report (Step-by-Step Calculation)</b>", title_style))
    story.append(Spacer(1, 5))

    # Section 1: Inputs Summary
    story.append(Paragraph("<b>1. Input Parameters</b>", h2_style))
    input_data = [
        ["Parameter", "Value", "Unit", "Parameter", "Value", "Unit"],
        ["Method Used", method, "-", "Unit System", "SI" if is_si else "FPS", "-"],
        ["Footing Width (B)", f"{B:.2f}", u_len, "Footing Length (L)", f"{L:.2f}", u_len],
        ["Embedment Depth (Df)", f"{Df:.2f}", u_len, "Water Table Depth (Dw)", f"{Dw:.2f}", u_len],
        ["Cohesion (c)", f"{c:.2f}", u_stress, "Friction Angle (φ)", f"{phi:.1f}", "deg"],
        ["Dry Unit Weight (γ)", f"{gamma_dry:.2f}", u_gamma, "Sat. Unit Weight (γ_sat)", f"{gamma_sat:.2f}", u_gamma],
    ]
    t_input = Table(input_data, colWidths=[120, 60, 40, 120, 60, 40])
    t_input.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E5E7EB")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(t_input)

    # Section 2: Step-by-Step Calculation Breakdown
    story.append(Paragraph("<b>2. Step-by-Step Calculation Procedure</b>", h2_style))
    
    steps = [
        f"<b>Step 1: Effective Footing Dimensions</b><br/>"
        f"• B' = B - 2(e_x) = {B:.2f} - 2({ex:.2f}) = <b>{B_eff:.2f} {u_len}</b><br/>"
        f"• L' = L - 2(e_y) = {L:.2f} - 2({ey:.2f}) = <b>{L_eff:.2f} {u_len}</b>",

        f"<b>Step 2: Effective Stress & Water Table Correction</b><br/>"
        f"• Effective Surcharge Load (q) at footing base = <b>{q:.2f} {u_stress}</b><br/>"
        f"• Unit Weight below foundation (γ_eff) = <b>{gamma_eff:.2f} {u_gamma}</b>",

        f"<b>Step 3: Bearing Capacity Factors</b><br/>"
        f"• Nc = <b>{Nc:.3f}</b>, Nq = <b>{Nq:.3f}</b>, Nγ = <b>{Ng:.3f}</b>",

        f"<b>Step 4: Shape Factors</b><br/>"
        f"• Shape factor (s_c) = <b>{sc:.3f}</b><br/>"
        f"• Shape factor (s_q) = <b>{sq:.3f}</b><br/>"
        f"• Shape factor (s_γ) = <b>{sg:.3f}</b>",

        f"<b>Step 5: Ultimate & Allowable Bearing Capacity</b><br/>"
        f"• q_ult = (c × Nc × sc) + (q × Nq × sq) + (0.5 × γ_eff × B' × Nγ × s_γ)<br/>"
        f"• q_ult = ({c:.1f}×{Nc:.2f}×{sc:.2f}) + ({q:.1f}×{Nq:.2f}×{sq:.2f}) + (0.5×{gamma_eff:.1f}×{B_eff:.2f}×{Ng:.2f}×{sg:.2f})<br/>"
        f"• <b>Ultimate Capacity (q_ult) = {q_ult:.2f} {u_stress}</b><br/>"
        f"• Allowable Capacity (q_allow) = q_ult / Factor of Safety ({FS})<br/>"
        f"• <b>Allowable Capacity (q_allow) = {q_allow:.2f} {u_stress}</b>"
    ]

    for step in steps:
        story.append(Paragraph(step, body_style))
        story.append(Spacer(1, 6))

    # Section 3: Summary Table
    story.append(Paragraph("<b>3. Final Output Summary</b>", h2_style))
    summary_data = [
        ["Final Parameter", "Value", "Unit"],
        ["Ultimate Bearing Capacity (q_ult)", f"{q_ult:.2f}", u_stress],
        ["Factor of Safety (FS)", f"{FS:.1f}", "-"],
        ["Allowable Bearing Capacity (q_allow)", f"{q_allow:.2f}", u_stress]
    ]
    t_summary = Table(summary_data, colWidths=[220, 100, 80])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F9FAFB")),
    ]))
    story.append(t_summary)

    doc.build(story)
    buffer.seek(0)
    return buffer

st.markdown("---")
st.download_button(
    label="📥 Download Detailed Report with Step-by-Step Calculations (PDF)",
    data=generate_pdf(),
    file_name=f"bearing_capacity_detailed_{'SI' if is_si else 'FPS'}.pdf",
    mime="application/pdf"
)
