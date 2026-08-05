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

# Page Setup
st.set_page_config(
    page_title="Single Footing Design Suite", page_icon="🏗️", layout="wide"
)
st.title("🏗️ Single Geotechnical & Structural Footing Design Suite")

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
            "Direct Gross Allowable Soil Capacity",
            "c-phi Parameters (Analytical - Terzaghi/Meyerhof)",
            "SPT N-value (Empirical Method - Meyerhof/Bowles)",
        ],
    )

    # --- Column Loading Inputs (DL and LL unfactored) ---
    st.header("2. Applied Column Loads & Eccentricity")
    col_p1, col_p2 = st.columns(2)
    P_DL = col_p1.number_input(f"Dead Load P_DL ({u_force})", 0.0, 100000.0, 300.0 if not is_imperial else 60.0)
    P_LL = col_p2.number_input(f"Live Load P_LL ({u_force})", 0.0, 100000.0, 200.0 if not is_imperial else 40.0)
    P_unfactored = P_DL + P_LL

    col_mx, col_my = st.columns(2)
    Mx_unfactored = col_mx.number_input(f"Moment Mx ({u_moment})", 0.0, 10000.0, 0.0)
    My_unfactored = col_my.number_input(f"Moment My ({u_moment})", 0.0, 10000.0, 0.0)

    col_ex, col_ey = st.columns(2)
    ex_input = col_ex.number_input(f"Column Eccentricity ex ({u_len})", -5.0, 5.0, 0.0, step=0.05)
    ey_input = col_ey.number_input(f"Column Eccentricity ey ({u_len})", -5.0, 5.0, 0.0, step=0.05)

    # --- Geotechnical Inputs ---
    if "Direct" in geo_input_mode:
        q_allow_direct = st.number_input(f"Gross Allowable Soil Capacity q_allow ({u_stress})", 1.0, 10000.0, 150.0 if not is_imperial else 3.0)
        num_layers = 1
        soil_layers = [{"thickness": 10.0, "gamma": 18.0 if not is_imperial else 115.0, "c": 0, "phi": 0, "N": 0}]
        FS = 3.0
    else:
        q_allow_direct = None
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
        FS = st.number_input("Geotechnical Safety Factor (FS)", 1.0, 10.0, 3.0)

    st.header("4. Geometry Settings (Footing & Column)")
    col_b, col_l = st.columns(2)
    B = col_b.number_input(f"Footing Width B (x-dir) ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)
    L = col_l.number_input(f"Footing Length L (y-dir) ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)

    col_shape = st.radio("Column Shape", ["Rectangular / Square", "Circular"])
    if col_shape == "Circular":
        D_col = st.number_input(f"Column Diameter D ({u_len})", 0.1, 5.0, 0.45 if not is_imperial else 1.25)
        cx = D_col
        cy = D_col
    else:
        D_col = None
        col_cx, col_cy = st.columns(2)
        cx = col_cx.number_input(f"Column Size cx ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.0)
        cy = col_cy.number_input(f"Column Size cy ({u_len})", 0.1, 5.0, 0.4 if not is_imperial else 1.25)

    Df = st.number_input(f"Embedment Depth Df (to Bottom of Footing) ({u_len})", 0.0, 20.0, 1.5 if not is_imperial else 3.5)
    h_foot = st.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 0.45 if not is_imperial else 1.5)
    Dw = st.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 0.8 if not is_imperial else 2.5)

    st.header("5. Structural & Rebar Details")
    aci_version = st.selectbox("ACI 318 Code Standard", ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"])

    u_fc = "psi" if is_imperial else "MPa"
    fc = st.number_input(f"Concrete Strength f'c ({u_fc})", 10.0, 10000.0, 28.0 if not is_imperial else 4000.0)
    fy = st.number_input(f"Steel Yield Strength fy ({u_fc})", 100.0, 100000.0, 420.0 if not is_imperial else 60000.0)

    rebar_system = st.radio("Rebar Unit System Standard", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"])

    if "Metric" in rebar_system:
        rebar_options = {
            "16 mm": {"dia": 16.0, "area_mm2": 201.06, "area_in2": 0.3116, "is_metric": True},
            "18 mm": {"dia": 18.0, "area_mm2": 254.47, "area_in2": 0.3944, "is_metric": True},
            "20 mm": {"dia": 20.0, "area_mm2": 314.16, "area_in2": 0.4869, "is_metric": True},
            "22 mm": {"dia": 22.0, "area_mm2": 380.13, "area_in2": 0.5892, "is_metric": True},
            "25 mm": {"dia": 25.0, "area_mm2": 490.87, "area_in2": 0.7608, "is_metric": True},
        }
    else:
        rebar_options = {
            "#5 (0.625in)": {"dia": 0.625, "area_mm2": 200.0, "area_in2": 0.31, "is_metric": False},
            "#6 (0.75in)": {"dia": 0.75, "area_mm2": 284.0, "area_in2": 0.44, "is_metric": False},
            "#7 (0.875in)": {"dia": 0.875, "area_mm2": 387.0, "area_in2": 0.60, "is_metric": False},
            "#8 (1.0in)": {"dia": 1.0, "area_mm2": 510.0, "area_in2": 0.79, "is_metric": False},
        }

    col_rb, col_tol = st.columns(2)
    selected_rebar = col_rb.selectbox("Select Reinforcement Bar", list(rebar_options.keys()))
    bar_tolerance_pct = col_tol.number_input("Market Bar Size Reduction (%)", 0.0, 15.0, 0.0, step=0.5)

    clear_cover_input = st.selectbox("Clear Concrete Cover", ["3.0 inches (75 mm) - Standard Footing Cover"], index=0)
    hook_type = st.radio("Rebar End Hook Type", ["None (Straight Bar)", "90-Degree Standard Hook", "180-Degree Standard Hook"])

    is_selected_metric = rebar_options[selected_rebar]["is_metric"]
    nom_area = rebar_options[selected_rebar]["area_in2"] if is_imperial else rebar_options[selected_rebar]["area_mm2"]
    actual_area = nom_area * (1.0 - (bar_tolerance_pct / 100.0))

    calc_trigger = st.button("🚀 Calculate Single Footing Design", type="primary", use_container_width=True)

# --- Calculation Engine ---
if calc_trigger or "calculated" in st.session_state:
    st.session_state["calculated"] = True

    # 1. Total Unfactored Moment & Eccentricity
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

    # 3. Geotechnical Capacity Calculation
    c_val = target_layer["c"]
    phi_val = target_layer["phi"]
    if "Direct" in geo_input_mode:
        q_allow = q_allow_direct
        q_ult = q_allow * FS
        Nc, Nq, Ng = 0.0, 0.0, 0.0
    elif "SPT" in geo_input_mode:
        N_val = target_layer["N"]
        Kd = min(1.33, 1 + 0.33 * (Df / B_eff))
        if is_imperial:
            q_allow = (N_val / 4.0) * (1.0 if is_ton else 2.0) * Kd
        else:
            q_allow = (N_val * 1.2 if is_ton else N_val / 0.05) * Kd
        q_ult = q_allow * FS
        Nc, Nq, Ng = 0.0, 0.0, 0.0
    else:
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

    # 4. Structural Design Calculations
    Pu = (1.2 * P_DL) + (1.6 * P_LL)
    Mux_total = (1.2 * Mx_unfactored) + (1.6 * (P_unfactored * abs(ey_input)))
    qu_factored = (Pu / footing_area) + (6 * Mux_total / (B * (L**2)))

    cover = 0.075 if not is_imperial else (3.0 / 12.0)
    d_eff = h_foot - cover

    if aci_version in ["ACI 318-19", "ACI 318-22"]:
        d_mm_check = d_eff * 1000 if not is_imperial else d_eff * 12 * 25.4
        lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_mm_check)))
    else:
        lambda_s = 1.0

    # Shear Checks
    if col_shape == "Circular":
        bo = np.pi * (D_col + d_eff)
        Area_bo = (np.pi / 4.0) * ((D_col + d_eff) ** 2)
        cantilever_x = max((B / 2.0) - (0.886 * D_col / 2.0) + ex_input, (B / 2.0) - (0.886 * D_col / 2.0) - ex_input)
        cantilever_y = max((L / 2.0) - (0.886 * D_col / 2.0) + ey_input, (L / 2.0) - (0.886 * D_col / 2.0) - ey_input)
    else:
        bo = 2 * ((cx + d_eff) + (cy + d_eff))
        Area_bo = (cx + d_eff) * (cy + d_eff)
        cantilever_x = max((B / 2.0) - (cx / 2.0) + ex_input, (B / 2.0) - (cx / 2.0) - ex_input)
        cantilever_y = max((L / 2.0) - (cy / 2.0) + ey_input, (L / 2.0) - (cy / 2.0) - ey_input)

    Vu_punch = qu_factored * (footing_area - Area_bo)
    crit_dist_x = cantilever_x - d_eff
    Vu_oneway = qu_factored * L * max(0.0, crit_dist_x)

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

    # Reinforcement Calculation (Updated Conservative Beam Minimum Included)
    Mu_x = (qu_factored * L * (cantilever_x**2)) / 2
    Mu_y = (qu_factored * B * (cantilever_y**2)) / 2

    if not is_imperial:
        w_mm, d_mm = L * 1000, d_eff * 1000
        Mu_Nmm = Mu_x * 1e6 * (9.81 if is_ton else 1.0)
        Rn_val = Mu_Nmm / (0.9 * w_mm * (d_mm**2))
        rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn_val) / (0.85 * fc))))
        
        # Minimum Steel Ratios
        rho_slab_min = 0.0018
        rho_beam_min = max((0.25 * np.sqrt(fc)) / fy, 1.4 / fy)
        rho_min = max(rho_slab_min, rho_beam_min)
        
        rho_req = max(rho_calc, rho_min)
        As_req = rho_req * w_mm * d_mm
        total_span = L * 1000
        clear_c = 75.0
        unit_as = "mm²"
        unit_rn = "N/mm²"
        spacing_unit = "mm"
    else:
        w_in, d_in = L * 12, d_eff * 12
        Mu_inlbs = Mu_x * 12000 * (2.0 if is_ton else 1.0)
        Rn_val = Mu_inlbs / (0.9 * w_in * (d_in**2))
        rho_calc = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn_val) / (0.85 * fc))))
        
        # Minimum Steel Ratios (Imperial)
        rho_slab_min = 0.0018
        rho_beam_min = max((3.0 * np.sqrt(fc)) / fy, 200.0 / fy)
        rho_min = max(rho_slab_min, rho_beam_min)
        
        rho_req = max(rho_calc, rho_min)
        As_req = rho_req * w_in * d_in
        total_span = L * 12
        clear_c = 3.0
        unit_as = "in²"
        unit_rn = "psi"
        spacing_unit = "in"

    n_bars = int(np.ceil(As_req / actual_area))
    num_bars_x = max(2, n_bars)
    spacing_x = round((total_span - (2 * clear_c)) / max(1, (num_bars_x - 1)), 1)

    num_bars_y = num_bars_x
    spacing_y = spacing_x

    # --- Drawing Logic ---
    def draw_cross_section():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))

        footing_bottom_y = -Df
        footing_top_y = -Df + h_foot

        ax.fill_between([-B / 2 - 1.2, B / 2 + 1.2], [0, 0], [footing_bottom_y - 0.5, footing_bottom_y - 0.5], color="#E5D3B3", alpha=0.5)
        ax.axhline(0, color="k", linestyle="--", linewidth=1, label="Ground Level (GL)")

        if Dw <= (Df + 0.5):
            ax.axhline(-Dw, color="blue", linestyle="-.", linewidth=1.5, label=f"Water Table (Dw={Dw:.2f}{u_len})")

        ax.add_patch(plt.Rectangle((-B / 2, footing_bottom_y), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5, label="Footing"))

        col_x_start = ex_input - (cx / 2.0)
        col_height = (Df - h_foot) + 0.3
        if col_shape == "Circular":
            ax.add_patch(plt.Rectangle((col_x_start, footing_top_y), cx, col_height, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Circular Col"))
        else:
            ax.add_patch(plt.Rectangle((col_x_start, footing_top_y), cx, col_height, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Column"))

        rebar_y_xdir = footing_bottom_y + cover
        left_x = -B / 2 + cover
        right_x = B / 2 - cover
        ax.plot([left_x, right_x], [rebar_y_xdir, rebar_y_xdir], color="red", linewidth=2.0, label=f"x-dir: {num_bars_x}-{selected_rebar}")

        hook_len = 0.12 if not is_imperial else 0.4
        if "90-Degree" in hook_type:
            ax.plot([left_x, left_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x, right_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
        elif "180-Degree" in hook_type:
            ax.plot([left_x, left_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([left_x, left_x + 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([left_x + 0.03, left_x + 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + 0.02], color="red", linewidth=2.0)

            ax.plot([right_x, right_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x, right_x - 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x - 0.03, right_x - 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + 0.02], color="red", linewidth=2.0)

        x_coords = np.linspace(left_x, right_x, num_bars_x)
        ax.scatter(x_coords, [rebar_y_xdir + 0.02] * num_bars_x, color="darkblue", s=15, zorder=5, label=f"y-dir: {num_bars_y} Nos")

        ax.set_xlim(-B / 2 - 1.0, B / 2 + 1.0)
        ax.set_ylim(footing_bottom_y - 0.7, 0.5)
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

    def draw_plan_view():
        fig, ax = plt.subplots(figsize=(6.5, 6.5))
        ax.add_patch(patches.Rectangle((-B / 2, -L / 2), B, L, facecolor="#E5E7EB", edgecolor="black", linewidth=1.5))

        left_x, right_x = -B / 2 + cover, B / 2 - cover
        bot_y, top_y = -L / 2 + cover, L / 2 - cover

        y_pos_list = np.linspace(bot_y, top_y, num_bars_x)
        for y_p in y_pos_list:
            ax.plot([left_x, right_x], [y_p, y_p], color="red", linewidth=1.0, alpha=0.7)

        x_pos_list = np.linspace(left_x, right_x, num_bars_y)
        for x_p in x_pos_list:
            ax.plot([x_p, x_p], [bot_y, top_y], color="blue", linewidth=1.0, alpha=0.7)

        if col_shape == "Circular":
            ax.add_patch(patches.Circle((ex_input, ey_input), radius=D_col / 2.0, facecolor="#374151", edgecolor="black", linewidth=1.5, zorder=6))
            ax.text(ex_input, ey_input, f"D={D_col:.2f}", color="white", ha="center", va="center", fontsize=7, fontweight="bold", zorder=7)
        else:
            col_x_min = ex_input - (cx / 2.0)
            col_y_min = ey_input - (cy / 2.0)
            ax.add_patch(patches.Rectangle((col_x_min, col_y_min), cx, cy, facecolor="#374151", edgecolor="black", linewidth=1.5, zorder=6))
            ax.text(ex_input, ey_input, f"cx={cx:.2f}\ncy={cy:.2f}", color="white", ha="center", va="center", fontsize=7, fontweight="bold", zorder=7)

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(-L / 2 - 0.8, L / 2 + 0.8)
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

    # --- PDF Report Generator ---
    def generate_pdf_report(sec_buf, plan_buf):
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()

        main_title_style = ParagraphStyle(
            'MainTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor("#1A365D"), spaceAfter=8
        )
        sub_title_style = ParagraphStyle(
            'SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#2D3748"), spaceAfter=12
        )
        h1_sec_style = ParagraphStyle(
            'H1Sec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#000000"), spaceBefore=10, spaceAfter=6
        )
        sub_heading_style = ParagraphStyle(
            'SubHeading', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=10, leading=14, textColor=colors.HexColor("#2B6CB0"), spaceBefore=6, spaceAfter=4
        )
        bullet_style = ParagraphStyle(
            'BulletText', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#1A202C")
        )
        math_code_style = ParagraphStyle(
            'MathCode', parent=styles['Normal'], fontName='Courier', fontSize=8.5, leading=12, textColor=colors.HexColor("#4A5568")
        )
        final_spec_style = ParagraphStyle(
            'FinalSpec', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=10, leading=14, textColor=colors.HexColor("#1A365D"), spaceBefore=8
        )

        story = []

        # Header Title
        story.append(Paragraph("STRUCTURAL & GEOTECHNICAL FOOTING DESIGN CALCULATION REPORT", main_title_style))
        story.append(Paragraph(
            f"Code Standard: <b>{aci_version}</b> | Unit System: <b>{unit_system}</b> | Clear Cover: <b>3.0 in (75 mm)</b><br/>"
            f"Reinforcement Hook Type: <b>{hook_type}</b>",
            sub_title_style
        ))

        # 1. Column Loads & Eccentricity
        story.append(Paragraph("1. Column Loads & Eccentricity Calculations", h1_sec_style))
        story.append(Paragraph(f"• Axial Load (P) = <b>{P_unfactored:.2f} {u_force}</b> | Mx = <b>{Mx_unfactored:.2f} {u_moment}</b> | My = <b>{My_unfactored:.2f} {u_moment}</b>", bullet_style))
        story.append(Paragraph(f"• Applied Column Eccentricity: e<sub>x,input</sub> = {ex_input:.2f} {u_len}, e<sub>y,input</sub> = {ey_input:.2f} {u_len}", bullet_style))
        
        story.append(Paragraph("Step-by-step Eccentricity Derivation:", sub_heading_style))
        math_1 = (
            f"M<sub>x,total</sub> = M<sub>x</sub> + (P × |e<sub>y</sub>|) = {Mx_unfactored:.2f} + ({P_unfactored:.2f} × {abs(ey_input):.2f}) = {Mx_total:.2f} {u_moment}<br/>"
            f"M<sub>y,total</sub> = M<sub>y</sub> + (P × |e<sub>x</sub>|) = {My_unfactored:.2f} + ({P_unfactored:.2f} × {abs(ex_input):.2f}) = {My_total:.2f} {u_moment}<br/>"
            f"e<sub>x,total</sub> = M<sub>y,total</sub> / P = {My_total:.2f} / {P_unfactored:.2f} = {e_x_total:.4f} {u_len}<br/>"
            f"e<sub>y,total</sub> = M<sub>x,total</sub> / P = {Mx_total:.2f} / {P_unfactored:.2f} = {e_y_total:.4f} {u_len}"
        )
        story.append(Paragraph(math_1, math_code_style))

        # 2. Geotechnical Bearing Capacity
        story.append(Paragraph("2. Geotechnical Bearing Capacity", h1_sec_style))
        story.append(Paragraph(f"• Footing Dimensions: B = {B:.2f} {u_len}, L = {L:.2f} {u_len}, D<sub>f</sub> = {Df:.2f} {u_len}", bullet_style))
        story.append(Paragraph(f"• Selected Calculation Method: <b>{geo_input_mode}</b>", bullet_style))
        
        if "Direct" in geo_input_mode:
            math_2b = (
                f"q<sub>allow,direct</sub> = {q_allow:.2f} {u_stress}<br/>"
                f"q<sub>max,service</sub> = P/A + 6M<sub>x</sub>/(BL²) + 6M<sub>y</sub>/(LB²) = {q_max_service:.2f} {u_stress} [{'PASS' if q_max_service <= q_allow else 'FAIL'}]"
            )
        elif "SPT" in geo_input_mode:
            math_2b = (
                f"N-value = {target_layer['N']}, K<sub>d</sub> = {Kd:.2f}<br/>"
                f"q<sub>allow</sub> = {q_allow:.2f} {u_stress}<br/>"
                f"q<sub>max,service</sub> = {q_max_service:.2f} {u_stress} [{'PASS' if q_max_service <= q_allow else 'FAIL'}]"
            )
        else:
            math_2b = (
                f"N<sub>c</sub> = {Nc:.2f}, N<sub>q</sub> = {Nq:.2f}, N<sub>γ</sub> = {Ng:.2f} (Bearing Layer φ = {phi_val:.1f}°)<br/>"
                f"q<sub>ult</sub> = (c × N<sub>c</sub>) + (q<sub>surcharge</sub> × N<sub>q</sub>) + (0.5 × γ<sub>eff</sub> × B<sub>eff</sub> × N<sub>γ</sub>)<br/>"
                f"q<sub>ult</sub> = ({c_val:.1f} × {Nc:.2f}) + ({q_surcharge:.2f} × {Nq:.2f}) + (0.5 × {target_layer['gamma']:.1f} × {B_eff:.2f} × {Ng:.2f}) = {q_ult:.2f} {u_stress}<br/>"
                f"q<sub>allow</sub> = q<sub>ult</sub> / FS = {q_ult:.2f} / {FS:.1f} = {q_allow:.2f} {u_stress}<br/>"
                f"q<sub>max,service</sub> = P/A + 6M<sub>x</sub>/(BL²) + 6M<sub>y</sub>/(LB²) = {q_max_service:.2f} {u_stress} [{'PASS' if q_max_service <= q_allow else 'FAIL'}]"
            )
        story.append(Paragraph(math_2b, math_code_style))

        # 3. Structural Shear Verification
        story.append(Paragraph("3. Structural Shear Verification (ACI 318)", h1_sec_style))
        story.append(Paragraph(f"• Factored Load P<sub>u</sub> = 1.2 × DL + 1.6 × LL = <b>{Pu:.2f} {u_force}</b>", bullet_style))
        story.append(Paragraph(f"• Factored Ultimate Pressure q<sub>u</sub> = P<sub>u</sub>/A + 6M<sub>ux</sub>/(BL²) = <b>{qu_factored:.2f} {u_stress}</b>", bullet_style))
        story.append(Paragraph(f"• Effective Depth d<sub>eff</sub> = h - cover = {h_foot:.3f} - {cover:.3f} = <b>{d_eff:.3f} {u_len}</b> | Size Effect λ<sub>s</sub> = <b>{lambda_s:.3f}</b>", bullet_style))

        story.append(Paragraph("3.1 Two-Way Punching Shear Calculation:", sub_heading_style))
        math_3a = (
            f"Critical Perimeter b<sub>o</sub> = 2 × [(c<sub>x</sub> + d) + (c<sub>y</sub> + d)] = {bo:.3f} {u_len}<br/>"
            f"Punching Area A<sub>bo</sub> = (c<sub>x</sub> + d)(c<sub>y</sub> + d) = {Area_bo:.3f} {u_len}²<br/>"
            f"V<sub>u,punch</sub> = q<sub>u</sub> × (B × L - A<sub>bo</sub>) = {qu_factored:.2f} × ({B*L:.2f} - {Area_bo:.2f}) = {Vu_punch:.2f} {u_force}<br/>"
            f"v<sub>c,punch</sub> = 0.33 × λ<sub>s</sub> × √(f'c) = {vc_punch:.3f}<br/>"
            f"φV<sub>c,punch</sub> = φ × v<sub>c</sub> × b<sub>o</sub> × d = {Phi_Vc_punch:.2f} {u_force} [{'PASS' if Phi_Vc_punch >= Vu_punch else 'FAIL'}]"
        )
        story.append(Paragraph(math_3a, math_code_style))

        story.append(Paragraph("3.2 One-Way Beam Shear Calculation:", sub_heading_style))
        math_3b = (
            f"Max Cantilever Arm = (B/2 - c<sub>x</sub>/2 + e<sub>x</sub>) = {cantilever_x:.3f} {u_len}<br/>"
            f"Critical Shear Distance = Cantilever - d = {cantilever_x:.3f} - {d_eff:.3f} = {max(0.0, crit_dist_x):.3f} {u_len}<br/>"
            f"V<sub>u,oneway</sub> = q<sub>u</sub> × L × Critical Distance = {qu_factored:.2f} × {L:.2f} × {max(0.0, crit_dist_x):.3f} = {Vu_oneway:.2f} {u_force}<br/>"
            f"φV<sub>c,oneway</sub> = φ × (0.17 × λ<sub>s</sub> × √(f'c)) × L × d = {Phi_Vc_oneway:.2f} {u_force} [{'PASS' if Phi_Vc_oneway >= Vu_oneway else 'FAIL'}]"
        )
        story.append(Paragraph(math_3b, math_code_style))

        # 4. Flexural Reinforcement Design
        story.append(Paragraph("4. Flexural Reinforcement Design", h1_sec_style))
        math_4a = (
            f"M<sub>u</sub> = (q<sub>u</sub> × L × Cantilever²) / 2 = ({qu_factored:.2f} × {L:.2f} × {cantilever_x:.2f}²) / 2 = {Mu_x:.2f} {u_moment}<br/>"
            f"Nominal Resistance Factor R<sub>n</sub> = M<sub>u</sub> / (φ × b × d²) = {Rn_val:.4f} {unit_rn}"
        )
        story.append(Paragraph(math_4a, math_code_style))

        math_4b = (
            f"Calculated Steel Ratio ρ = (0.85 × f'c / f<sub>y</sub>) × [1 - √(1 - 2R<sub>n</sub> / (0.85 × f'c))] = {rho_calc:.6f}<br/>"
            f"Minimum Ratios: ρ<sub>slab,min</sub> = {rho_slab_min:.6f} | Conservative Beam ρ<sub>beam,min</sub> = {rho_beam_min:.6f}<br/>"
            f"Governing Required Steel Ratio ρ<sub>req</sub> = max(ρ, ρ<sub>slab,min</sub>, ρ<sub>beam,min</sub>) = {rho_req:.6f}<br/>"
            f"Required Steel Area A<sub>s,req</sub> = ρ<sub>req</sub> × L × d = {As_req:.2f} {unit_as}<br/>"
            f"Selected Bar: {selected_rebar} with {hook_type} (Effective Area = {actual_area:.2f} {unit_as} with {bar_tolerance_pct}% tolerance)<br/>"
            f"Bar Count Calculation: N = ceil(A<sub>s,req</sub> / A<sub>bar</sub>) = ceil({As_req:.2f} / {actual_area:.2f}) = {num_bars_x} Bars<br/>"
            f"Spacing Calculation: s = (L - 2xCover) / (N - 1) = {spacing_x:.1f} {spacing_unit} c/c (Cover = {cover*(12 if is_imperial else 1000):.1f} {u_rebar})"
        )
        story.append(Paragraph(math_4b, math_code_style))

        story.append(Paragraph(
            f"FINAL SPECIFICATION: Provide {num_bars_x} Nos - {selected_rebar} with {hook_type} @ {spacing_x} {spacing_unit} c/c (Both Ways)",
            final_spec_style
        ))
        story.append(Spacer(1, 10))

        # 5. Structural Detailing Drawings
        story.append(Paragraph("5. Structural Detailing Drawings", h1_sec_style))
        img_sec = RLImage(sec_buf, width=240, height=160)
        img_plan = RLImage(plan_buf, width=240, height=160)
        img_table = Table([[img_sec, img_plan]], colWidths=[255, 255])
        story.append(img_table)

        doc.build(story)
        pdf_buf.seek(0)
        return pdf_buf

    # Render Outputs
    sec_img = draw_cross_section()
    plan_img = draw_plan_view()
    pdf_file = generate_pdf_report(sec_img, plan_img)

    with col_res:
        st.header("📊 Results & Verification Summary")
        st.subheader("1. Eccentricity & Soil Pressure")
        st.metric("Total Unfactored P", f"{P_unfactored:.2f} {u_force} (DL: {P_DL}, LL: {P_LL})")
        st.metric("Max Pressure (q_max)", f"{q_max_service:.2f} {u_stress}", delta="✅ SAFE" if q_max_service <= q_allow else "❌ OVERLOADED")

        st.subheader("2. Structural Shears Check")
        s1, s2 = st.columns(2)
        s1.metric("Punching Shear", f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}", delta="✅ PASS" if Phi_Vc_punch >= Vu_punch else "❌ FAIL")
        s2.metric("One-Way Shear", f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}", delta="✅ PASS" if Phi_Vc_oneway >= Vu_oneway else "❌ FAIL")

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(f"• **x-direction Steel:** Provide **{num_bars_x} Nos - {selected_rebar}** @ **{spacing_x} {spacing_unit} c/c**")
        st.markdown(f"• **y-direction Steel:** Provide **{num_bars_y} Nos - {selected_rebar}** @ **{spacing_y} {spacing_unit} c/c**")

        st.subheader("4. Detailing Drawings")
        st.image(sec_img, caption="Footing Elevation Section (Ground to Base = Df)")
        st.image(plan_img, caption="Footing Plan Top View with Dimensions & Rebar Layout")

        st.markdown("---")
        st.download_button(
            label="📄 Download Detailed Calculation PDF Report",
            data=pdf_file,
            file_name="Detailed_Footing_Design_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
