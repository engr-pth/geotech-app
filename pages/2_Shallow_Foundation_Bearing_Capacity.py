import io
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(
    page_title="Comprehensive Footing Design Suite",
    page_icon="🏗️",
    layout="wide",
)
st.title("🏗️ Geotechnical & Structural Footing Design Suite")

# --- UI Layout ---
col_in, col_res = st.columns([1.1, 1.1])

with col_in:
  st.header("1. General & Unit System")
  unit_system = st.radio(
      "Unit System",
      ["SI Units (m, kN, kPa, mm)", "FPS System (ft, kips, ksf, in)"],
  )
  is_imperial = "FPS" in unit_system

  geo_input_mode = st.radio(
      "Geotechnical Input Method",
      ["c-phi Parameters (Analytical)", "SPT N-value (IBC Method)"],
  )

  st.header("2. Soil & Geotechnical Inputs")
  if geo_input_mode == "c-phi Parameters (Analytical)":
    method = st.selectbox(
        "Bearing Capacity Theory",
        ["Terzaghi Method", "Hansen Method", "Meyerhof Method", "Vesić Method"],
    )
    c_val = st.number_input(
        f"Cohesion c ({'kPa' if not is_imperial else 'ksf'})",
        0.0,
        5000.0,
        15.0 if not is_imperial else 0.3,
    )
    phi_val = st.number_input("Friction Angle φ (deg)", 0.0, 45.0, 28.0)
    N_spt = None
  else:
    method = "IBC Presumptive Method"
    N_spt = st.number_input(
        "Standard Penetration Resistance (SPT N-Value)", 1, 100, 15
    )
    c_val, phi_val = 0.0, 0.0

  gamma_dry = st.number_input(
      f"Dry Unit Weight γ ({'kN/m³' if not is_imperial else 'pcf'})",
      0.0,
      500.0,
      18.0 if not is_imperial else 115.0,
  )
  gamma_sat = st.number_input(
      f"Sat. Unit Weight γ_sat ({'kN/m³' if not is_imperial else 'pcf'})",
      0.0,
      500.0,
      20.0 if not is_imperial else 125.0,
  )

  st.header("3. Footing Geometry & Loading")
  B = st.number_input(
      f"Width B ({'m' if not is_imperial else 'ft'})",
      0.5,
      50.0,
      1.8 if not is_imperial else 6.0,
  )
  L = st.number_input(
      f"Length L ({'m' if not is_imperial else 'ft'})",
      0.5,
      50.0,
      1.8 if not is_imperial else 6.0,
  )
  Df = st.number_input(
      f"Embedment Depth Df ({'m' if not is_imperial else 'ft'})",
      0.0,
      20.0,
      1.0 if not is_imperial else 3.5,
  )
  Dw = st.number_input(
      f"Water Table Depth Dw ({'m' if not is_imperial else 'ft'})",
      0.0,
      50.0,
      1.0 if not is_imperial else 3.5,
  )
  FS = st.number_input("Geotechnical Safety Factor (FS)", 1.0, 10.0, 3.0)

  st.header("4. Structural & Rebar Details")
  aci_version = st.selectbox(
      "ACI 318 Standard Code",
      [
          "ACI 318-22",
          "ACI 318-19",
          "ACI 318-14",
          "ACI 318-11",
          "ACI 318-08",
          "ACI 318-05",
      ],
  )
  fc = st.number_input(
      f"Concrete Strength f'c ({'MPa' if not is_imperial else 'psi'})",
      10.0,
      10000.0,
      28.0 if not is_imperial else 4000.0,
  )
  fy = st.number_input(
      f"Rebar Yield Strength fy ({'MPa' if not is_imperial else 'psi'})",
      100.0,
      100000.0,
      420.0 if not is_imperial else 60000.0,
  )

  c1, c2 = st.columns(2)
  cx = c1.number_input(
      f"Column cx ({'m' if not is_imperial else 'ft'})",
      0.1,
      5.0,
      0.4 if not is_imperial else 1.25,
  )
  cy = c2.number_input(
      f"Column cy ({'m' if not is_imperial else 'ft'})",
      0.1,
      5.0,
      0.4 if not is_imperial else 1.25,
  )
  h_foot = st.number_input(
      f"Thickness h ({'m' if not is_imperial else 'ft'})",
      0.1,
      5.0,
      0.45 if not is_imperial else 1.5,
  )

  # Rebar Selection Options
  if not is_imperial:
    rebar_options = {
        "12mm": (12, 113.1),
        "16mm": (16, 201.1),
        "20mm": (20, 314.2),
        "25mm": (25, 490.9),
    }
  else:
    rebar_options = {
        "#4 (0.5in)": (0.5, 0.20),
        "#5 (0.625in)": (0.625, 0.31),
        "#6 (0.75in)": (0.75, 0.44),
        "#7 (0.875in)": (0.875, 0.60),
        "#8 (1.0in)": (1.0, 0.79),
    }
  selected_rebar = st.selectbox("Select Reinforcement Bar Size", list(rebar_options.keys()))

  st.markdown("---")
  # CALCULATE BUTTON
  calc_trigger = st.button("🚀 Calculate Design", type="primary", use_container_width=True)

# --- Perform Calculations Only When Button Is Pressed ---
if calc_trigger or "calculated" in st.session_state:
  st.session_state["calculated"] = True

  # 1. Geotechnical Engine
  gamma_w = 9.81 if not is_imperial else 62.4
  if Dw <= Df:
    q_surcharge = (Dw * gamma_dry) + ((Df - Dw) * (gamma_sat - gamma_w))
    gamma_eff = gamma_sat - gamma_w
  else:
    q_surcharge = Df * gamma_dry
    gamma_eff = gamma_dry

  if geo_input_mode == "SPT N-value (IBC Method)":
    # IBC Table 1806.2 Empirical Approximation
    q_allow = N_spt * 12.5 if not is_imperial else N_spt * 0.25  # kPa or ksf
    q_ult = q_allow * FS
    Nc = Nq = Ng = 0.0
  else:
    rad_phi = np.radians(phi_val)
    if method == "Terzaghi Method":
      if phi_val > 0:
        a = np.exp((0.75 * np.pi - rad_phi / 2) * np.tan(rad_phi))
        Nq = (a**2) / (2 * (np.cos(np.radians(45 + phi_val / 2))) ** 2)
        Nc = (Nq - 1) / np.tan(rad_phi)
        Kp = (np.tan(np.radians(45 + phi_val / 2))) ** 2
        Ng = (np.tan(rad_phi) / 2) * (Kp / (np.cos(rad_phi)) ** 2 - 1)
      else:
        Nc, Nq, Ng = 5.7, 1.0, 0.0
      q_ult = (
          (1.3 * c_val * Nc)
          + (q_surcharge * Nq)
          + (0.4 * gamma_eff * B * Ng)
      )
    else:
      Nq = (
          np.exp(np.pi * np.tan(rad_phi))
          * (np.tan(np.radians(45 + phi_val / 2))) ** 2
          if phi_val > 0
          else 1.0
      )
      Nc = (Nq - 1) / np.tan(rad_phi) if phi_val > 0 else 5.14
      Ng = 2 * (Nq + 1) * np.tan(rad_phi) if phi_val > 0 else 0.0
      q_ult = (c_val * Nc) + (q_surcharge * Nq) + (0.5 * gamma_eff * B * Ng)
    q_allow = q_ult / FS

  # 2. Structural Engine (ACI 318)
  cover = 0.075 if not is_imperial else (3.0 / 12.0)
  d_eff = h_foot - cover

  qu_factored = 1.5 * q_allow
  Pu = qu_factored * B * L

  # Size Effect Factor λs (ACI 318-19/22)
  if aci_version in ["ACI 318-19", "ACI 318-22"]:
    d_metric = d_eff * 1000 if not is_imperial else d_eff * 12 * 25.4
    lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_metric)))
  else:
    lambda_s = 1.0

  # Punching Shear Check
  bo = 2 * ((cx + d_eff) + (cy + d_eff))
  Area_bo = (cx + d_eff) * (cy + d_eff)
  Vu_punch = qu_factored * (B * L - Area_bo)

  phi_s = 0.75
  if not is_imperial:
    vc_punch = 0.33 * lambda_s * np.sqrt(fc)  # MPa
    Phi_Vc_punch = (phi_s * vc_punch * (bo * 1000) * (d_eff * 1000)) / 1000.0
  else:
    vc_punch = 4.0 * lambda_s * np.sqrt(fc)  # psi
    Phi_Vc_punch = (phi_s * vc_punch * (bo * 12) * (d_eff * 12)) / 1000.0

  # One-Way Beam Shear
  crit_dist = (B / 2) - (cx / 2) - d_eff
  Vu_oneway = qu_factored * L * max(0.0, crit_dist)
  if not is_imperial:
    vc_oneway = 0.17 * lambda_s * np.sqrt(fc)
    Phi_Vc_oneway = (phi_s * vc_oneway * (L * 1000) * (d_eff * 1000)) / 1000.0
  else:
    vc_oneway = 2.0 * lambda_s * np.sqrt(fc)
    Phi_Vc_oneway = (phi_s * vc_oneway * (L * 12) * (d_eff * 12)) / 1000.0

  # Bending Moment & Steel Calculation
  cantilever = (B - cx) / 2
  Mu = (qu_factored * L * (cantilever**2)) / 2

  if not is_imperial:
    L_mm, d_mm = L * 1000, d_eff * 1000
    Rn = (Mu * 1e6) / (0.9 * L_mm * (d_mm**2))
    rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
    rho_req = max(rho, 0.0018)
    As_req = rho_req * L_mm * d_mm  # mm²
    bar_dia, bar_area = rebar_options[selected_rebar]
    num_bars = int(np.ceil(As_req / bar_area))
    spacing = int(((L_mm - 150) / max(1, (num_bars - 1))))
  else:
    L_in, d_in = L * 12, d_eff * 12
    Rn = (Mu * 12000) / (0.9 * L_in * (d_in**2))
    rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
    rho_req = max(rho, 0.0018)
    As_req = rho_req * L_in * d_in  # in²
    bar_dia, bar_area = rebar_options[selected_rebar]
    num_bars = int(np.ceil(As_req / bar_area))
    spacing = round(((L_in - 6) / max(1, (num_bars - 1))), 2)

  # --- Matplotlib Section Diagram Function ---
  def draw_section_diagram():
    fig, ax = plt.subplots(figsize=(6, 3.5))

    # Draw Soil & Ground Level
    ax.fill_between([-B / 2 - 0.5, B / 2 + 0.5], [0, 0], [-Df - h_foot - 0.2, -Df - h_foot - 0.2], color="#E5D3B3", alpha=0.5, label="Soil Mass")
    ax.plot([-B / 2 - 0.5, B / 2 + 0.5], [-Df, -Df], "k--", linewidth=1, label="Ground Level (GL)")

    # Draw Concrete Footing
    ax.add_patch(plt.Rectangle((-B / 2, -Df - h_foot), B, h_foot, facecolor="#A3A3A3", edgecolor="black", linewidth=1.5, label="Concrete Footing"))

    # Draw Column
    ax.add_patch(plt.Rectangle((-cx / 2, -Df), cx, Df + 0.3, facecolor="#737373", edgecolor="black", linewidth=1.5, label="RCC Column"))

    # Draw Rebar (Bottom Reinforcement Layer)
    rebar_y = -Df - h_foot + cover
    ax.plot([-B / 2 + cover, B / 2 - cover], [rebar_y, rebar_y], color="red", linewidth=3, label=f"Main Rebars: {num_bars}-{selected_rebar}")

    # Draw Points for Cross Rebars
    x_rebars = np.linspace(-B / 2 + cover, B / 2 - cover, min(num_bars, 8))
    ax.scatter(x_rebars, [rebar_y + 0.03] * len(x_rebars), color="darkred", s=25, zorder=5, label="Distribution Bars")

    # Formatting Plot
    ax.set_xlim(-B / 2 - 0.6, B / 2 + 0.6)
    ax.set_ylim(-Df - h_foot - 0.3, 0.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper right", fontsize=6, framealpha=0.9)
    plt.title(f"Footing Structural Section Elevation ({B}m x {L}m)", fontsize=9, fontweight="bold")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    buf.seek(0)
    plt.close()
    return buf

  # Display Results in UI Right Column
  with col_res:
    st.header("📊 Detailed Design Results")

    st.subheader("1. Capacity & Structural Summary")
    r1, r2 = st.columns(2)
    r1.metric("Allowable Bearing Capacity", f"{q_allow:.2f} {'kPa' if not is_imperial else 'ksf'}")
    r2.metric("Factored Ultimate Load (Pu)", f"{Pu:.1f} {'kN' if not is_imperial else 'kips'}")

    r3, r4 = st.columns(2)
    p_status = "✅ PASS" if Phi_Vc_punch >= Vu_punch else "❌ FAIL"
    r3.metric("Punching Shear Check", f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}", delta=p_status)
    w_status = "✅ PASS" if Phi_Vc_oneway >= Vu_oneway else "❌ FAIL"
    r4.metric("One-Way Shear Check", f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}", delta=w_status)

    st.subheader("2. Reinforcement Recommendation")
    st.info(f"<b>Required Area (As):</b> {As_req:.2f} {'mm²' if not is_imperial else 'in²'}<br/>"
            f"<b>Provide:</b> Use <b>{num_bars} Nos - {selected_rebar}</b> bars @ <b>{spacing} {'mm' if not is_imperial else 'in'} c/c</b> (Both Directions)", unsafe_allow_html=True)

    st.subheader("3. Cross-Section Elevation View")
    fig_buf = draw_section_diagram()
    st.image(fig_buf)

  # --- Step-by-Step PDF Generation ---
  def generate_pdf():
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("T", parent=styles["Heading1"], fontSize=14, textColor=colors.HexColor("#1E3A8A"), spaceAfter=8)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10, textColor=colors.HexColor("#2563EB"), spaceBefore=6, spaceAfter=4)
    body_style = ParagraphStyle("B", parent=styles["Normal"], fontSize=8, leading=11)

    story.append(Paragraph("<b>Geotechnical & Structural Footing Design Calculation</b>", title_style))

    # Inputs Table
    story.append(Paragraph("<b>1. Design Inputs & Selected Codes</b>", h2_style))
    input_data = [
        ["Parameter", "Value", "Unit", "Parameter", "Value", "Unit"],
        ["Geo Method", method, "-", "Code Standard", aci_version, "-"],
        ["Footing B x L", f"{B} x {L}", "m/ft", "Thickness (h)", f"{h_foot}", "m/ft"],
        ["Column cx x cy", f"{cx} x {cy}", "m/ft", "SPT N-value", f"{N_spt if N_spt else 'N/A'}", "-"],
        ["f'c Concrete", f"{fc}", "MPa/psi", "fy Steel", f"{fy}", "MPa/psi"],
    ]
    t_in = Table(input_data, colWidths=[100, 70, 40, 100, 70, 40])
    t_in.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ]))
    story.append(t_in)

    # Detailed Step-by-Step Breakdown
    story.append(Paragraph("<b>2. Step-by-step Calculation Procedure</b>", h2_style))
    steps_text = [
        f"<b>Step 1: Geotechnical Capacity Check ({method})</b><br/>"
        f"• Surcharge overburden load (q) = {q_surcharge:.2f} | Effective γ = {gamma_eff:.2f}<br/>"
        f"• Ultimate Capacity (q_ult) = {q_ult:.2f} | Allowable Capacity (q_allow) = {q_allow:.2f}",

        f"<b>Step 2: Factored Soil Pressure & Design Shears (ACI 318)</b><br/>"
        f"• Factored Pressure qu = 1.5 × q_allow = {qu_factored:.2f}<br/>"
        f"• Effective depth (d) = {d_eff:.3f} | Size effect factor (λs) = {lambda_s:.3f}<br/>"
        f"• Punching Shear: Vu = {Vu_punch:.1f} vs ϕVc = {Phi_Vc_punch:.1f} → <b>{'PASS' if Phi_Vc_punch>=Vu_punch else 'FAIL'}</b><br/>"
        f"• One-Way Shear: Vu = {Vu_oneway:.1f} vs ϕVc = {Phi_Vc_oneway:.1f} → <b>{'PASS' if Phi_Vc_oneway>=Vu_oneway else 'FAIL'}</b>",

        f"<b>Step 3: Flexural Reinforcement Design & Bar Selection</b><br/>"
        f"• Critical Cantilever Moment (Mu) = {Mu:.2f}<br/>"
        f"• Required Steel Area (As) = {As_req:.2f} {'mm²' if not is_imperial else 'in²'}<br/>"
        f"• <b>Provided Rebar Setup: Use {num_bars} Nos - {selected_rebar} bars @ {spacing} {'mm' if not is_imperial else 'in'} c/c</b>"
    ]
    for step in steps_text:
      story.append(Paragraph(step, body_style))
      story.append(Spacer(1, 4))

    # Add Diagram to PDF
    story.append(Paragraph("<b>3. Structural Footing Section Elevation</b>", h2_style))
    img_buf = draw_section_diagram()
    story.append(Image(img_buf, width=380, height=220))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

  st.markdown("---")
  st.download_button(
      label="📥 Download Detailed Design Report with Section Diagram (PDF)",
      data=generate_pdf(),
      file_name="Footing_Design_Detailed_Report.pdf",
      mime="application/pdf",
      use_container_width=True,
  )
