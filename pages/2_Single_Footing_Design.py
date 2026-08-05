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

    # --- Geotechnical Inputs based on selected Mode ---
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
    B = col_b.number_input(f"Footing Width B ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)
    L = col_l.number_input(f"Footing Length L ({u_len})", 0.5, 50.0, 1.8 if not is_imperial else 6.0)

    # Column Shape Selection
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

    Df = st.number_input(f"Embedment Depth Df ({u_len})", 0.0, 20.0, 1.0 if not is_imperial else 3.5)
    h_foot = st.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 0.45 if not is_imperial else 1.5)
    Dw = st.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 1.5 if not is_imperial else 5.0)

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

    clear_cover_input = st.selectbox("Clear Concrete Cover", ["3.0 inches (75 mm) - Standard Footing Cover"], index=0)
    hook_type = st.radio("Rebar End Hook Type", ["None (Straight Bar)", "90-Degree Standard Hook", "180-Degree Standard Hook"])

    nom_area = rebar_options[selected_rebar]["area"]
    actual_area = nom_area * (1.0 - (bar_tolerance_pct / 100.0))
    is_selected_metric = rebar_options[selected_rebar]["is_metric"]

    calc_trigger = st.button("🚀 Calculate Single Footing Design", type="primary", use_container_width=True)

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

    # 3. Geotechnical Bearing Capacity Calculation
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

    # 4. Structural Design Calculations (Factored DL & LL)
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

    # Punching Shear Perimeter adjustment for Circular Column
    if col_shape == "Circular":
        bo = np.pi * (D_col + d_eff)
        Area_bo = (np.pi / 4.0) * ((D_col + d_eff) ** 2)
        cantilever_max = max((B / 2.0) - (0.886 * D_col / 2.0) + ex_input, (B / 2.0) - (0.886 * D_col / 2.0) - ex_input)
    else:
        bo = 2 * ((cx + d_eff) + (cy + d_eff))
        Area_bo = (cx + d_eff) * (cy + d_eff)
        cantilever_max = max((B / 2.0) - (cx / 2.0) + ex_input, (B / 2.0) - (cx / 2.0) - ex_input)

    Vu_punch = qu_factored * (footing_area - Area_bo)
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

    # --- Drawing Logic (Corrected 180 degree hook) ---
    def draw_cross_section():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        f_bottom = -Df - h_foot
        ax.fill_between([-B / 2 - 1.2, B / 2 + 1.2], [0, 0], [f_bottom - 0.5, f_bottom - 0.5], color="#E5D3B3", alpha=0.5)
        ax.axhline(0, color="k", linestyle="--", linewidth=1, label="Ground Level")
        ax.add_patch(plt.Rectangle((-B / 2, f_bottom), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5, label="Footing"))

        col_x_start = ex_input - (cx / 2.0)
        if col_shape == "Circular":
            ax.add_patch(plt.Rectangle((col_x_start, -Df), cx, Df + 0.3, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Circular Col (Sec)"))
        else:
            ax.add_patch(plt.Rectangle((col_x_start, -Df), cx, Df + 0.3, facecolor="#4B5563", edgecolor="black", linewidth=1.5, label="Column"))

        rebar_y_xdir = f_bottom + cover
        left_x = -B / 2 + cover
        right_x = B / 2 - cover
        ax.plot([left_x, right_x], [rebar_y_xdir, rebar_y_xdir], color="red", linewidth=2.0, label=f"Bar: {num_bars}-{selected_rebar}")

        hook_len = 0.12 if not is_imperial else 0.4
        if "90-Degree" in hook_type:
            ax.plot([left_x, left_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x, right_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
        elif "180-Degree" in hook_type:
            # Corrected Vertical U-Turn Hook
            ax.plot([left_x, left_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([left_x, left_x + 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([left_x + 0.03, left_x + 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + 0.03], color="red", linewidth=2.0)

            ax.plot([right_x, right_x], [rebar_y_xdir, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x, right_x - 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + hook_len], color="red", linewidth=2.0)
            ax.plot([right_x - 0.03, right_x - 0.03], [rebar_y_xdir + hook_len, rebar_y_xdir + 0.03], color="red", linewidth=2.0)

        x_coords = np.linspace(left_x, right_x, num_bars)
        ax.scatter(x_coords, [rebar_y_xdir + 0.02] * num_bars, color="darkblue", s=15, zorder=5)

        ax.set_xlim(-B / 2 - 1.0, B / 2 + 1.0)
        ax.set_ylim(f_bottom - 0.7, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.legend(loc="upper right", fontsize=6.5)
        plt.title(f"Elevation Section ({hook_type})", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    def draw_plan_view():
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.add_patch(patches.Rectangle((-B / 2, -L / 2), B, L, facecolor="#D1D5DB", edgecolor="black", linewidth=1.5))

        if col_shape == "Circular":
            ax.add_patch(patches.Circle((ex_input, ey_input), radius=D_col / 2.0, facecolor="#374151", edgecolor="black", linewidth=1.5))
        else:
            col_x_min = ex_input - (cx / 2.0)
            col_y_min = ey_input - (cy / 2.0)
            ax.add_patch(patches.Rectangle((col_x_min, col_y_min), cx, cy, facecolor="#374151", edgecolor="black", linewidth=1.5))

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(-L / 2 - 0.8, L / 2 + 0.8)
        ax.set_aspect("equal")
        ax.axis("off")
        plt.title("Footing Plan Top View", fontsize=9, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    # Render Outputs
    sec_img = draw_cross_section()
    plan_img = draw_plan_view()

    with col_res:
        st.header("📊 Results & Verification Summary")
        st.subheader("1. Eccentricity & Soil Pressure")
        st.metric("Total Unfactored P", f"{P_unfactored:.2f} {u_force} (DL: {P_DL}, LL: {P_LL})")
        st.metric("Max Pressure (q_max)", f"{q_max_service:.2f} {u_stress}", delta="✅ OK" if q_max_service <= q_allow else "❌ OVERLOADED")

        st.subheader("2. Structural Shears Check")
        s1, s2 = st.columns(2)
        s1.metric("Punching Shear", f"{Vu_punch:.1f} / {Phi_Vc_punch:.1f}", delta="✅ PASS" if Phi_Vc_punch >= Vu_punch else "❌ FAIL")
        s2.metric("One-Way Shear", f"{Vu_oneway:.1f} / {Phi_Vc_oneway:.1f}", delta="✅ PASS" if Phi_Vc_oneway >= Vu_oneway else "❌ FAIL")

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(f"**Design Recommendation:** Provide **{num_bars} Nos - {selected_rebar}** with **{hook_type}** @ **{spacing} {spacing_unit} c/c**")

        st.image(sec_img, caption="Cross-Section Elevation")
        st.image(plan_img, caption="Plan View")
