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

# Page Setup
st.set_page_config(
    page_title="Multi-Layer Footing Design Suite", page_icon="🏗️", layout="wide"
)
st.title("🏗️ Multi-Layer Geotechnical & Structural Footing Design Suite")

col_in, col_res = st.columns([1.1, 1.1])

with col_in:
  st.header("1. General & Unit System Selection")
  unit_system = st.radio(
      "Unit System",
      [
          "SI Units (m, kN, kPa, mm)",
          "Metric Ton System (m, ton, t/m², mm)",
          "FPS - Kip System (ft, kips, ksf, in)",
          "FPS - Ton System (ft, ton, tsf, in)",
      ],
  )

  is_imperial = "FPS" in unit_system
  is_ton = "Ton" in unit_system

  # Units Label Mapping
  u_len = "ft" if is_imperial else "m"
  u_stress = (
      "tsf"
      if (is_imperial and is_ton)
      else (
          "ksf"
          if is_imperial
          else ("t/m²" if is_ton else "kPa")
      )
  )
  u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
  u_rebar = "in" if is_imperial else "mm"

  geo_input_mode = st.radio(
      "Geotechnical Calculation Method",
      [
          "c-phi Parameters (Analytical - Terzaghi/Meyerhof)",
          "SPT N-value (Empirical Method - Meyerhof/Bowles)",
      ],
  )

  st.header("2. Multi-Layer Soil Stratigraphy")
  num_layers = st.number_input("Number of Soil Layers", 1, 5, 2)

  soil_layers = []
  for i in range(int(num_layers)):
    st.subheader(f"Soil Layer {i+1}")
    lc1, lc2, lc3, lc4 = st.columns(4)
    thick = lc1.number_input(
        f"Thick ({u_len})",
        0.5,
        50.0,
        1.5 if i == 0 else 3.0,
        key=f"thick_{i}",
    )
    g_unit = lc2.number_input(
        f"γ ({u_gamma})",
        0.0,
        500.0,
        (
            (115.0 if is_imperial else (1.8 if is_ton else 18.0))
            if i == 0
            else (125.0 if is_imperial else (2.0 if is_ton else 20.0))
        ),
        key=f"gamma_{i}",
    )

    if "c-phi" in geo_input_mode:
      c_i = lc3.number_input(
          f"c ({u_stress})",
          0.0,
          5000.0,
          10.0 if not is_imperial else 0.2,
          key=f"c_{i}",
      )
      phi_i = lc4.number_input(
          "φ (deg)", 0.0, 45.0, 28.0 if i == 0 else 32.0, key=f"phi_{i}"
      )
      n_spt_i = 0
    else:
      n_spt_i = lc3.number_input(
          "SPT N", 1, 100, 12 if i == 0 else 22, key=f"n_{i}"
      )
      c_i, phi_i = 0.0, 0.0

    soil_layers.append({
        "thickness": thick,
        "gamma": g_unit,
        "c": c_i,
        "phi": phi_i,
        "N": n_spt_i,
    })

  st.header("3. Footing Geometry & Water Table")
  B = st.number_input(
      f"Width B ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0
  )
  L = st.number_input(
      f"Length L ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0
  )
  Df = st.number_input(
      f"Embedment Depth Df ({u_len})", 0.0, 20.0, 1.0 if not is_imperial else 3.5
  )
  Dw = st.number_input(
      f"Water Table Depth Dw ({u_len})",
      0.0,
      50.0,
      1.5 if not is_imperial else 5.0,
  )
  FS = st.number_input("Geotechnical Safety Factor (FS)", 1.0, 10.0, 3.0)

  st.header("4. Structural & Rebar Details")
  aci_version = st.selectbox(
      "ACI 318 Code Standard",
      [
          "ACI 318-22",
          "ACI 318-19",
          "ACI 318-14",
          "ACI 318-11",
          "ACI 318-08",
          "ACI 318-05",
      ],
  )

  u_fc = "psi" if is_imperial else "MPa"
  fc = st.number_input(
      f"Concrete Strength f'c ({u_fc})",
      10.0,
      10000.0,
      28.0 if not is_imperial else 4000.0,
  )
  fy = st.number_input(
      f"Steel Yield Strength fy ({u_fc})",
      100.0,
      100000.0,
      420.0 if not is_imperial else 60000.0,
  )

  col_x, col_y = st.columns(2)
  cx = col_x.number_input(
      f"Column cx ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.25
  )
  cy = col_y.number_input(
      f"Column cy ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.25
  )
  h_foot = st.number_input(
      f"Thickness h ({u_len})", 0.1, 5.0, 0.45 if not is_imperial else 1.5
  )

  # Metric Rebar Selection starting from 16mm up to 32mm
  if not is_imperial:
    rebar_options = {
        "16 mm": {"dia": 16.0, "area": 201.06},
        "18 mm": {"dia": 18.0, "area": 254.47},
        "20 mm": {"dia": 20.0, "area": 314.16},
        "22 mm": {"dia": 22.0, "area": 380.13},
        "25 mm": {"dia": 25.0, "area": 490.87},
        "32 mm": {"dia": 32.0, "area": 804.25},
    }
  else:
    rebar_options = {
        "#5 (0.625in)": {"dia": 0.625, "area": 0.31},
        "#6 (0.75in)": {"dia": 0.75, "area": 0.44},
        "#7 (0.875in)": {"dia": 0.875, "area": 0.60},
        "#8 (1.0in)": {"dia": 1.0, "area": 0.79},
        "#9 (1.128in)": {"dia": 1.128, "area": 1.00},
    }

  col_rb, col_tol = st.columns(2)
  selected_rebar = col_rb.selectbox(
      "Select Reinforcement Bar Size", list(rebar_options.keys())
  )

  bar_tolerance_pct = col_tol.number_input(
      "Market Bar Size Reduction (%)",
      min_value=0.0,
      max_value=15.0,
      value=0.0,
      step=0.5,
      help="ဈေးကွက်ထဲတွင် တကယ့်အမှန် rebar size လျော့နည်းနိုင်သဖြင့် Effective Area ကို % ဖြင့် လျှော့တွက်ရန်",
  )

  # Calculate Nominal and Effective Actual Area
  nom_dia = rebar_options[selected_rebar]["dia"]
  nom_area = rebar_options[selected_rebar]["area"]
  actual_area = nom_area * (1.0 - (bar_tolerance_pct / 100.0))

  st.markdown("---")
  calc_trigger = st.button(
      "🚀 Calculate Multi-Layer Design", type="primary", use_container_width=True
  )

# --- Calculation Engine ---
if calc_trigger or "calculated" in st.session_state:
  st.session_state["calculated"] = True

  # 1. Multi-Layer Overburden Surcharge (q) Calculation
  q_surcharge = 0.0
  current_depth = 0.0
  gamma_w = 62.4 if is_imperial else (1.0 if is_ton else 9.81)

  bearing_layer_idx = 0
  for idx, layer in enumerate(soil_layers):
    layer_top = current_depth
    layer_bottom = current_depth + layer["thickness"]

    if Df >= layer_top and Df < layer_bottom:
      bearing_layer_idx = idx

    if Df > layer_top:
      effective_thick = min(Df, layer_bottom) - layer_top
      if Dw < min(Df, layer_bottom):
        dry_thick = max(0.0, Dw - layer_top)
        sat_thick = effective_thick - dry_thick
        q_surcharge += (dry_thick * layer["gamma"]) + (
            sat_thick * (layer["gamma"] - gamma_w)
        )
      else:
        q_surcharge += effective_thick * layer["gamma"]

    current_depth = layer_bottom

  target_layer = soil_layers[bearing_layer_idx]

  # 2. Geotechnical Capacity Engine
  if "SPT N-value" in geo_input_mode:
    N_val = target_layer["N"]
    Kd = min(1.33, 1 + 0.33 * (Df / B))

    if is_imperial:
      q_allow = (N_val / 4.0) * (1.0 if is_ton else 2.0) * Kd
    else:
      q_allow = (N_val * 1.2 if is_ton else N_val / 0.05) * Kd

    q_ult = q_allow * FS
    c_val, phi_val = 0.0, 0.0
  else:
    c_val = target_layer["c"]
    phi_val = target_layer["phi"]
    rad_phi = np.radians(phi_val)

    if phi_val > 0:
      Nq = (
          np.exp(np.pi * np.tan(rad_phi))
          * (np.tan(np.radians(45 + phi_val / 2))) ** 2
      )
      Nc = (Nq - 1) / np.tan(rad_phi)
      Ng = 2 * (Nq + 1) * np.tan(rad_phi)
    else:
      Nc, Nq, Ng = 5.14, 1.0, 0.0

    gamma_eff = target_layer["gamma"] - (gamma_w if Dw <= Df else 0.0)
    q_ult = (c_val * Nc) + (q_surcharge * Nq) + (0.5 * gamma_eff * B * Ng)
    q_allow = q_ult / FS

  # 3. Structural Design Calculations (ACI 318)
  cover = 0.075 if not is_imperial else (3.0 / 12.0)
  d_eff = h_foot - cover

  qu_factored = 1.5 * q_allow
  Pu = qu_factored * B * L

  if aci_version in ["ACI 318-19", "ACI 318-22"]:
    d_mm_check = d_eff * 1000 if not is_imperial else d_eff * 12 * 25.4
    lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_mm_check)))
  else:
    lambda_s = 1.0

  # Shear Verification
  bo = 2 * ((cx + d_eff) + (cy + d_eff))
  Area_bo = (cx + d_eff) * (cy + d_eff)
  Vu_punch = qu_factored * (B * L - Area_bo)

  crit_dist = (B / 2) - (cx / 2) - d_eff
  Vu_oneway = qu_factored * L * max(0.0, crit_dist)

  phi_s = 0.75
  if not is_imperial:
    vc_punch = 0.33 * lambda_s * np.sqrt(fc)
    vc_oneway = 0.17 * lambda_s * np.sqrt(fc)
    force_mult = 1.0 / 9.81 if is_ton else 1.0
    Phi_Vc_punch = (
        (phi_s * vc_punch * (bo * 1000) * (d_eff * 1000)) / 1000.0
    ) * force_mult
    Phi_Vc_oneway = (
        (phi_s * vc_oneway * (L * 1000) * (d_eff * 1000)) / 1000.0
    ) * force_mult
  else:
    vc_punch = 4.0 * lambda_s * np.sqrt(fc)
    vc_oneway = 2.0 * lambda_s * np.sqrt(fc)
    force_mult = 0.5 if is_ton else 1.0
    Phi_Vc_punch = (
        (phi_s * vc_punch * (bo * 12) * (d_eff * 12)) / 1000.0
    ) * force_mult
    Phi_Vc_oneway = (
        (phi_s * vc_oneway * (L * 12) * (d_eff * 12)) / 1000.0
    ) * force_mult

  # Flexural Reinforcement Design
  cantilever = (B - cx) / 2
  Mu = (qu_factored * L * (cantilever**2)) / 2

  if not is_imperial:
    L_mm, d_mm = L * 1000, d_eff * 1000
    Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
    Rn = Mu_Nmm / (0.9 * L_mm * (d_mm**2))
    rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
    rho_req = max(rho, 0.0018)
    As_req = rho_req * L_mm * d_mm
    num_bars = int(np.ceil(As_req / actual_area))
    num_bars = max(2, num_bars)
    spacing = int((L_mm - 150) / max(1, (num_bars - 1)))
  else:
    L_in, d_in = L * 12, d_eff * 12
    Mu_inlbs = Mu * 12000 * (2.0 if is_ton else 1.0)
    Rn = Mu_inlbs / (0.9 * L_in * (d_in**2))
    rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
    rho_req = max(rho, 0.0018)
    As_req = rho_req * L_in * d_in
    num_bars = int(np.ceil(As_req / actual_area))
    num_bars = max(2, num_bars)
    spacing = round((L_in - 6) / max(1, (num_bars - 1)), 2)

  # Section Plot Generator
  def draw_multilayer_section():
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    y_top = 0.0
    colors_list = ["#E5D3B3", "#D2B48C", "#C4A484", "#B8860B", "#A0522D"]

    for idx, layer in enumerate(soil_layers):
      y_bottom = y_top - layer["thickness"]
      ax.fill_between(
          [-B / 2 - 0.8, B / 2 + 0.8],
          [y_top, y_top],
          [y_bottom, y_bottom],
          color=colors_list[idx % 5],
          alpha=0.6,
          label=f"Layer {idx+1} ({layer['thickness']}{u_len})",
      )
      y_top = y_bottom

    ax.plot(
        [-B / 2 - 0.8, B / 2 + 0.8],
        [0, 0],
        "k--",
        linewidth=1,
        label="Ground Level",
    )
    if Dw <= abs(y_top):
      ax.plot(
          [-B / 2 - 0.8, B / 2 + 0.8],
          [-Dw, -Dw],
          "b-.",
          linewidth=1.2,
          label="Water Table (GWT)",
      )

    ax.add_patch(
        plt.Rectangle(
            (-B / 2, -Df - h_foot),
            B,
            h_foot,
            facecolor="#9CA3AF",
            edgecolor="black",
            linewidth=1.5,
            label="Footing",
        )
    )
    ax.add_patch(
        plt.Rectangle(
            (-cx / 2, -Df),
            cx,
            Df + 0.3,
            facecolor="#4B5563",
            edgecolor="black",
            linewidth=1.5,
            label="Column",
        )
    )

    rebar_y = -Df - h_foot + cover
    ax.plot(
        [-B / 2 + cover, B / 2 - cover],
        [rebar_y, rebar_y],
        color="red",
        linewidth=2.5,
        label=f"Rebars: {num_bars}-{selected_rebar}",
    )

    ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
    ax.set_ylim(y_top - 0.2, 0.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.35, 1.0),
        fontsize=6.5,
        framealpha=0.9,
    )
    plt.title(
        "Multi-Layer Footing Cross-Section Elevation",
        fontsize=9,
        fontweight="bold",
    )
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close()
    return buf

  # Results Display
  with col_res:
    st.header("📊 Results & Verification Summary")

    st.subheader("1. Geotechnical & Bearing Capacity")
    m1, m2 = st.columns(2)
    m1.metric("Effective Overburden (q)", f"{q_surcharge:.2f} {u_stress}")
    m2.metric("Bearing Soil Layer", f"Layer {bearing_layer_idx+1}")

    m3, m4 = st.columns(2)
    m3.metric("Ultimate Capacity (q_ult)", f"{q_ult:.2f} {u_stress}")
    m4.metric("Allowable Capacity (q_allow)", f"{q_allow:.2f} {u_stress}")

    st.subheader("2. Structural Shears Check")
    s1, s2 = st.columns(2)
    p_check = Phi_Vc_punch >= Vu_punch
    s1.metric(
        "Punching Shear",
        f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}",
        delta="✅ PASS" if p_check else "❌ FAIL",
    )

    w_check = Phi_Vc_oneway >= Vu_oneway
    s2.metric(
        "One-Way Shear",
        f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}",
        delta="✅ PASS" if w_check else "❌ FAIL",
    )

    st.subheader("3. Reinforcement Arrangement")
    st.success(
        f"<b>Required Area (As):</b> {As_req:.2f} {'mm²' if not is_imperial else 'in²'}<br/>"
        f"<b>Effective Bar Area ({100-bar_tolerance_pct}%):</b> {actual_area:.1f} {'mm²' if not is_imperial else 'in²'}<br/>"
        f"<b>Design Recommendation:</b> Provide <b>{num_bars} Nos - {selected_rebar}</b> bars @ <b>{spacing} {u_rebar} c/c</b> (Both Ways)",
        icon="💡",
    )

    st.subheader("4. Multi-Layer Cross Section View")
    st.image(draw_multilayer_section())

  # PDF Report Generator
  def generate_pdf():
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "T",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=10,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=5,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "B", parent=styles["Normal"], fontSize=8, leading=11
    )

    story.append(
        Paragraph(
            "<b>Multi-Layer Geotechnical & Structural Design Report</b>",
            title_style,
        )
    )

    story.append(Paragraph("<b>1. Soil Stratigraphy Inputs</b>", h2_style))
    strat_data = [
        ["Layer", f"Thickness ({u_len})", f"γ ({u_gamma})", "c / N-value", "φ"]
    ]
    for idx, ly in enumerate(soil_layers):
      param_str = f"N={ly['N']}" if "SPT" in geo_input_mode else f"c={ly['c']}"
      strat_data.append([
          f"Layer {idx+1}",
          f"{ly['thickness']}",
          f"{ly['gamma']}",
          param_str,
          f"{ly['phi']}°",
      ])

    t_strat = Table(strat_data, colWidths=[70, 90, 90, 90, 90])
    t_strat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ]))
    story.append(t_strat)

    story.append(
        Paragraph("<b>2. Calculation Step-by-Step Summary</b>", h2_style)
    )
    steps = [
        f"• <b>Overburden Surcharge:</b> Calculated q at Df = <b>{q_surcharge:.2f} {u_stress}</b> (Bearing Layer: Layer {bearing_layer_idx+1})<br/>",
        f"• <b>Bearing Capacity:</b> q_ult = {q_ult:.2f} {u_stress} | Allowable Capacity (q_allow) = <b>{q_allow:.2f} {u_stress}</b> (FS={FS})<br/>",
        f"• <b>Shear Checks ({aci_version}):</b> Punching Vu = {Vu_punch:.1f} vs ϕVc = {Phi_Vc_punch:.1f} ({'PASS' if p_check else 'FAIL'}) | One-Way Vu = {Vu_oneway:.1f} vs ϕVc = {Phi_Vc_oneway:.1f} ({'PASS' if w_check else 'FAIL'})<br/>",
        f"• <b>Reinforcement Design:</b> Req. As = {As_req:.2f} → <b>Provide {num_bars} Nos - {selected_rebar} (Tolerance {bar_tolerance_pct}%) @ {spacing} {u_rebar} c/c</b>",
    ]
    for s in steps:
      story.append(Paragraph(s, body_style))
      story.append(Spacer(1, 3))

    story.append(
        Paragraph("<b>3. Soil Profile & Foundation Elevation</b>", h2_style)
    )
    img_buf = draw_multilayer_section()
    story.append(Image(img_buf, width=380, height=220))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

  st.markdown("---")
  st.download_button(
      label="📥 Download Comprehensive Multi-Layer Design Report (PDF)",
      data=generate_pdf(),
      file_name="MultiLayer_Footing_Design_Report.pdf",
      mime="application/pdf",
      use_container_width=True,
  )
