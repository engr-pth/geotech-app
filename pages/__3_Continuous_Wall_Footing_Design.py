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
)

# --- Page Config ---
st.set_page_config(
    page_title="Continuous Wall Footing Design Suite", page_icon="🧱", layout="wide"
)
st.title("🧱 Continuous RC Wall Footing Design Suite")

col_in, col_res = st.columns([1.1, 1.1])

with col_in:
    # --- Section 1: Single Footing Style ---
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

    u_len = "ft" if is_imperial else "m"
    u_force_per_len = "kips/ft" if (is_imperial and not is_ton) else ("ton/ft" if is_imperial and is_ton else ("ton/m" if is_ton else "kN/m"))
    u_stress = "tsf" if (is_imperial and is_ton) else ("ksf" if is_imperial else ("t/m²" if is_ton else "kPa"))
    u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
    u_rebar = "in" if is_imperial else "mm"
    u_fc = "psi" if is_imperial else "MPa"

    geo_mode = st.radio(
        "Geotechnical Input Option",
        [
            "Direct Gross Allowable Soil Capacity (q_allow)",
            "c-phi Parameters (Analytical - Terzaghi/Meyerhof)",
            "SPT N-value (Empirical Method)",
        ],
    )

    # --- Section 2: Loading Inputs ---
    st.header("2. Applied Line Loads")
    col_p1, col_p2 = st.columns(2)
    P_dl = col_p1.number_input(f"Dead Load P_DL ({u_force_per_len})", 0.0, 5000.0, 100.0 if not is_imperial else 8.0)
    P_ll = col_p2.number_input(f"Live Load P_LL ({u_force_per_len})", 0.0, 5000.0, 50.0 if not is_imperial else 4.0)

    # --- Section 3: Geotechnical Parameters ---
    st.header("3. Geotechnical Soil Parameters Mode")
    if "Direct" in geo_mode:
        q_allow_input = st.number_input(f"Gross Allowable Soil Cap. q_allow ({u_stress})", 1.0, 10000.0, 150.0 if not is_imperial else 3.0)
        c_val, phi_val, n_spt, FS = 0.0, 0.0, 0, 3.0
    elif "c-phi" in geo_mode:
        col_c1, col_c2 = st.columns(2)
        c_val = col_c1.number_input(f"Cohesion c ({u_stress})", 0.0, 5000.0, 10.0 if not is_imperial else 0.2)
        phi_val = col_c2.number_input("Friction Angle φ (deg)", 0.0, 45.0, 28.0)
        n_spt, q_allow_input = 0, None
        FS = st.number_input("Safety Factor (FS)", 1.0, 10.0, 3.0)
    else:
        n_spt = st.number_input("SPT N-Value", 1, 100, 15)
        c_val, phi_val, q_allow_input = 0.0, 0.0, None
        FS = st.number_input("Safety Factor (FS)", 1.0, 10.0, 3.0)

    # --- Section 4: Geometry ---
    st.header("4. Geometry Settings (Footing & Wall)")
    col_g1, col_g2 = st.columns(2)
    b_wall = col_g1.number_input(f"Wall Thickness b_w ({u_len})", 0.1, 5.0, 0.25 if not is_imperial else 0.833)
    B = col_g2.number_input(f"Footing Width B ({u_len})", 0.5, 30.0, 1.8 if not is_imperial else 6.0)

    col_g3, col_g4 = st.columns(2)
    h_foot = col_g3.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 0.40 if not is_imperial else 1.25)
    Df = col_g4.number_input(f"Embedment Depth Df ({u_len})", 0.0, 20.0, 1.2 if not is_imperial else 4.0)

    col_s1, col_s2 = st.columns(2)
    gamma_soil = col_s1.number_input(f"Soil γ ({u_gamma})", 0.0, 300.0, 18.0 if not is_imperial else 115.0)
    Dw = col_s2.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 1.0 if not is_imperial else 3.5)

    # --- Section 5: Structural & Rebar Details ---
    st.header("5. Structural & Rebar Details")
    aci_version = st.selectbox("ACI Standard Code", ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"])
    col_m1, col_m2 = st.columns(2)
    fc = col_m1.number_input(f"Concrete f'c ({u_fc})", 10.0, 10000.0, 28.0 if not is_imperial else 4000.0)
    fy = col_m2.number_input(f"Steel fy ({u_fc})", 100.0, 100000.0, 420.0 if not is_imperial else 60000.0)

    rebar_system = st.radio("Rebar Unit System Standard", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"])
    if "Metric" in rebar_system:
        main_rebar_opts = {
            "16 mm": {"dia": 16.0, "area": 201.1},
            "18 mm": {"dia": 18.0, "area": 254.5},
            "20 mm": {"dia": 20.0, "area": 314.2},
            "22 mm": {"dia": 22.0, "area": 380.1},
            "25 mm": {"dia": 25.0, "area": 490.9},
        }
        temp_rebar_opts = {
            "10 mm": {"dia": 10.0, "area": 78.5},
            "12 mm": {"dia": 113.1, "area": 113.1},
            "16 mm": {"dia": 16.0, "area": 201.1},
            "18 mm": {"dia": 18.0, "area": 254.5},
            "20 mm": {"dia": 20.0, "area": 314.2},
            "22 mm": {"dia": 22.0, "area": 380.1},
            "25 mm": {"dia": 25.0, "area": 490.9},
        }
    else:
        main_rebar_opts = {
            "#5 (0.625 in)": {"dia": 0.625, "area": 0.31},
            "#6 (0.750 in)": {"dia": 0.750, "area": 0.44},
            "#7 (0.875 in)": {"dia": 0.875, "area": 0.60},
            "#8 (1.000 in)": {"dia": 1.000, "area": 0.79},
        }
        temp_rebar_opts = {
            "#3 (0.375 in)": {"dia": 0.375, "area": 0.11},
            "#4 (0.500 in)": {"dia": 0.500, "area": 0.20},
            "#5 (0.625 in)": {"dia": 0.625, "area": 0.31},
            "#6 (0.750 in)": {"dia": 0.750, "area": 0.44},
        }

    col_r1, col_r2 = st.columns(2)
    selected_main_bar = col_r1.selectbox("Main Rebar (Transverse)", list(main_rebar_opts.keys()))
    selected_temp_bar = col_r2.selectbox("Temperature & Shrinkage Rebar", list(temp_rebar_opts.keys()))

    hook_type = st.radio("Rebar End Hook Type", ["None (Straight Bar)", "90-Degree Standard Hook", "180-Degree Standard Hook"])

    calc_trigger = st.button("🚀 Calculate Continuous Wall Footing", type="primary", use_container_width=True)

# --- Calculation Engine ---
if calc_trigger or "wall_calc_state" in st.session_state:
    st.session_state["wall_calc_state"] = True

    gamma_w = 62.4 if is_imperial else (1.0 if is_ton else 9.81)
    gamma_conc = 150.0 if is_imperial else (2.4 if is_ton else 24.0)
    unit_div = (1000.0 if not is_ton else 2000.0) if is_imperial else 1.0

    # Soil Surcharge Calculation
    if Dw >= Df + h_foot:
        surcharge = ((Df * gamma_soil) + (h_foot * gamma_conc)) / unit_div
    else:
        d_dry = min(Df, Dw)
        d_sat = Df - d_dry
        surcharge = ((d_dry * gamma_soil) + (d_sat * (gamma_soil - gamma_w)) + (h_foot * (gamma_conc - gamma_w))) / unit_div

    # Geotechnical Bearing Capacity Determination
    if "Direct" in geo_mode:
        q_allow = q_allow_input
    elif "c-phi" in geo_mode:
        rad_phi = np.radians(phi_val)
        if phi_val > 0:
            Nq = np.exp(np.pi * np.tan(rad_phi)) * (np.tan(np.radians(45 + phi_val / 2))) ** 2
            Nc = (Nq - 1) / np.tan(rad_phi)
            Ng = 2 * (Nq + 1) * np.tan(rad_phi)
        else:
            Nc, Nq, Ng = 5.14, 1.0, 0.0
        q_ult = (c_val * Nc) + (surcharge * Nq) + (0.5 * gamma_soil * B * Ng)
        q_allow = q_ult / FS
    else:
        Kd = min(1.33, 1 + 0.33 * (Df / B))
        if is_imperial:
            q_allow = (n_spt / 4.0) * (1.0 if is_ton else 2.0) * Kd
        else:
            q_allow = (n_spt * 1.2 if is_ton else n_spt / 0.05) * Kd

    q_net_allow = max(0.001, q_allow - surcharge)
    P_service = P_dl + P_ll
    q_service_actual = P_service / B

    Pu = (1.2 * P_dl) + (1.6 * P_ll)
    qu_factored = Pu / B

    cover = (3.0 / 12.0) if is_imperial else 0.075
    d_eff = h_foot - cover

    cantilever_arm = (B - b_wall) / 2.0
    crit_shear_dist = cantilever_arm - d_eff
    Vu_oneway = qu_factored * max(0.0, crit_shear_dist)

    lambda_s = min(1.0, np.sqrt(2.0 / (1.0 + 0.004 * (d_eff * (1000.0 if not is_imperial else 304.8))))) if aci_version in ["ACI 318-19", "ACI 318-22"] else 1.0

    phi_shear = 0.75
    if not is_imperial:
        vc = 0.17 * lambda_s * np.sqrt(fc)
        Phi_Vc = (phi_shear * vc * 1000.0 * (d_eff * 1000.0) / 1000.0) * (1.0 / 9.81 if is_ton else 1.0)
    else:
        vc = 2.0 * lambda_s * np.sqrt(fc)
        Phi_Vc = (phi_shear * vc * 12.0 * (d_eff * 12.0) / 1000.0) * (0.5 if is_ton else 1.0)

    Mu = (qu_factored * (cantilever_arm**2)) / 2.0

    if not is_imperial:
        b_mm, d_mm_val = 1000.0, d_eff * 1000.0
        h_mm_val = h_foot * 1000.0
        Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
        Rn = Mu_Nmm / (0.9 * b_mm * (d_mm_val**2))
        rho_calc = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc))))
        
        rho_min = 0.0018
        rho_req = max(rho_calc, rho_min)
        
        main_bar_area = main_rebar_opts[selected_main_bar]["area"] if "Metric" in rebar_system else main_rebar_opts[selected_main_bar]["area"] * 645.16
        temp_bar_area = temp_rebar_opts[selected_temp_bar]["area"] if "Metric" in rebar_system else temp_rebar_opts[selected_temp_bar]["area"] * 645.16

        As_main_req = rho_req * b_mm * d_mm_val
        As_temp_req = 0.0018 * b_mm * h_mm_val
        spacing_unit = "mm"
    else:
        b_in, d_in_val = 12.0, d_eff * 12.0
        h_in_val = h_foot * 12.0
        Mu_inlbs = Mu * 12000.0 * (2.0 if is_ton else 1.0)
        Rn = Mu_inlbs / (0.9 * b_in * (d_in_val**2))
        rho_calc = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc))))
        
        rho_min = 0.0018
        rho_req = max(rho_calc, rho_min)
        
        main_bar_area = main_rebar_opts[selected_main_bar]["area"] if "Imperial" in rebar_system else main_rebar_opts[selected_main_bar]["area"] / 645.16
        temp_bar_area = temp_rebar_opts[selected_temp_bar]["area"] if "Imperial" in rebar_system else temp_rebar_opts[selected_temp_bar]["area"] / 645.16

        As_main_req = rho_req * b_in * d_in_val
        As_temp_req = 0.0018 * b_in * h_in_val
        spacing_unit = "in"

    s_main = (main_bar_area / As_main_req) * (1000.0 if not is_imperial else 12.0)
    s_temp = (temp_bar_area / As_temp_req) * (1000.0 if not is_imperial else 12.0)

    max_s_temp = min(5 * h_foot * (1000.0 if not is_imperial else 12.0), 450.0 if not is_imperial else 18.0)

    s_main_final = int(min(s_main, min(3 * h_foot * (1000.0 if not is_imperial else 12.0), 450.0 if not is_imperial else 18.0)))
    s_temp_final = int(min(s_temp, max_s_temp))

    raw_db = main_rebar_opts[selected_main_bar]["dia"]
    if is_imperial:
        db_calc = raw_db if "Imperial" in rebar_system else (raw_db / 25.4)
    else:
        db_calc = raw_db if "Metric" in rebar_system else (raw_db * 25.4)

    L_avail_val = cantilever_arm - cover

    if not is_imperial:
        L_avail_disp = L_avail_val * 1000.0
        ld_straight = (fy / (1.1 * np.sqrt(fc))) * db_calc
        ld_hook = (0.24 * fy / np.sqrt(fc)) * db_calc
        u_ld = "mm"
    else:
        L_avail_disp = L_avail_val * 12.0
        ld_straight = (fy / (25.0 * np.sqrt(fc))) * db_calc
        ld_hook = (0.02 * fy / np.sqrt(fc)) * db_calc
        u_ld = "in"

    ld_req = ld_hook if "Hook" in hook_type else ld_straight
    ld_status = L_avail_disp >= ld_req

    def draw_footing_section():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        f_top, f_bottom = -Df, -Df - h_foot

        ax.fill_between([-B / 2 - 1.0, B / 2 + 1.0], [0, 0], [f_bottom - 0.4, f_bottom - 0.4], color="#E5D3B3", alpha=0.5)
        ax.plot([-B / 2 - 1.0, B / 2 + 1.0], [0, 0], "k--", linewidth=1, label="Ground Level (GL)")
        
        footing_rect = patches.Rectangle((-B / 2, f_bottom), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5, label="Footing")
        wall_rect = patches.Rectangle((-b_wall / 2, f_top), b_wall, Df + 0.4, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="RC Wall")
        
        ax.add_patch(footing_rect)
        ax.add_patch(wall_rect)

        main_y = f_bottom + cover
        left_x, right_x = -B / 2 + cover, B / 2 - cover
        
        ax.plot([left_x, right_x], [main_y, main_y], color="red", linewidth=2.0, label=f"Main Bar: {selected_main_bar}")

        if "90-Degree" in hook_type:
            hook_len = 0.1 if not is_imperial else 0.3
            ax.plot([left_x, left_x], [main_y, main_y + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x, right_x], [main_y, main_y + hook_len], color="red", linewidth=2.0)

        elif "180-Degree" in hook_type:
            r_hook = 0.04 if not is_imperial else 0.12
            tail_len = 0.05 if not is_imperial else 0.15

            theta_left = np.linspace(1.5 * np.pi, 0.5 * np.pi, 30)
            x_arc_left = left_x + r_hook * np.cos(theta_left)
            y_arc_left = (main_y + r_hook) + r_hook * np.sin(theta_left)

            ax.plot(x_arc_left, y_arc_left, color="red", linewidth=2.0)
            ax.plot([left_x, left_x + tail_len], 
                    [main_y + 2 * r_hook, main_y + 2 * r_hook], color="red", linewidth=2.0)

            theta_right = np.linspace(1.5 * np.pi, 0.5 * np.pi, 30)
            x_arc_right = right_x - r_hook * np.cos(theta_right)
            y_arc_right = (main_y + r_hook) + r_hook * np.sin(theta_right)

            ax.plot(x_arc_right, y_arc_right, color="red", linewidth=2.0)
            ax.plot([right_x, right_x - tail_len], 
                    [main_y + 2 * r_hook, main_y + 2 * r_hook], color="red", linewidth=2.0)

        dot_x_coords = np.linspace(left_x + 0.08, right_x - 0.08, 7)
        ax.scatter(dot_x_coords, [main_y + 0.03] * 7, color="darkblue", s=25, zorder=5, label=f"Temp/Shrinkage Bar: {selected_temp_bar}")

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(f_bottom - 0.6, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        
        ax.legend(loc="upper right", fontsize=6.0)
        plt.title(f"Footing Elevation Section ({hook_type})", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    def draw_footing_plan():
        fig, ax = plt.subplots(figsize=(6.5, 6.5))
        unit_len_display = 2.0 if not is_imperial else 6.0
        
        foot_plan = patches.Rectangle((-B / 2, -unit_len_display / 2), B, unit_len_display, facecolor="#E5E7EB", edgecolor="#1F2937", linewidth=2, label="Footing Plan")
        wall_plan = patches.Rectangle((-b_wall / 2, -unit_len_display / 2), b_wall, unit_len_display, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Wall Above")
        
        ax.add_patch(foot_plan)
        ax.add_patch(wall_plan)

        y_lines = np.linspace(-unit_len_display / 2 + 0.1, unit_len_display / 2 - 0.1, 8)
        for idx, y_pos in enumerate(y_lines):
            ax.plot([-B / 2 + cover, B / 2 - cover], [y_pos, y_pos], color="red", linewidth=1.5, label="Transverse Rebar" if idx == 0 else "")

        x_lines = np.linspace(-B / 2 + cover + 0.05, B / 2 - cover - 0.05, 7)
        for idx, x_pos in enumerate(x_lines):
            ax.plot([x_pos, x_pos], [-unit_len_display / 2 + 0.05, unit_len_display / 2 - 0.05], color="darkblue", linestyle="--", linewidth=1.2, label="Longitudinal Rebar" if idx == 0 else "")

        ax.set_xlim(-B / 2 - 0.5, B / 2 + 0.5)
        ax.set_ylim(-unit_len_display / 2 - 0.4, unit_len_display / 2 + 0.4)
        ax.set_aspect("equal")
        ax.axis("off")
        
        cover_val_disp = cover * (12.0 if is_imperial else 1000.0)
        plt.title(f"Footing Structural Top Plan View (Cover = {cover_val_disp:.1f} {u_rebar})", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    def generate_pdf_report(sec_buf, plan_buf):
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()

        main_title_style = ParagraphStyle(
            'MainTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor("#1A365D"), spaceAfter=6
        )
        sub_title_style = ParagraphStyle(
            'SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#2D3748"), spaceAfter=10
        )
        h1_sec_style = ParagraphStyle(
            'H1Sec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor("#000000"), spaceBefore=8, spaceAfter=4
        )
        bullet_style = ParagraphStyle(
            'BulletText', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#1A202C")
        )
        math_code_style = ParagraphStyle(
            'MathCode', parent=styles['Normal'], fontName='Courier', fontSize=8.0, leading=11, textColor=colors.HexColor("#2C5282")
        )

        story = []

        story.append(Paragraph("STRUCTURAL & GEOTECHNICAL CONTINUOUS WALL FOOTING DESIGN REPORT", main_title_style))
        story.append(Paragraph(
            f"Code Standard: <b>{aci_version}</b> | Unit System: <b>{unit_system}</b> | Hook Type: <b>{hook_type}</b>",
            sub_title_style
        ))

        story.append(Paragraph("1. Applied Loads & Geometric Parameters", h1_sec_style))
        story.append(Paragraph(f"• Dead Load (P_DL) = {P_dl:.2f} {u_force_per_len} | Live Load (P_LL) = {P_ll:.2f} {u_force_per_len}", bullet_style))
        story.append(Paragraph(f"• Factored Line Load Pu = 1.2({P_dl:.2f}) + 1.6({P_ll:.2f}) = <b>{Pu:.2f} {u_force_per_len}</b>", bullet_style))
        story.append(Paragraph(f"• Footing Width (B) = {B:.2f} {u_len} | Thickness (h) = {h_foot:.2f} {u_len} | Wall Width (b_w) = {b_wall:.2f} {u_len}", bullet_style))

        story.append(Paragraph("2. Geotechnical Bearing Capacity Checks", h1_sec_style))
        story.append(Paragraph(f"• Soil Surcharge Pressure (q_surcharge) = {surcharge:.2f} {u_stress}", bullet_style))
        story.append(Paragraph(f"• Net Allowable Bearing Capacity (q_net_allow) = {q_net_allow:.2f} {u_stress}", bullet_style))
        story.append(Paragraph(f"• Actual Service Soil Pressure q_service = {P_service:.2f} / {B:.2f} = <b>{q_service_actual:.2f} {u_stress}</b>", bullet_style))
        status_geo = "SAFE" if q_service_actual <= q_net_allow else "OVERLOADED"
        story.append(Paragraph(f"• Geotechnical Bearing Status: <b>[{status_geo}]</b>", bullet_style))

        story.append(Paragraph("3. One-Way Shear Verification (ACI 318)", h1_sec_style))
        math_shear = (
            f"Factored Pressure qu = Pu / B = {qu_factored:.2f} {u_stress}<br/>"
            f"Cantilever Arm = (B - b_w) / 2 = {cantilever_arm:.3f} {u_len}<br/>"
            f"Critical Section Distance = Cantilever - d = {max(0.0, crit_shear_dist):.3f} {u_len}<br/>"
            f"Vu,oneway = {Vu_oneway:.2f} {u_force_per_len} | Shear Capacity φVc = {Phi_Vc:.2f} {u_force_per_len}"
        )
        story.append(Paragraph(math_shear, math_code_style))
        status_shear = "PASS" if Phi_Vc >= Vu_oneway else "FAIL"
        story.append(Paragraph(f"• One-Way Shear Status: <b>[{status_shear}]</b>", bullet_style))

        story.append(Paragraph("4. Flexural Reinforcement Derivations", h1_sec_style))
        math_flex = (
            f"Factored Moment Mu = (qu * Cantilever^2) / 2 = {Mu:.2f} {u_force_per_len}*{u_len}<br/>"
            f"Calculated Steel Ratio ρ_calc = {rho_calc:.6f}<br/>"
            f"Minimum Temperature & Shrinkage Ratio ρ_min = {rho_min:.6f}<br/>"
            f"Governing Steel Ratio ρ_req = max(ρ_calc, ρ_min) = {rho_req:.6f}"
        )
        story.append(Paragraph(math_flex, math_code_style))
        story.append(Paragraph(f"• Main Transverse Rebar: <b>{selected_main_bar} @ {s_main_final} {spacing_unit} c/c</b> ({hook_type})", bullet_style))
        story.append(Paragraph(f"• Temperature & Shrinkage Rebar: <b>{selected_temp_bar} @ {s_temp_final} {spacing_unit} c/c</b>", bullet_style))

        story.append(Paragraph("5. Rebar Development Length Verification (ACI 318)", h1_sec_style))
        math_dev = (
            f"Available Anchorage Length (L_avail) = Cantilever - Cover = {L_avail_disp:.1f} {u_ld}<br/>"
            f"Required Development Length (L_d / L_dh) = {ld_req:.1f} {u_ld}"
        )
        story.append(Paragraph(math_dev, math_code_style))
        status_ld_str = "PASS" if ld_status else "FAIL (Hook or Larger Width Required)"
        story.append(Paragraph(f"• Development Length Status: <b>[{status_ld_str}]</b>", bullet_style))

        story.append(Spacer(1, 6))
        story.append(Paragraph("6. Structural Detailing Drawings", h1_sec_style))
        
        img_sec = RLImage(sec_buf, width=240, height=160)
        img_plan = RLImage(plan_buf, width=240, height=160)
        
        img_table = Table([[img_sec, img_plan]], colWidths=[255, 255])
        img_table.setStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ])
        story.append(img_table)

        doc.build(story)
        pdf_buf.seek(0)
        return pdf_buf

    sec_img = draw_footing_section()
    plan_img = draw_footing_plan()
    pdf_file = generate_pdf_report(sec_img, plan_img)

    # --- Section 6: Results Summary Display (Single Footing UI Alignment) ---
    with col_res:
        st.header("📊 Results & Verification Summary")
        
        st.subheader("1. Eccentricity & Soil Pressure")
        st.metric("Total Service P", f"{P_service:.2f} {u_force_per_len} (DL: {P_dl}, LL: {P_ll})")
        st.metric("Actual Service Pressure", f"{q_service_actual:.2f} {u_stress}", delta="✅ SAFE" if q_service_actual <= q_net_allow else "❌ OVERLOADED")

        st.subheader("2. Structural Shears Check")
        st.metric("One-Way Shear (Vu / φVc)", f"{Vu_oneway:.1f} / {Phi_Vc:.1f} {u_force_per_len}", delta="✅ PASS" if Phi_Vc >= Vu_oneway else "❌ FAIL")

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(f"• **Main Steel:** Provide **{selected_main_bar} @ {s_main_final} {spacing_unit} c/c** ({hook_type})")
        st.markdown(f"• **Temp/Shrinkage Steel:** Provide **{selected_temp_bar} @ {s_temp_final} {spacing_unit} c/c**")

        st.subheader("4. Development Length Verification ($L_d$)")
        st.metric(
            f"Available Length vs Req. Length ({u_ld})",
            f"{L_avail_disp:.1f} / {ld_req:.1f} {u_ld}",
            delta="✅ PASS (Adequate Anchorage)" if ld_status else "❌ FAIL (Provide Hook or Increase B)"
        )

        st.subheader("5. Detailing Drawings")
        st.image(sec_img, caption="Footing Elevation Cross-Section Diagram")
        st.image(plan_img, caption="Footing Top Structural Plan View")

        st.markdown("---")
        st.download_button(
            label="📄 Download Detailed Calculation PDF Report",
            data=pdf_file,
            file_name="Continuous_Wall_Footing_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
