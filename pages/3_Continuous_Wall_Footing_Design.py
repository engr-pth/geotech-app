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

# --- Page Config ---
st.set_page_config(
    page_title="Wall Footing Design Suite", page_icon="🧱", layout="wide"
)
st.title("🧱 Continuous RC Wall Footing Design Suite")
st.caption(
    "Design of Strip/Continuous Footing under Wall Load per ACI 318 Standard"
)

col_in, col_res = st.columns([1.1, 1.1])

with col_in:
    st.header("1. Unit System & Loading Inputs")
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

    # Unit Mapping Labels
    u_len = "ft" if is_imperial else "m"
    u_force_per_len = (
        "kips/ft"
        if (is_imperial and not is_ton)
        else ("ton/ft" if is_imperial and is_ton else ("ton/m" if is_ton else "kN/m"))
    )
    u_stress = (
        "tsf"
        if (is_imperial and is_ton)
        else ("ksf" if is_imperial else ("t/m²" if is_ton else "kPa"))
    )
    u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
    u_rebar = "in" if is_imperial else "mm"
    u_fc = "psi" if is_imperial else "MPa"

    col_p1, col_p2 = st.columns(2)
    P_dl = col_p1.number_input(
        f"Dead Load P_DL ({u_force_per_len})",
        0.0,
        5000.0,
        100.0 if not is_imperial else 8.0,
    )
    P_ll = col_p2.number_input(
        f"Live Load P_LL ({u_force_per_len})",
        0.0,
        5000.0,
        50.0 if not is_imperial else 4.0,
    )

    st.header("2. Geometry & Geotechnical (Water Table)")
    col_g1, col_g2 = st.columns(2)
    b_wall = col_g1.number_input(
        f"Wall Thickness b_w ({u_len})",
        0.1,
        5.0,
        0.25 if not is_imperial else 0.833,
    )
    B = col_g2.number_input(
        f"Footing Width B ({u_len})", 0.5, 30.0, 1.8 if not is_imperial else 6.0
    )

    col_g3, col_g4 = st.columns(2)
    h_foot = col_g3.number_input(
        f"Footing Thickness h ({u_len})",
        0.1,
        5.0,
        0.40 if not is_imperial else 1.25,
    )
    Df = col_g4.number_input(
        f"Embedment Depth Df ({u_len})",
        0.0,
        20.0,
        1.2 if not is_imperial else 4.0,
    )

    col_s1, col_s2, col_s3 = st.columns(3)
    gamma_soil = col_s1.number_input(
        f"Soil γ ({u_gamma})",
        0.0,
        300.0,
        18.0 if not is_imperial else 115.0,
    )
    q_allow = col_s2.number_input(
        f"Gross Allowable Soil Cap. q_allow ({u_stress})",
        1.0,
        10000.0,
        150.0 if not is_imperial else 3.0,
    )
    Dw = col_s3.number_input(
        f"Water Table Depth Dw ({u_len})",
        0.0,
        50.0,
        1.0 if not is_imperial else 3.5,
    )

    st.header("3. Structural Materials & Rebar Detailing")
    aci_version = st.selectbox(
        "ACI Standard Code",
        ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"],
    )
    col_m1, col_m2 = st.columns(2)
    fc = col_m1.number_input(
        f"Concrete f'c ({u_fc})",
        10.0,
        10000.0,
        28.0 if not is_imperial else 4000.0,
    )
    fy = col_m2.number_input(
        f"Steel fy ({u_fc})",
        100.0,
        100000.0,
        420.0 if not is_imperial else 60000.0,
    )

    rebar_system = st.radio(
        "Rebar Size Standard", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"]
    )
    if "Metric" in rebar_system:
        main_rebar_opts = {
            "12 mm": {"dia": 12.0, "area": 113.1},
            "16 mm": {"dia": 16.0, "area": 201.1},
            "20 mm": {"dia": 20.0, "area": 314.2},
            "25 mm": {"dia": 25.0, "area": 490.9},
        }
        temp_rebar_opts = {
            "10 mm": {"dia": 10.0, "area": 78.5},
            "12 mm": {"dia": 12.0, "area": 113.1},
            "16 mm": {"dia": 16.0, "area": 201.1},
        }
    else:
        main_rebar_opts = {
            "#4 (0.500 in)": {"dia": 0.500, "area": 0.20},
            "#5 (0.625 in)": {"dia": 0.625, "area": 0.31},
            "#6 (0.750 in)": {"dia": 0.750, "area": 0.44},
            "#8 (1.000 in)": {"dia": 1.000, "area": 0.79},
        }
        temp_rebar_opts = {
            "#3 (0.375 in)": {"dia": 0.375, "area": 0.11},
            "#4 (0.500 in)": {"dia": 0.500, "area": 0.20},
            "#5 (0.625 in)": {"dia": 0.625, "area": 0.31},
        }

    col_r1, col_r2 = st.columns(2)
    selected_main_bar = col_r1.selectbox(
        "Main Rebar (Transverse)", list(main_rebar_opts.keys())
    )
    selected_temp_bar = col_r2.selectbox(
        "Distribution Steel (Longitudinal)", list(temp_rebar_opts.keys())
    )

    hook_type = st.radio(
        "Main Rebar End Hook Type",
        [
            "None (Straight Bar)",
            "90-Degree Standard Hook",
            "180-Degree Standard Hook",
        ],
    )

    calc_trigger = st.button(
        "🚀 Calculate Wall Footing Design",
        type="primary",
        use_container_width=True,
    )

# --- Calculation Engine ---
if calc_trigger or "wall_calc_state" in st.session_state:
    st.session_state["wall_calc_state"] = True

    # 1. Unit Normalizations & Water Table Effect
    gamma_w = 62.4 if is_imperial else (1.0 if is_ton else 9.81)
    gamma_conc = 150.0 if is_imperial else (2.4 if is_ton else 24.0)

    # Unit conversion factor for density to pressure surcharge
    if is_imperial:
        unit_div = 1000.0 if not is_ton else 2000.0  # pcf to ksf or tsf
    else:
        unit_div = 1.0  # kN/m³ * m -> kPa

    # Surcharge Calculation with Water Table
    if Dw >= Df + h_foot:
        # Water Table is deep below footing base
        surcharge = ((Df * gamma_soil) + (h_foot * gamma_conc)) / unit_div
    elif Dw <= Df:
        # Water Table is above footing base
        d_dry = Dw
        d_sat = Df - Dw
        gamma_sub = gamma_soil - gamma_w
        surcharge = (
            (d_dry * gamma_soil)
            + (d_sat * gamma_sub)
            + (h_foot * (gamma_conc - gamma_w))
        ) / unit_div
    else:
        # Water Table within footing depth
        d_dry_soil = Df
        h_dry_conc = Dw - Df
        h_sat_conc = h_foot - h_dry_conc
        surcharge = (
            (d_dry_soil * gamma_soil)
            + (h_dry_conc * gamma_conc)
            + (h_sat_conc * (gamma_conc - gamma_w))
        ) / unit_div

    # Correct Net Allowable Bearing Capacity calculation
    q_net_allow = max(0.001, q_allow - surcharge)
    P_service = P_dl + P_ll
    q_service_actual = P_service / B

    # 2. Factored Ultimate Loads
    Pu = (1.2 * P_dl) + (1.6 * P_ll)
    qu_factored = Pu / B  # Factored soil reaction per unit length

    # 3. Structural Shear Verification (One-way Shear)
    cover = (3.0 / 12.0) if is_imperial else 0.075  # 3 inches
    d_eff = h_foot - cover

    cantilever_arm = (B - b_wall) / 2.0
    crit_shear_dist = cantilever_arm - d_eff
    Vu_oneway = qu_factored * max(0.0, crit_shear_dist)

    # Size Effect Factor
    if aci_version in ["ACI 318-19", "ACI 318-22"]:
        d_mm = d_eff * 1000.0 if not is_imperial else d_eff * 12.0 * 25.4
        lambda_s = min(1.0, np.sqrt(2.0 / (1.0 + 0.004 * d_mm)))
    else:
        lambda_s = 1.0

    phi_shear = 0.75
    if not is_imperial:
        vc = 0.17 * lambda_s * np.sqrt(fc)
        force_mult = 1.0 / 9.81 if is_ton else 1.0
        Phi_Vc = (
            phi_shear
            * vc
            * (1.0 * 1000.0)
            * (d_eff * 1000.0)
            / 1000.0
            * force_mult
        )
    else:
        vc = 2.0 * lambda_s * np.sqrt(fc)
        force_mult = 0.5 if is_ton else 1.0
        Phi_Vc = (
            phi_shear * vc * (12.0) * (d_eff * 12.0) / 1000.0 * force_mult
        )

    # 4. Flexural Design (Transverse Main Steel)
    Mu = (qu_factored * (cantilever_arm**2)) / 2.0

    if not is_imperial:
        b_mm, d_mm_val = 1000.0, d_eff * 1000.0
        Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
        Rn = Mu_Nmm / (0.9 * b_mm * (d_mm_val**2))
        rho = (0.85 * fc / fy) * (
            1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc)))
        )
        rho_req = max(rho, 0.0018)
        As_main_req = rho_req * b_mm * d_mm_val  # mm²/m
        area_unit = "mm²/m"
        spacing_unit = "mm"

        # Temperature & Shrinkage Distribution Steel (Longitudinal)
        As_temp_req = 0.0018 * b_mm * (h_foot * 1000.0)  # mm²/m
    else:
        b_in, d_in_val = 12.0, d_eff * 12.0
        Mu_inlbs = Mu * 12000.0 * (2.0 if is_ton else 1.0)
        Rn = Mu_inlbs / (0.9 * b_in * (d_in_val**2))
        rho = (0.85 * fc / fy) * (
            1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc)))
        )
        rho_req = max(rho, 0.0018)
        As_main_req = rho_req * b_in * d_in_val  # in²/ft
        area_unit = "in²/ft"
        spacing_unit = "in"

        # Temperature & Shrinkage Distribution Steel
        As_temp_req = 0.0018 * b_in * (h_foot * 12.0)  # in²/ft

    # Spacing Calculations
    main_bar_area = main_rebar_opts[selected_main_bar]["area"]
    temp_bar_area = temp_rebar_opts[selected_temp_bar]["area"]

    if not is_imperial:
        s_main = (main_bar_area / As_main_req) * 1000.0
        s_temp = (temp_bar_area / As_temp_req) * 1000.0
        max_s_main = min(3 * h_foot * 1000.0, 450.0)
        max_s_temp = min(5 * h_foot * 1000.0, 450.0)
    else:
        s_main = (main_bar_area / As_main_req) * 12.0
        s_temp = (temp_bar_area / As_temp_req) * 12.0
        max_s_main = min(3 * h_foot * 12.0, 18.0)
        max_s_temp = min(5 * h_foot * 12.0, 18.0)

    s_main_final = int(min(s_main, max_s_main))
    s_temp_final = int(min(s_temp, max_s_temp))

    # --- Matplotlib Plotting Function with Legends and Hooks ---
    def draw_footing_section():
        fig, ax = plt.subplots(figsize=(7, 4.5))

        # Soil & Ground Base
        f_top = -Df
        f_bottom = -Df - h_foot

        ax.fill_between(
            [-B / 2 - 1.0, B / 2 + 1.0],
            [0, 0],
            [f_bottom - 0.4, f_bottom - 0.4],
            color="#E5D3B3",
            alpha=0.5,
            label="Soil Stratum",
        )

        # Concrete Footing & Wall
        ax.add_patch(
            patches.Rectangle(
                (-B / 2, f_bottom),
                B,
                h_foot,
                facecolor="#9CA3AF",
                edgecolor="black",
                linewidth=1.5,
                label="Concrete Footing",
            )
        )
        ax.add_patch(
            patches.Rectangle(
                (-b_wall / 2, f_top),
                b_wall,
                Df + 0.4,
                facecolor="#4B5563",
                edgecolor="black",
                linewidth=1.5,
                label="RC Wall",
            )
        )

        # Ground Level Line
        ax.axhline(
            0,
            color="#8B4513",
            linestyle="--",
            linewidth=1.2,
            label="Ground Level (GL)",
        )

        # Water Table Line
        if Dw <= Df + h_foot + 0.4:
            ax.axhline(
                -Dw,
                color="blue",
                linestyle="-.",
                linewidth=1.5,
                label=f"Water Table (Dw={Dw:.2f}{u_len})",
            )

        # Rebar Layout Drawing
        main_y = f_bottom + cover
        left_x = -B / 2 + cover
        right_x = B / 2 - cover

        # Main Transverse Rebar Line
        ax.plot(
            [left_x, right_x],
            [main_y, main_y],
            color="red",
            linewidth=2.5,
            label=f"Main Steel: {selected_main_bar} @ {s_main_final}{spacing_unit}",
        )

        # Hook Rendering
        hook_len = 0.12 if not is_imperial else 0.4
        if "90-Degree" in hook_type:
            ax.plot(
                [left_x, left_x],
                [main_y, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )
            ax.plot(
                [right_x, right_x],
                [main_y, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )
        elif "180-Degree" in hook_type:
            ax.plot(
                [left_x, left_x],
                [main_y, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )
            ax.plot(
                [left_x, left_x - 0.05],
                [main_y + hook_len, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )
            ax.plot(
                [right_x, right_x],
                [main_y, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )
            ax.plot(
                [right_x, right_x + 0.05],
                [main_y + hook_len, main_y + hook_len],
                color="red",
                linewidth=2.5,
            )

        # Distribution / Temperature Steel Dots (Longitudinal)
        dot_x_coords = np.linspace(left_x + 0.1, right_x - 0.1, 7)
        ax.scatter(
            dot_x_coords,
            [main_y + 0.03] * 7,
            color="darkblue",
            s=25,
            zorder=5,
            label=f"Temp Steel: {selected_temp_bar} @ {s_temp_final}{spacing_unit}",
        )

        # Dimension Lines & Annotations
        dim_y = f_bottom - 0.25
        ax.annotate(
            "",
            xy=(-B / 2, dim_y),
            xytext=(B / 2, dim_y),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.2),
        )
        ax.text(
            0,
            dim_y - 0.10,
            f"B = {B:.2f} {u_len}",
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
        )

        ax.annotate(
            "",
            xy=(-B / 2 - 0.2, f_bottom),
            xytext=(-B / 2 - 0.2, f_top),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.2),
        )
        ax.text(
            -B / 2 - 0.28,
            (f_bottom + f_top) / 2,
            f"h = {h_foot:.2f} {u_len}",
            ha="right",
            va="center",
            fontsize=8,
            fontweight="bold",
            rotation=90,
        )

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(f_bottom - 0.6, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.legend(
            loc="upper right", bbox_to_anchor=(1.45, 1.0), fontsize=7, frameon=True
        )
        plt.title(
            f"Wall Footing Cross-Section Detailing ({hook_type})",
            fontsize=10,
            fontweight="bold",
        )
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    # --- Step-by-Step PDF Report Generation Function ---
    def generate_pdf_report(plot_img_buf):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor("#1E3A8A"),
        )
        sec_heading = ParagraphStyle(
            "SecHeading",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=6,
            spaceAfter=4,
            textColor=colors.HexColor("#0F172A"),
        )
        normal_p = ParagraphStyle(
            "NormalP",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            spaceAfter=4,
        )
        code_p = ParagraphStyle(
            "CodeP",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            fontName="Courier",
            spaceAfter=3,
            textColor=colors.HexColor("#334155"),
        )

        story = []
        story.append(
            Paragraph(
                "<b>CONTINUOUS RC WALL FOOTING DESIGN REPORT</b>", title_style
            )
        )
        story.append(
            Paragraph(
                f"Design Standard: <b>{aci_version}</b> | Unit System: <b>{unit_system}</b>",
                normal_p,
            )
        )
        story.append(Spacer(1, 4))

        # 1. Inputs Summary
        story.append(Paragraph("1. Design Inputs & Parameters", sec_heading))
        story.append(
            Paragraph(
                f"• Applied Loads: P<sub>DL</sub> = {P_dl:.2f} {u_force_per_len}, P<sub>LL</sub> = {P_ll:.2f} {u_force_per_len}",
                normal_p,
            )
        )
        story.append(
            Paragraph(
                f"• Dimensions: B = {B:.2f} {u_len}, h = {h_foot:.2f} {u_len}, b<sub>wall</sub> = {b_wall:.2f} {u_len}, D<sub>f</sub> = {Df:.2f} {u_len}",
                normal_p,
            )
        )
        story.append(
            Paragraph(
                f"• Soil & Water Table: γ<sub>soil</sub> = {gamma_soil:.1f} {u_gamma}, q<sub>allow,gross</sub> = {q_allow:.2f} {u_stress}, Water Table D<sub>w</sub> = {Dw:.2f} {u_len}",
                normal_p,
            )
        )

        # 2. Bearing Capacity Steps
        story.append(
            Paragraph(
                "2. Geotechnical Soil Bearing Capacity Verification", sec_heading
            )
        )
        story.append(
            Paragraph(
                f"  Surcharge Stress q<sub>surcharge</sub> = Σ (γ<sub>i</sub> × h<sub>i</sub>) = <b>{surcharge:.3f} {u_stress}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Net Allowable Capacity q<sub>net,allow</sub> = q<sub>allow,gross</sub> - q<sub>surcharge</sub> = {q_allow:.2f} - {surcharge:.3f} = <b>{q_net_allow:.3f} {u_stress}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Actual Service Pressure q<sub>service</sub> = (P<sub>DL</sub> + P<sub>LL</sub>) / B = ({P_dl:.2f} + {P_ll:.2f}) / {B:.2f} = <b>{q_service_actual:.3f} {u_stress}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Bearing Capacity Check: q<sub>service</sub> ({q_service_actual:.3f}) ≤ q<sub>net,allow</sub> ({q_net_allow:.3f}) -> <b>{'[PASS]' if q_service_actual <= q_net_allow else '[OVERLOADED]'}</b>",
                code_p,
            )
        )

        # 3. Structural Shears
        story.append(
            Paragraph("3. Ultimate Shear Verification (ACI 318)", sec_heading)
        )
        story.append(
            Paragraph(
                f"  Factored Load P<sub>u</sub> = 1.2(P<sub>DL</sub>) + 1.6(P<sub>LL</sub>) = 1.2({P_dl:.2f}) + 1.6({P_ll:.2f}) = <b>{Pu:.2f} {u_force_per_len}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Factored Reaction Pressure q<sub>u</sub> = P<sub>u</sub> / B = <b>{qu_factored:.3f} {u_stress}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Effective Depth d<sub>eff</sub> = h - cover = {h_foot:.3f} - {cover:.3f} = <b>{d_eff:.3f} {u_len}</b> | Size Factor λ<sub>s</sub> = <b>{lambda_s:.3f}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Cantilever Arm = (B - b<sub>w</sub>)/2 = ({B:.2f} - {b_wall:.2f})/2 = <b>{cantilever_arm:.3f} {u_len}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Critical Shear Distance = Cantilever - d<sub>eff</sub> = <b>{crit_shear_dist:.3f} {u_len}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Factored Shear Force V<sub>u,oneway</sub> = q<sub>u</sub> × max(0, Crit Dist) = <b>{Vu_oneway:.2f} {u_force_per_len}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  One-Way Shear Resistance φV<sub>c</sub> = <b>{Phi_Vc:.2f} {u_force_per_len}</b> -> <b>{'[PASS]' if Phi_Vc >= Vu_oneway else '[FAIL]'}</b>",
                code_p,
            )
        )

        # 4. Flexural Design Steps
        story.append(
            Paragraph(
                "4. Flexural Design & Reinforcement Spacing", sec_heading
            )
        )
        story.append(
            Paragraph(
                f"  Ultimate Design Moment M<sub>u</sub> = (q<sub>u</sub> × Cantilever²) / 2 = <b>{Mu:.2f}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  Required Transverse Main Steel A<sub>s,main</sub> = <b>{As_main_req:.2f} {area_unit}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  <b>Main Steel Recommendation: Provide {selected_main_bar} @ {s_main_final} {spacing_unit} c/c ({hook_type})</b>",
                normal_p,
            )
        )
        story.append(
            Paragraph(
                f"  Required Temperature/Distribution Steel A<sub>s,temp</sub> = 0.0018 × b × h = <b>{As_temp_req:.2f} {area_unit}</b>",
                code_p,
            )
        )
        story.append(
            Paragraph(
                f"  <b>Distribution Steel Recommendation: Provide {selected_temp_bar} @ {s_temp_final} {spacing_unit} c/c (Longitudinal)</b>",
                normal_p,
            )
        )

        # 5. Drawing
        story.append(Spacer(1, 6))
        story.append(
            Paragraph("5. Structural Detailing Drawing", sec_heading)
        )
        story.append(RLImage(plot_img_buf, width=420, height=270))

        doc.build(story)
        buf.seek(0)
        return buf

    # --- UI Rendering Output ---
    sec_img_buf = draw_footing_section()

    with col_res:
        st.header("📊 Results & Structural Verification")

        # Metrics
        st.subheader("1. Bearing Capacity Verification")
        c1, c2 = st.columns(2)
        c1.metric(
            "Service Soil Pressure (q_service)",
            f"{q_service_actual:.2f} {u_stress}",
        )
        c2.metric(
            "Net Allowable Capacity (q_net)",
            f"{q_net_allow:.2f} {u_stress}",
            delta="✅ SAFE" if q_service_actual <= q_net_allow else "❌ OVERLOADED",
        )

        st.subheader("2. One-Way Shear Verification")
        s1, s2 = st.columns(2)
        s1.metric("Factored Shear Vu", f"{Vu_oneway:.2f} {u_force_per_len}")
        s2.metric(
            "Shear Capacity φVc",
            f"{Phi_Vc:.2f} {u_force_per_len}",
            delta="✅ PASS" if Phi_Vc >= Vu_oneway else "❌ FAIL",
        )

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(
            f"• **Main Steel (Transverse):** **{selected_main_bar} @ {s_main_final} {spacing_unit} c/c** with **{hook_type}**"
        )
        st.markdown(
            f"• **Distribution Steel (Longitudinal):** **{selected_temp_bar} @ {s_temp_final} {spacing_unit} c/c**"
        )

        st.image(
            sec_img_buf,
            caption=f"Cross-Section Diagram (Water Table Dw={Dw:.2f}{u_len}, Cover=3 in)",
        )

        st.markdown("---")
        pdf_buf = generate_pdf_report(sec_img_buf)
        st.download_button(
            label="📄 Download Complete Design Calculation Report (PDF)",
            data=pdf_buf.getvalue(),
            file_name="Wall_Footing_Detailed_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
