import io
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(
    page_title="Geotechnical & Structural Footing Suite",
    page_icon="🏗️",
    layout="wide",
)
st.title("🏗️ Geotechnical Bearing Capacity & Structural Footing Suite")

col_in, col_res = st.columns([1, 1.2])

with col_in:
  # --- 1. Unit System Selection ---
  st.header("1. Unit System & Standards")
  unit_system = st.radio(
      "Unit System",
      [
          "SI Units (m, kN, kPa)",
          "Metric Ton System (m, ton, t/m²)",
          "FPS - Kip System (ft, kips, ksf)",
          "FPS - Ton System (ft, ton, tsf)",
      ],
  )

  # Define Labels & Units dynamically
  if unit_system == "SI Units (m, kN, kPa)":
    u_len, u_stress, u_gamma = "m", "kPa", "kN/m³"
    gamma_w_val = 9.81
    c_default, g_dry_def, g_sat_def = 15.0, 18.0, 20.0
    b_default, df_default, dw_default = 1.5, 1.0, 0.5
    u_fc, fc_def, fy_def = "MPa", 28.0, 420.0
    u_col, col_def, h_def = "m", 0.4, 0.5
    u_area = "mm²"

  elif unit_system == "Metric Ton System (m, ton, t/m²)":
    u_len, u_stress, u_gamma = "m", "t/m²", "t/m³"
    gamma_w_val = 1.0
    c_default, g_dry_def, g_sat_def = 1.5, 1.8, 2.0
    b_default, df_default, dw_default = 1.5, 1.0, 0.5
    u_fc, fc_def, fy_def = "MPa", 28.0, 420.0
    u_col, col_def, h_def = "m", 0.4, 0.5
    u_area = "cm²"

  elif unit_system == "FPS - Kip System (ft, kips, ksf)":
    u_len, u_stress, u_gamma = "ft", "ksf", "pcf"
    gamma_w_val = 62.4
    c_default, g_dry_def, g_sat_def = 0.3, 115.0, 125.0
    b_default, df_default, dw_default = 5.0, 3.0, 2.0
    u_fc, fc_def, fy_def = "psi", 4000.0, 60000.0
    u_col, col_def, h_def = "ft", 1.5, 1.5
    u_area = "in²"

  else:  # FPS - Ton System
    u_len, u_stress, u_gamma = "ft", "tsf (ton/ft²)", "pcf"
    gamma_w_val = 62.4
    c_default, g_dry_def, g_sat_def = 0.15, 115.0, 125.0
    b_default, df_default, dw_default = 5.0, 3.0, 2.0
    u_fc, fc_def, fy_def = "psi", 4000.0, 60000.0
    u_col, col_def, h_def = "ft", 1.5, 1.5
    u_area = "in²"

  method = st.selectbox(
      "Geotechnical Design Method",
      ["Terzaghi Method", "Hansen Method", "Meyerhof Method", "Vesić Method"],
  )

  st.header("2. Soil Parameters")
  c = st.number_input(f"Cohesion, c ({u_stress})", 0.0, 5000.0, c_default)
  phi = st.number_input("Friction Angle, φ (deg)", 0.0, 45.0, 28.0)
  gamma_dry = st.number_input(f"Dry/Moist γ ({u_gamma})", 0.0, 500.0, g_dry_def)
  gamma_sat = st.number_input(f"Saturated γ_sat ({u_gamma})", 0.0, 500.0, g_sat_def)

  st.header("3. Geometry & Water Table")
  footing_shape = st.selectbox(
      "Footing Shape", ["Strip / Continuous", "Square", "Rectangle"]
  )
  B = st.number_input(f"Width, B ({u_len})", 0.1, 100.0, b_default)

  max_L = 500.0 if footing_shape == "Strip / Continuous" else 100.0
  default_L = 500.0 if footing_shape == "Strip / Continuous" else b_default
  L = st.number_input(
      f"Length, L ({u_len})", min_value=0.1, max_value=max_L, value=default_L
  )

  Df = st.number_input(f"Depth, Df ({u_len})", 0.0, 50.0, df_default)
  ex = st.number_input(f"Eccentricity e_x ({u_len})", 0.0, B / 2, 0.0)
  ey = st.number_input(f"Eccentricity e_y ({u_len})", 0.0, L / 2, 0.0)
  Dw = st.number_input(f"Water Table Depth, Dw ({u_len})", 0.0, 100.0, dw_default)
  FS = st.number_input("Factor of Safety (FS)", 1.0, 10.0, 3.0)

  # --- Structural Inputs ---
  st.header("4. Structural Design Parameters (ACI 318)")
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
      f"Concrete Compressive Strength, f'c ({u_fc})", 10.0, 10000.0, fc_def
  )
  fy = st.number_input(
      f"Steel Yield Strength, fy ({u_fc})", 100.0, 100000.0, fy_def
  )

  c_col1, c_col2 = st.columns(2)
  cx = c_col1.number_input(f"Column Width, cx ({u_col})", 0.1, 10.0, col_def)
  cy = c_col2.number_input(f"Column Depth, cy ({u_col})", 0.1, 10.0, col_def)
  h_foot = st.number_input(f"Total Thickness, h ({u_len})", 0.1, 10.0, h_def)

# --- Geotechnical Calculation Engine ---
B_eff = max(0.01, B - (2 * ex))
L_eff = max(0.01, L - (2 * ey))

if unit_system == "FPS - Ton System (ft, ton, tsf)":
  g_dry_calc = gamma_dry / 2000.0
  g_sat_calc = gamma_sat / 2000.0
  gamma_w_calc = 62.4 / 2000.0
else:
  g_dry_calc = gamma_dry
  g_sat_calc = gamma_sat
  gamma_w_calc = gamma_w_val

if Dw <= Df:
  q = (Dw * g_dry_calc) + ((Df - Dw) * (g_sat_calc - gamma_w_calc))
  gamma_eff = g_sat_calc - gamma_w_calc
elif Df < Dw <= (Df + B_eff):
  q = Df * g_dry_calc
  gamma_eff = (g_sat_calc - gamma_w_calc) + ((Dw - Df) / B_eff) * (
      g_dry_calc - (g_sat_calc - gamma_w_calc)
  )
else:
  q = Df * g_dry_calc
  gamma_eff = g_dry_calc

rad_phi = np.radians(phi)

if method == "Terzaghi Method":
  if phi > 0:
    a = np.exp((0.75 * np.pi - rad_phi / 2) * np.tan(rad_phi))
    Nq = (a**2) / (2 * (np.cos(np.radians(45 + phi / 2))) ** 2)
    Nc = (Nq - 1) / np.tan(rad_phi)
    Kp_terzaghi = (np.tan(np.radians(45 + phi / 2))) ** 2
    Ng = (np.tan(rad_phi) / 2) * (Kp_terzaghi / (np.cos(rad_phi)) ** 2 - 1)
  else:
    Nc, Nq, Ng = 5.7, 1.0, 0.0

  sc, sg = (1.3, 0.8) if footing_shape == "Square" else (1.0, 1.0)
  sq = 1.0
  q_ult = (c * Nc * sc) + (q * Nq) + (0.5 * gamma_eff * B_eff * Ng * sg)

else:
  if phi > 0:
    Nq = (
        np.exp(np.pi * np.tan(rad_phi))
        * (np.tan(np.radians(45 + phi / 2))) ** 2
    )
    Nc = (Nq - 1) / np.tan(rad_phi)
  else:
    Nq, Nc = 1.0, 5.14

  if method == "Hansen Method":
    Ng = 1.5 * (Nq - 1) * np.tan(rad_phi) if phi > 0 else 0.0
    sc = (
        1 + (Nq / Nc) * (B_eff / L_eff)
        if phi > 0
        else 1 + 0.2 * (B_eff / L_eff)
    )
    sq = 1 + (B_eff / L_eff) * np.tan(rad_phi)
    sg = 1 - 0.4 * (B_eff / L_eff)
  elif method == "Meyerhof Method":
    Ng = (Nq - 1) * np.tan(1.4 * rad_phi) if phi > 0 else 0.0
    Kp = (np.tan(np.radians(45 + phi / 2))) ** 2
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

# --- Structural Calculation Engine (ACI 318) ---
is_imperial = "FPS" in unit_system
cover = 0.075 if not is_imperial else (3.0 / 12.0)  # 75mm or 3 inches
d_eff = max(0.01, h_foot - cover)

# Load Conversion (Estimated Factored Ultimate Load Pu)
# Factored soil pressure qu = 1.5 * q_allow
qu_factored = 1.5 * q_allow
Pu_factored = qu_factored * B * L

# Size Effect Factor (λs) for ACI 318-19 & ACI 318-22
if aci_version in ["ACI 318-19", "ACI 318-22"]:
  if not is_imperial:
    d_mm = d_eff * 1000
    lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_mm)))
  else:
    d_in = d_eff * 12
    lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_in)))
else:
  lambda_s = 1.0  # ACI 318-05 to ACI 318-14 do not have size effect factor

# 1. Two-Way Punching Shear
bo = 2 * ((cx + d_eff) + (cy + d_eff))
Area_inside_bo = (cx + d_eff) * (cy + d_eff)
Vu_punch = qu_factored * (B * L - Area_inside_bo)

beta_c = max(cx, cy) / min(cx, cy)
alpha_s = 40  # Interior column

phi_shear = 0.75

if not is_imperial:
  # Metric Calculations (fc in MPa, dimensions in mm/m)
  vc1 = 0.17 * (1 + 2 / beta_c) * np.sqrt(fc) * lambda_s
  vc2 = 0.083 * (alpha_s * (d_eff * 1000) / (bo * 1000) + 2) * np.sqrt(fc) * lambda_s
  vc3 = 0.33 * np.sqrt(fc) * lambda_s
  vc_punch = min(vc1, vc2, vc3)  # N/mm² = MPa
  Phi_Vc_punch = (
      phi_shear * vc_punch * (bo * 1000) * (d_eff * 1000)
  ) / 1000.0  # kN (or tons)

  # 2. One-Way Beam Shear
  crit_dist = (B / 2) - (cx / 2) - d_eff
  Vu_oneway = qu_factored * L * max(0.0, crit_dist)
  vc_oneway = 0.17 * lambda_s * np.sqrt(fc)
  Phi_Vc_oneway = (
      phi_shear * vc_oneway * (L * 1000) * (d_eff * 1000)
  ) / 1000.0

  # 3. Flexural Design
  cantilever_L = (B - cx) / 2
  Mu = (qu_factored * L * (cantilever_L**2)) / 2  # kNm
  phi_flex = 0.90
  Rn = (Mu * 1e6) / (phi_flex * (L * 1000) * ((d_eff * 1000) ** 2))
  rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
  rho_min = 0.0018
  rho_req = max(rho, rho_min)
  As_req = rho_req * (L * 1000) * (d_eff * 1000)  # mm²
  if unit_system == "Metric Ton System (m, ton, t/m²)":
    As_req = As_req / 100.0  # cm²

else:
  # Imperial Calculations (fc in psi, dimensions in inches/ft)
  d_in = d_eff * 12
  bo_in = bo * 12
  L_in = L * 12

  vc1 = 2 * (1 + 2 / beta_c) * np.sqrt(fc) * lambda_s
  vc2 = (alpha_s * d_in / bo_in + 2) * np.sqrt(fc) * lambda_s
  vc3 = 4 * np.sqrt(fc) * lambda_s
  vc_punch = min(vc1, vc2, vc3)  # psi
  Phi_Vc_punch = (phi_shear * vc_punch * bo_in * d_in) / 1000.0  # kips/tons

  crit_dist = (B / 2) - (cx / 2) - d_eff
  Vu_oneway = qu_factored * L * max(0.0, crit_dist)
  vc_oneway = 2 * lambda_s * np.sqrt(fc)
  Phi_Vc_oneway = (phi_shear * vc_oneway * L_in * d_in) / 1000.0

  cantilever_L = (B - cx) / 2
  Mu = (qu_factored * L * (cantilever_L**2)) / 2  # kips-ft
  phi_flex = 0.90
  Rn = (Mu * 12000) / (phi_flex * L_in * (d_in**2))
  rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
  rho_min = 0.0018
  rho_req = max(rho, rho_min)
  As_req = rho_req * L_in * d_in  # in²

# --- Results UI ---
with col_res:
  st.header("📊 Results Summary")
  st.subheader("Geotechnical Bearing Capacity")
  m1, m2 = st.columns(2)
  m1.metric(f"Effective Width (B')", f"{B_eff:.2f} {u_len}")
  m2.metric(f"Effective Surcharge (q)", f"{q:.2f} {u_stress}")

  m3, m4 = st.columns(2)
  m3.metric(f"Ultimate Capacity (q_ult)", f"{q_ult:.2f} {u_stress}")
  m4.metric(f"Allowable Capacity (q_allow)", f"{q_allow:.2f} {u_stress}")

  st.markdown("---")
  st.subheader(f"Structural Verification ({aci_version})")

  s1, s2, s3 = st.columns(3)
  punch_pass = Phi_Vc_punch >= Vu_punch
  s1.metric(
      "Punching Shear",
      f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}",
      delta="✅ PASS" if punch_pass else "❌ FAIL",
  )

  oneway_pass = Phi_Vc_oneway >= Vu_oneway
  s2.metric(
      "One-Way Shear",
      f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}",
      delta="✅ PASS" if oneway_pass else "❌ FAIL",
  )

  s3.metric("Req. Steel (As)", f"{As_req:.2f} {u_area}")


# --- PDF Generator WITH GEOTECHNICAL & STRUCTURAL CALCULATIONS ---
def generate_pdf():
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  story = []
  styles = getSampleStyleSheet()

  title_style = ParagraphStyle(
      "Title",
      parent=styles["Heading1"],
      fontSize=15,
      textColor=colors.HexColor("#1E3A8A"),
      spaceAfter=10,
  )
  h2_style = ParagraphStyle(
      "H2",
      parent=styles["Heading2"],
      fontSize=11,
      textColor=colors.HexColor("#2563EB"),
      spaceBefore=8,
      spaceAfter=4,
  )
  body_style = ParagraphStyle(
      "Body", parent=styles["Normal"], fontSize=8.5, leading=12
  )

  story.append(
      Paragraph(
          "<b>Geotechnical & Structural Design Report</b>",
          title_style,
      )
  )
  story.append(Spacer(1, 4))

  # Input Summary Table
  story.append(Paragraph("<b>1. Input Parameters</b>", h2_style))
  input_data = [
      ["Parameter", "Value", "Unit", "Parameter", "Value", "Unit"],
      ["Geo Method", method, "-", "Unit System", unit_system.split()[0], "-"],
      ["ACI Standard", aci_version, "-", "Factor of Safety", f"{FS:.1f}", "-"],
      [
          "Footing (B x L)",
          f"{B:.2f} x {L:.2f}",
          u_len,
          "Thickness (h)",
          f"{h_foot:.2f}",
          u_len,
      ],
      [
          "Cohesion (c)",
          f"{c:.2f}",
          u_stress,
          "Friction Angle",
          f"{phi:.1f}",
          "deg",
      ],
      [
          "f'c Strength",
          f"{fc:.1f}",
          u_fc,
          "fy Steel Yield",
          f"{fy:.1f}",
          u_fc,
      ],
  ]
  t_input = Table(input_data, colWidths=[110, 65, 45, 110, 65, 45])
  t_input.setStyle(TableStyle([
      ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
      ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
      ("FONTSIZE", (0, 0), (-1, -1), 8),
  ]))
  story.append(t_input)

  # Step-by-Step Geotechnical Breakdown
  story.append(
      Paragraph("<b>2. Geotechnical Calculation Procedure</b>", h2_style)
  )
  geo_steps = [
      f"• Effective Footing Dimensions: B' = <b>{B_eff:.2f} {u_len}</b>, L' ="
      f" <b>{L_eff:.2f} {u_len}</b><br/>• Effective Surcharge (q) ="
      f" <b>{q:.3f} {u_stress}</b>, Effective Unit Weight (γ_eff) ="
      f" <b>{gamma_eff:.4f} {u_gamma}</b><br/>• Bearing Capacity Factors: Nc ="
      f" <b>{Nc:.3f}</b>, Nq = <b>{Nq:.3f}</b>, Nγ = <b>{Ng:.3f}</b><br/>•"
      " Ultimate Capacity (q_ult) = <b>{q_ult:.2f} {u_stress}</b> | Allowable"
      f" Capacity (q_allow) = <b>{q_allow:.2f} {u_stress}</b>"
  ]
  for step in geo_steps:
    story.append(Paragraph(step, body_style))
    story.append(Spacer(1, 4))

  # Step-by-Step Structural Breakdown
  story.append(
      Paragraph(
          f"<b>3. Structural Design Breakdown ({aci_version})</b>", h2_style
      )
  )
  struct_steps = [
      f"• Effective Depth (d) = <b>{d_eff:.3f} {u_len}</b> | Size Effect Factor"
      f" (λs) = <b>{lambda_s:.3f}</b><br/>• Factored Soil Pressure (qu) ="
      f" 1.5 × q_allow = <b>{qu_factored:.2f} {u_stress}</b><br/>•"
      f" <b>Two-Way Punching Shear:</b> Vu = <b>{Vu_punch:.1f}</b> | ϕVc ="
      f" <b>{Phi_Vc_punch:.1f}</b> -> <b>{'PASS' if punch_pass else 'FAIL'}</b><br/>•"
      f" <b>One-Way Beam Shear:</b> Vu = <b>{Vu_oneway:.1f}</b> | ϕVc ="
      f" <b>{Phi_Vc_oneway:.1f}</b> ->"
      f" <b>{'PASS' if oneway_pass else 'FAIL'}</b><br/>• <b>Flexural"
      f" Reinforcement:</b> Ultimate Moment (Mu) = <b>{Mu:.2f}</b> | Req."
      f" Steel Area (As) = <b>{As_req:.2f} {u_area}</b>"
  ]
  for step in struct_steps:
    story.append(Paragraph(step, body_style))
    story.append(Spacer(1, 4))

  # Final Summary Table
  story.append(Paragraph("<b>4. Summary Checklist</b>", h2_style))
  summary_data = [
      ["Check / Parameter", "Value / Capacity", "Status"],
      ["Allowable Bearing Capacity", f"{q_allow:.2f} {u_stress}", "OK"],
      [
          "Punching Shear Check",
          f"Vu: {Vu_punch:.1f} ≤ ϕVc: {Phi_Vc_punch:.1f}",
          "PASS" if punch_pass else "FAIL",
      ],
      [
          "One-Way Shear Check",
          f"Vu: {Vu_oneway:.1f} ≤ ϕVc: {Phi_Vc_oneway:.1f}",
          "PASS" if oneway_pass else "FAIL",
      ],
      ["Flexural Reinforcement Area", f"{As_req:.2f} {u_area}", "DESIGNED"],
  ]
  t_summary = Table(summary_data, colWidths=[180, 180, 80])
  t_summary.setStyle(TableStyle([
      ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
      ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
      ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
      ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
  ]))
  story.append(t_summary)

  doc.build(story)
  buffer.seek(0)
  return buffer


st.markdown("---")
st.download_button(
    label=(
        "📥 Download Complete Report with Geotechnical & Structural Design"
        " (PDF)"
    ),
    data=generate_pdf(),
    file_name=f"footing_design_{aci_version.replace(' ', '_')}.pdf",
    mime="application/pdf",
)
