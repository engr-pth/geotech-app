import io
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image as RLImage,
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
    u_force = "kips" if (is_imperial and not is_ton) else ("ton" if is_ton else "kN")
    u_moment = "kip-ft" if (is_imperial and not is_ton) else ("ton-m" if is_ton else "kN-m")
    u_stress = "tsf" if (is_imperial and is_ton) else ("ksf" if is_imperial else ("t/m²" if is_ton else "kPa"))
    u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
    u_rebar = "in" if is_imperial else "mm"

    geo_input_mode = st.radio(
        "Geotechnical Calculation Method",
        [
            "c-phi Parameters (Analytical - Terzaghi/Meyerhof)",
            "SPT N-value (Empirical Method - Meyerhof/Bowles)",
        ],
    )

    # --- Column Loading Inputs ---
    st.header("2. Applied Column Loads & Eccentricity")
    col_p, col_mx, col_my = st.columns(3)
    P_unfactored = col_p.number_input(f"Axial Load P ({u_force})", 0.0, 100000.0, 500.0 if not is_imperial else 100.0)
    Mx_unfactored = col_mx.number_input(f"Moment Mx ({u_moment})", 0.0, 10000.0, 0.0)
    My_unfactored = col_my.number_input(f"Moment My ({u_moment})", 0.0, 10000.0, 0.0)

    col_ex, col_ey = st.columns(2)
    ex_input = col_ex.number_input(f"Column Eccentricity ex ({u_len})", -5.0, 5.0, 0.0, step=0.05)
    ey_input = col_ey.number_input(f"Column Eccentricity ey ({u_len})", -5.0, 5.0, 0.0, step=0.05)

    st.header("3. Multi-Layer Soil Stratigraphy")
    num_layers = st.number_input("Number of Soil Layers", 1, 5, 2)

    soil_layers = []
    for i in range(int(num_layers)):
        st.subheader(f"Soil Layer {i+1}")
        lc1, lc2, lc3, lc4 = st.columns(4)
        thick = lc1.number_input(f"Thick ({u_len})", 0.5, 50.0, 1.5 if i == 0 else 3.0, key=f"thick_{i}")
        g_unit = lc2.number_input(f"γ ({u_gamma})", 0.0, 500.0, ((115.0 if is_imperial else (1.8 if is_ton else 18.0)) if i == 0 else (125.0 if is_imperial else (2.0 if is_ton else 20.0))), key=f"gamma_{i}")

        if "c-phi" in geo_input_mode:
            c_i = lc3.number_input(f"c ({u_stress})", 0.0, 5000.0, 10.0 if not is_imperial else 0.2, key=f"c_{i}")
            phi_i = lc4.number_input("φ (deg)", 0.0, 45.0, 28.0 if i == 0 else 32.0, key=f"phi_{i}")
            n_spt_i = 0
        else:
            n_spt_i = lc3.number_input("SPT N", 1, 100, 12 if i == 0 else 22, key=f"n_{i}")
            c_i, phi_i = 0.0, 0.0

        soil_layers.append({"thickness": thick, "gamma": g_unit, "c": c_i, "phi": phi_i, "N": n_spt_i})

    st.header("4. Geometry Settings (Footing & Column)")
    col_b, col_l = st.columns(2)
    B = col_b.number_input(f"Footing Width B ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)
    L = col_l.number_input(f"Footing Length L ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)

    col_cx, col_cy = st.columns(2)
    cx = col_cx.number_input(f"Column Size cx ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.0)
    cy = col_cy.number_input(f"Column Size cy ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.25)

    Df = st.number_input(f"Embedment Depth Df ({u_len})", 0.0, 20.0, 1.0 if not is_imperial else 3.5)
    h_foot = st.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 0.45 if not is_imperial else 1.5)
    Dw = st.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 1.5 if not is_imperial else 5.0)
    FS = st.number_input("Geotechnical Safety Factor (FS)", 1.0, 10.0, 3.0)

    st.header("5. Structural & Rebar Details")
    aci_version = st.selectbox("ACI 318 Code Standard", ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"])

    u_fc = "psi" if is_imperial else "MPa"
    fc = st.number_input(f"Concrete Strength f'c ({u_fc})", 10.0, 10000.0, 28.0 if not is_imperial else 4000.0)
    fy = st.number_input(f"Steel Yield Strength fy ({u_fc})", 100.0, 100000.0, 420.0 if not is_imperial else 60000.0)

    rebar_system = st.radio("Rebar Unit System Standard", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"])

    if "Metric" in rebar_system:
        rebar_options = {
            "16 mm": {"dia": 16.0, "area": 201.06, "is_metric": True},
            "18 mm": {"dia": 18.0, "area": 254.47, "is_metric": True},
            "20 mm": {"dia": 20.0, "area": 314.16, "is_metric": True},
            "25 mm": {"dia": 25.0, "area": 490.87, "is_metric": True},
        }
    else:
        rebar_options = {
            "#5 (0.625in)": {"dia": 0.625, "area": 0.31, "is_metric": False},
            "#6 (0.75in)": {"dia": 0.75, "area": 0.44, "is_metric": False},
            "#8 (1.0in)": {"dia": 1.0, "area": 0.79, "is_metric": False},
        }

    col_rb, col_tol = st.columns(2)
    selected_rebar = col_rb.selectbox("Select Reinforcement Bar", list(rebar_options.keys()))
    bar_tolerance_pct = col_tol.number_input("Market Bar Size Reduction (%)", 0.0, 15.0, 0.0, step=0.5)

    nom_area = rebar_options[selected_rebar]["area"]
    actual_area = nom_area * (1.0 - (bar_tolerance_pct / 100.0))
    is_selected_metric = rebar_options[selected_rebar]["is_metric"]

    calc_trigger = st.button("🚀 Calculate Multi-Layer Design", type="primary", use_container_width=True)

# --- Calculation Engine ---
if calc_trigger or "calculated" in st.session_state:
    st.session_state["calculated"] = True

    # 1. Total Moment & Eccentricity
    Mx_total = Mx_unfactored + (P_unfactored * abs(ey_input))
    My_total = My_unfactored + (P_unfactored * abs(ex_input))
    e_x_total = My_total / P_unfactored if P_unfactored > 0 else 0.0
    e_y_total = Mx_total / P_unfactored if P_unfactored > 0 else 0.0

    # 2. Multi-Layer Surcharge Engine
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
                q_surcharge += (dry_thick * layer["gamma"]) + (sat_thick * (layer["gamma"] - gamma_w))
            else:
                q_surcharge += effective_thick * layer["gamma"]
        current_depth = layer_bottom

    target_layer = soil_layers[bearing_layer_idx]
    B_eff = max(0.1, B - 2 * e_x_total)
    L_eff = max(0.1, L - 2 * e_y_total)

    # 3. Geotechnical Bearing Capacity
    if "SPT" in geo_input_mode:
        N_val = target_layer["N"]
        Kd = min(1.33, 1 + 0.33 * (Df / B_eff))
        if is_imperial:
            q_allow = (N_val / 4.0) * (1.0 if is_ton else 2.0) * Kd
        else:
            q_allow = (N_val * 1.2 if is_ton else N_val / 0.05) * Kd
        q_ult = q_allow * FS
        Nc, Nq, Ng = 0.0, 0.0, 0.0
    else:
        c_val = target_layer["c"]
        phi_val = target_layer["phi"]
        rad_phi = np.radians(phi_val)
        if phi_val > 0:
            Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi_val / 2))) ** 2
            Nc = (Nq - 1) / np.tan(rad_phi)
            Ng = 2 * (Nq + 1) * np.tan(rad_phi)
        else:
            Nc, Nq, Ng = 5.14, 1.0, 0.0

        gamma_eff = target_layer["gamma"] - (gamma_w if Dw <= Df else 0.0)
        q_ult = (c_val * Nc) + (q_surcharge * Nq) + (0.5 * gamma_eff * B_eff * Ng)
        q_allow = q_ult / FS

    footing_area = B * L
    q_avg = P_unfactored / footing_area
    q_max_service = q_avg + (6 * Mx_total / (B * (L**2))) + (6 * My_total / (L * (B**2)))
    is_within_kern = (e_x_total <= B / 6.0) and (e_y_total <= L / 6.0)

    # 4. Structural Design Calculations
    Pu = 1.4 * P_unfactored
    Mux_total = 1.4 * Mx_total
    qu_factored = (Pu / footing_area) + (6 * Mux_total / (B * (L**2)))

    cover = 0.075 if not is_imperial else (3.0 / 12.0)
    d_eff = h_foot - cover

    if aci_version in ["ACI 318-19", "ACI 318-22"]:
        d_mm_check = d_eff * 1000 if not is_imperial else d_eff * 12 * 25.4
        lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_mm_check)))
    else:
        lambda_s = 1.0

    bo = 2 * ((cx + d_eff) + (cy + d_eff))
    Area_bo = (cx + d_eff) * (cy + d_eff)
    Vu_punch = qu_factored * (footing_area - Area_bo)

    cantilever_max = max((B / 2.0) - (cx / 2.0) + ex_input, (B / 2.0) - (cx / 2.0) - ex_input)
    crit_dist = cantilever_max - d_eff
    Vu_oneway = qu_factored * L * max(0.0, crit_dist)

    phi_s = 0.75
    if not is_imperial:
        vc_punch = 0.33 * lambda_s * np.sqrt(fc)
        vc_oneway = 0.17 * lambda_s * np.sqrt(fc)
        force_mult = 1.0 / 9.81 if is_ton else 1.0
        Phi_Vc_punch = ((phi_s * vc_punch * (bo * 1000) * (d_eff * 1000)) / 1000.0) * force_mult
        Phi_Vc_oneway = ((phi_s * vc_oneway * (L * 1000) * (d_eff * 1000)) / 1000.0) * force_mult
    else:
        vc_punch = 4.0 * lambda_s * np.sqrt(fc)
        vc_oneway = 2.0 * lambda_s * np.sqrt(fc)
        force_mult = 0.5 if is_ton else 1.0
        Phi_Vc_punch = ((phi_s * vc_punch * (bo * 12) * (d_eff * 12)) / 1000.0) * force_mult
        Phi_Vc_oneway = ((phi_s * vc_oneway * (L * 12) * (d_eff * 12)) / 1000.0) * force_mult

    Mu = (qu_factored * L * (cantilever_max**2)) / 2

    if not is_imperial:
        L_mm, d_mm = L * 1000, d_eff * 1000
        Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
        Rn = Mu_Nmm / (0.9 * L_mm * (d_mm**2))
        rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
        rho_req = max(rho, 0.0018)
        As_req_mm2 = rho_req * L_mm * d_mm
    else:
        L_in, d_in = L * 12, d_eff * 12
        Mu_inlbs = Mu * 12000 * (2.0 if is_ton else 1.0)
        Rn = Mu_inlbs / (0.9 * L_in * (d_in**2))
        rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
        rho_req = max(rho, 0.0018)
        As_req_mm2 = (rho_req * L_in * d_in) * 645.16

    if is_selected_metric:
        As_req_disp = As_req_mm2
        area_unit = "mm²"
        spacing_unit = "mm"
        total_len = L * 1000 if not is_imperial else L * 304.8
        clear_cov = 75.0
    else:
        As_req_disp = As_req_mm2 / 645.16
        area_unit = "in²"
        spacing_unit = "in"
        total_len = L * 12 if is_imperial else (L * 1000) / 25.4
        clear_cov = 3.0

    num_bars = int(np.ceil(As_req_disp / actual_area))
    num_bars = max(2, num_bars)
    spacing = round((total_len - (2 * clear_cov)) / max(1, (num_bars - 1)), 1)

    # --- ENHANCED DETAILED PDF GENERATOR ---
    def generate_pdf_report(plot1, plot2):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, spaceAfter=10, textColor=colors.HexColor('#1E3A8A'))
        sec_heading = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=12, spaceBefore=8, spaceAfter=6, textColor=colors.HexColor('#0F172A'))
        subsec_heading = ParagraphStyle('SubSecHeading', parent=styles['Heading3'], fontSize=10, spaceBefore=4, spaceAfter=4, textColor=colors.HexColor('#1E40AF'))
        normal_p = ParagraphStyle('NormalP', parent=styles['Normal'], fontSize=8.5, leading=11, spaceAfter=4)
        code_p = ParagraphStyle('CodeP', parent=styles['Normal'], fontSize=8, leading=10, fontName='Courier', spaceAfter=3, textColor=colors.HexColor('#334155'))

        story = []

        story.append(Paragraph("<b>STRUCTURAL & GEOTECHNICAL FOOTING DESIGN CALCULATION REPORT</b>", title_style))
        story.append(Paragraph(f"Code Standard: <b>{aci_version}</b> | Unit System: <b>{unit_system}</b>", normal_p))
        story.append(Spacer(1, 6))

        # 1. Loading & Eccentricity Steps
        story.append(Paragraph("1. Column Loads & Eccentricity Calculations", sec_heading))
        story.append(Paragraph(f"• Axial Load (P) = <b>{P_unfactored:.2f} {u_force}</b> | Mx = <b>{Mx_unfactored:.2f} {u_moment}</b> | My = <b>{My_unfactored:.2f} {u_moment}</b>", normal_p))
        story.append(Paragraph(f"• Applied Column Eccentricity: e<sub>x,input</sub> = {ex_input:.2f} {u_len}, e<sub>y,input</sub> = {ey_input:.2f} {u_len}", normal_p))
        story.append(Paragraph("<b>Step-by-step Eccentricity Derivation:</b>", subsec_heading))
        story.append(Paragraph(f"  M<sub>x,total</sub> = M<sub>x</sub> + (P × |e<sub>y</sub>|) = {Mx_unfactored:.2f} + ({P_unfactored:.2f} × {abs(ey_input):.2f}) = <b>{Mx_total:.2f} {u_moment}</b>", code_p))
        story.append(Paragraph(f"  M<sub>y,total</sub> = M<sub>y</sub> + (P × |e<sub>x</sub>|) = {My_unfactored:.2f} + ({P_unfactored:.2f} × {abs(ex_input):.2f}) = <b>{My_total:.2f} {u_moment}</b>", code_p))
        story.append(Paragraph(f"  e<sub>x,total</sub> = M<sub>y,total</sub> / P = {My_total:.2f} / {P_unfactored:.2f} = <b>{e_x_total:.4f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  e<sub>y,total</sub> = M<sub>x,total</sub> / P = {Mx_total:.2f} / {P_unfactored:.2f} = <b>{e_y_total:.4f} {u_len}</b>", code_p))

        # 2. Geotechnical
        story.append(Spacer(1, 4))
        story.append(Paragraph("2. Geotechnical Bearing Capacity (Multi-Layer Engine)", sec_heading))
        story.append(Paragraph(f"• Footing Dimensions: B = {B:.2f} {u_len}, L = {L:.2f} {u_len}, D<sub>f</sub> = {Df:.2f} {u_len}", normal_p))
        story.append(Paragraph("<b>Step-by-step Effective Dimensions & Surcharge:</b>", subsec_heading))
        story.append(Paragraph(f"  B<sub>eff</sub> = B - 2(e<sub>x,total</sub>) = {B:.2f} - 2({e_x_total:.4f}) = <b>{B_eff:.3f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  L<sub>eff</sub> = L - 2(e<sub>y,total</sub>) = {L:.2f} - 2({e_y_total:.4f}) = <b>{L_eff:.3f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  Effective Soil Surcharge q<sub>surcharge</sub> = Σ (γ<sub>i</sub> × h<sub>i</sub>) = <b>{q_surcharge:.2f} {u_stress}</b>", code_p))

        if "c-phi" in geo_input_mode:
            story.append(Paragraph("<b>Terzaghi / Meyerhof Analytical Equations:</b>", subsec_heading))
            story.append(Paragraph(f"  N<sub>c</sub> = {Nc:.2f}, N<sub>q</sub> = {Nq:.2f}, N<sub>γ</sub> = {Ng:.2f} (Bearing Layer φ = {target_layer['phi']}°)", code_p))
            story.append(Paragraph(f"  q<sub>ult</sub> = (c × N<sub>c</sub>) + (q<sub>surcharge</sub> × N<sub>q</sub>) + (0.5 × γ<sub>eff</sub> × B<sub>eff</sub> × N<sub>γ</sub>)", code_p))
            story.append(Paragraph(f"  q<sub>ult</sub> = ({target_layer['c']} × {Nc:.2f}) + ({q_surcharge:.2f} × {Nq:.2f}) + (0.5 × {target_layer['gamma']} × {B_eff:.2f} × {Ng:.2f}) = <b>{q_ult:.2f} {u_stress}</b>", code_p))
        else:
            story.append(Paragraph("<b>Meyerhof / Bowles Empirical SPT N Method:</b>", subsec_heading))
            story.append(Paragraph(f"  K<sub>d</sub> = min(1.33, 1 + 0.33 × D<sub>f</sub>/B<sub>eff</sub>) = <b>{min(1.33, 1 + 0.33*(Df/B_eff)):.3f}</b>", code_p))
            story.append(Paragraph(f"  q<sub>ult</sub> = q<sub>allow</sub> × FS = <b>{q_ult:.2f} {u_stress}</b>", code_p))

        story.append(Paragraph(f"  q<sub>allow</sub> = q<sub>ult</sub> / FS = {q_ult:.2f} / {FS} = <b>{q_allow:.2f} {u_stress}</b>", code_p))
        story.append(Paragraph(f"  q<sub>max,service</sub> = P/A + 6M<sub>x</sub>/(BL²) + 6M<sub>y</sub>/(LB²) = <b>{q_max_service:.2f} {u_stress}</b> {'[PASS]' if q_max_service <= q_allow else '[OVERLOADED]'}", code_p))

        # 3. Structural Shear Calculations
        story.append(Spacer(1, 4))
        story.append(Paragraph("3. Structural Shear Verification (ACI 318)", sec_heading))
        story.append(Paragraph(f"• Factored Load P<sub>u</sub> = 1.4 × P = 1.4 × {P_unfactored:.2f} = <b>{Pu:.2f} {u_force}</b>", normal_p))
        story.append(Paragraph(f"• Factored Ultimate Pressure q<sub>u</sub> = P<sub>u</sub>/A + 6M<sub>ux</sub>/(BL²) = <b>{qu_factored:.2f} {u_stress}</b>", normal_p))
        story.append(Paragraph(f"• Effective Depth d<sub>eff</sub> = h - cover = {h_foot:.3f} - {cover:.3f} = <b>{d_eff:.3f} {u_len}</b> | Size Effect λ<sub>s</sub> = <b>{lambda_s:.3f}</b>", normal_p))

        story.append(Paragraph("<b>3.1 Two-Way Punching Shear Calculation:</b>", subsec_heading))
        story.append(Paragraph(f"  Critical Perimeter b<sub>o</sub> = 2 × [(c<sub>x</sub> + d) + (c<sub>y</sub> + d)] = 2 × [({cx:.2f}+{d_eff:.3f}) + ({cy:.2f}+{d_eff:.3f})] = <b>{bo:.3f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  Punching Area A<sub>bo</sub> = (c<sub>x</sub> + d)(c<sub>y</sub> + d) = <b>{Area_bo:.3f} {u_len}²</b>", code_p))
        story.append(Paragraph(f"  V<sub>u,punch</sub> = q<sub>u</sub> × (B × L - A<sub>bo</sub>) = {qu_factored:.2f} × ({B:.2f}×{L:.2f} - {Area_bo:.3f}) = <b>{Vu_punch:.2f} {u_force}</b>", code_p))
        story.append(Paragraph(f"  v<sub>c,punch</sub> = 0.33 × λ<sub>s</sub> × √(f'c) = 0.33 × {lambda_s:.3f} × √({fc}) = {vc_punch:.3f} MPa", code_p))
        story.append(Paragraph(f"  φV<sub>c,punch</sub> = φ × v<sub>c</sub> × b<sub>o</sub> × d = <b>{Phi_Vc_punch:.2f} {u_force}</b> {'[PASS]' if Phi_Vc_punch >= Vu_punch else '[FAIL]'}", code_p))

        story.append(Paragraph("<b>3.2 One-Way Beam Shear Calculation:</b>", subsec_heading))
        story.append(Paragraph(f"  Max Cantilever Arm = (B/2 - c<sub>x</sub>/2 + e<sub>x</sub>) = <b>{cantilever_max:.3f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  Critical Shear Distance = Cantilever - d = {cantilever_max:.3f} - {d_eff:.3f} = <b>{crit_dist:.3f} {u_len}</b>", code_p))
        story.append(Paragraph(f"  V<sub>u,oneway</sub> = q<sub>u</sub> × L × Critical Distance = {qu_factored:.2f} × {L:.2f} × {max(0.0, crit_dist):.3f} = <b>{Vu_oneway:.2f} {u_force}</b>", code_p))
        story.append(Paragraph(f"  φV<sub>c,oneway</sub> = φ × (0.17 × λ<sub>s</sub> × √(f'c)) × L × d = <b>{Phi_Vc_oneway:.2f} {u_force}</b> {'[PASS]' if Phi_Vc_oneway >= Vu_oneway else '[FAIL]'}", code_p))

        # 4. Flexural Design
        story.append(Spacer(1, 4))
        story.append(Paragraph("4. Flexural Reinforcement Design", sec_heading))
        story.append(Paragraph(f"  M<sub>u</sub> = (q<sub>u</sub> × L × Cantilever²) / 2 = ({qu_factored:.2f} × {L:.2f} × {cantilever_max:.3f}²) / 2 = <b>{Mu:.2f} {u_moment}</b>", code_p))
        story.append(Paragraph(f"  Nominal Resistance Factor R<sub>n</sub> = M<sub>u</sub> / (φ × b × d²) = <b>{Rn:.4f} N/mm²</b>", code_p))
        story.append(Paragraph(f"  Calculated Steel Ratio ρ = (0.85 × f'c / f<sub>y</sub>) × [1 - √(1 - 2R<sub>n</sub> / (0.85 × f'c))] = <b>{rho:.6f}</b>", code_p))
        story.append(Paragraph(f"  Required Steel Ratio ρ<sub>req</sub> = max(ρ, ρ<sub>min</sub> = 0.0018) = <b>{rho_req:.6f}</b>", code_p))
        story.append(Paragraph(f"  Required Steel Area A<sub>s,req</sub> = ρ<sub>req</sub> × L × d = <b>{As_req_disp:.2f} {area_unit}</b>", code_p))
        story.append(Paragraph(f"  Selected Bar: <b>{selected_rebar}</b> (Effective Area = {actual_area:.2f} {area_unit} with {bar_tolerance_pct}% tolerance)", code_p))
        story.append(Paragraph(f"  Bar Count Calculation: N = ceil(A<sub>s,req</sub> / A<sub>bar</sub>) = ceil({As_req_disp:.2f} / {actual_area:.2f}) = <b>{num_bars} Bars</b>", code_p))
        story.append(Paragraph(f"  Spacing Calculation: s = (L - 2×Cover) / (N - 1) = <b>{spacing} {spacing_unit} c/c</b>", code_p))
        story.append(Paragraph(f"<b>FINAL SPECIFICATION: Provide {num_bars} Nos - {selected_rebar} @ {spacing} {spacing_unit} c/c (Both Ways)</b>", subsec_heading))

        # 5. Drawings
        story.append(Spacer(1, 8))
        story.append(Paragraph("5. Structural Detailing Drawings", sec_heading))
        img_table = Table([
            [RLImage(plot1, width=250, height=170), RLImage(plot2, width=250, height=170)]
        ], colWidths=[260, 260])
        img_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(img_table)

        doc.build(story)
        buf.seek(0)
        return buf

    # --- Drawing Logic ---
    def draw_cross_section():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        y_top = 0.0
        colors_list = ["#E5D3B3", "#D2B48C", "#C4A484", "#B8860B", "#A0522D"]

        for idx, layer in enumerate(soil_layers):
            y_bottom = y_top - layer["thickness"]
            ax.fill_between([-B / 2 - 1.2, B / 2 + 1.2], [y_top, y_top], [y_bottom, y_bottom], color=colors_list[idx % 5], alpha=0.5)
            y_top = y_bottom

        ax.plot([-B / 2 - 1.2, B / 2 + 1.2], [0, 0], "k--", linewidth=1, label="Ground Level")
        f_bottom = -Df - h_foot
        ax.add_patch(plt.Rectangle((-B / 2, f_bottom), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5, label="Footing"))
        
        col_x_start = ex_input - (cx / 2.0)
        ax.add_patch(plt.Rectangle((col_x_start, -Df), cx, Df + 0.3, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Column"))

        ax.axvline(0, color="gray", linestyle=":", linewidth=1.0)
        rebar_y_xdir = f_bottom + cover
        
        ax.plot([-B / 2 + cover, B / 2 - cover], [rebar_y_xdir, rebar_y_xdir], color="red", linewidth=2.0, label=f"X-Bar: {num_bars}-{selected_rebar}")
        x_coords = np.linspace(-B / 2 + cover, B / 2 - cover, num_bars)
        ax.scatter(x_coords, [rebar_y_xdir + 0.02] * num_bars, color="darkblue", s=15, zorder=5, label=f"Y-Bar: {num_bars}-{selected_rebar}")

        dim_y = f_bottom - 0.25
        ax.annotate("", xy=(-B / 2, dim_y), xytext=(B / 2, dim_y), arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
        ax.text(0, dim_y - 0.12, f"B = {B:.2f} {u_len}", ha="center", va="top", fontsize=8, fontweight="bold")
        
        ax.set_xlim(-B / 2 - 1.0, B / 2 + 1.0)
        ax.set_ylim(f_bottom - 0.7, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.legend(loc="upper right", bbox_to_anchor=(1.38, 1.0), fontsize=6.5)
        plt.title("Footing Elevation Section View", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    def draw_plan_view():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.add_patch(patches.Rectangle((-B / 2, -L / 2), B, L, facecolor="#D1D5DB", edgecolor="black", linewidth=1.5))
        
        col_x_min = ex_input - (cx / 2.0)
        col_y_min = ey_input - (cy / 2.0)
        ax.add_patch(patches.Rectangle((col_x_min, col_y_min), cx, cy, facecolor="#374151", edgecolor="black", linewidth=1.5))

        x_rebar_coords = np.linspace(-B / 2 + cover, B / 2 - cover, num_bars)
        y_rebar_coords = np.linspace(-L / 2 + cover, L / 2 - cover, num_bars)

        for xc in x_rebar_coords:
            ax.plot([xc, xc], [-L / 2 + cover, L / 2 - cover], color="darkblue", linewidth=1.0, alpha=0.7)
        for yc in y_rebar_coords:
            ax.plot([-B / 2 + cover, B / 2 - cover], [yc, yc], color="red", linewidth=1.0, alpha=0.7)

        ax.annotate("", xy=(col_x_min, col_y_min + cy + 0.15), xytext=(col_x_min + cx, col_y_min + cy + 0.15), arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
        ax.text(ex_input, col_y_min + cy + 0.22, f"cx={cx:.2f}{u_len}", ha="center", va="bottom", fontsize=7.5)

        ax.annotate("", xy=(col_x_min + cx + 0.15, col_y_min), xytext=(col_x_min + cx + 0.15, col_y_min + cy), arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
        ax.text(col_x_min + cx + 0.22, ey_input, f"cy={cy:.2f}{u_len}", ha="left", va="center", fontsize=7.5, rotation=270)

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(-L / 2 - 0.8, L / 2 + 0.8)
        ax.set_aspect("equal")
        ax.axis("off")
        plt.title("Footing Structural Top Plan View", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    # --- Render Output ---
    sec_img_buf = draw_cross_section()
    plan_img_buf = draw_plan_view()

    with col_res:
        st.header("📊 Results & Verification Summary")
        
        # UI Metrics
        st.subheader("1. Eccentricity & Soil Pressure")
        e1, e2 = st.columns(2)
        e1.metric(f"Total ex", f"{e_x_total:.3f} {u_len}")
        e2.metric(f"Max Pressure (q_max)", f"{q_max_service:.2f} {u_stress}", delta="✅ OK" if q_max_service <= q_allow else "❌ OVERLOADED")
        
        st.subheader("2. Structural Shears Check")
        s1, s2 = st.columns(2)
        s1.metric("Punching Shear", f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}", delta="✅ PASS" if Phi_Vc_punch >= Vu_punch else "❌ FAIL")
        s2.metric("One-Way Shear", f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}", delta="✅ PASS" if Phi_Vc_oneway >= Vu_oneway else "❌ FAIL")

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(f"**Design Recommendation:** Provide **{num_bars} Nos - {selected_rebar}** bars @ **{spacing} {spacing_unit} c/c** (Both Directions)")

        st.image(sec_img_buf, caption="Cross-Section Elevation with Rebar Counts")
        st.image(plan_img_buf, caption="Footing Plan Top View with Column Dimensions")

        # --- PDF Download Button ---
        st.markdown("---")
        pdf_buffer = generate_pdf_report(sec_img_buf, plan_img_buf)
        st.download_button(
            label="📄 Download Detailed Calculation Report (PDF)",
            data=pdf_buffer.getvalue(),
            file_name="Detailed_Footing_Design_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
