import io
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Continuous Wall Footing Design Suite", page_icon="🧱", layout="wide"
)
st.title("🧱 Continuous RC Wall Footing Design Suite")

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

    u_len = "ft" if is_imperial else "m"
    u_force_per_len = "kips/ft" if (is_imperial and not is_ton) else ("ton/ft" if is_imperial and is_ton else ("ton/m" if is_ton else "kN/m"))
    u_stress = "tsf" if (is_imperial and is_ton) else ("ksf" if is_imperial else ("t/m²" if is_ton else "kPa"))
    u_gamma = "pcf" if is_imperial else ("t/m³" if is_ton else "kN/m³")
    u_rebar = "in" if is_imperial else "mm"
    u_fc = "psi" if is_imperial else "MPa"

    col_p1, col_p2 = st.columns(2)
    P_dl = col_p1.number_input(f"Dead Load P_DL ({u_force_per_len})", 0.0, 5000.0, 100.0 if not is_imperial else 8.0)
    P_ll = col_p2.number_input(f"Live Load P_LL ({u_force_per_len})", 0.0, 5000.0, 50.0 if not is_imperial else 4.0)

    st.header("2. Geotechnical Soil Parameters Mode")
    geo_mode = st.radio(
        "Geotechnical Input Option",
        [
            "Direct Gross Allowable Soil Capacity (q_allow)",
            "c-phi Parameters (Analytical - Terzaghi/Meyerhof)",
            "SPT N-value (Empirical Method)",
        ]
    )

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

    st.header("3. Geometry & Water Table")
    col_g1, col_g2 = st.columns(2)
    b_wall = col_g1.number_input(f"Wall Thickness b_w ({u_len})", 0.1, 5.0, 0.25 if not is_imperial else 0.833)
    B = col_g2.number_input(f"Footing Width B ({u_len})", 0.5, 30.0, 1.8 if not is_imperial else 6.0)

    col_g3, col_g4 = st.columns(2)
    h_foot = col_g3.number_input(f"Footing Thickness h ({u_len})", 0.1, 5.0, 0.40 if not is_imperial else 1.25)
    Df = col_g4.number_input(f"Embedment Depth Df ({u_len})", 0.0, 20.0, 1.2 if not is_imperial else 4.0)

    col_s1, col_s2 = st.columns(2)
    gamma_soil = col_s1.number_input(f"Soil γ ({u_gamma})", 0.0, 300.0, 18.0 if not is_imperial else 115.0)
    Dw = col_s2.number_input(f"Water Table Depth Dw ({u_len})", 0.0, 50.0, 1.0 if not is_imperial else 3.5)

    st.header("4. Materials & Structural Details")
    aci_version = st.selectbox("ACI Standard Code", ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"])
    col_m1, col_m2 = st.columns(2)
    fc = col_m1.number_input(f"Concrete f'c ({u_fc})", 10.0, 10000.0, 28.0 if not is_imperial else 4000.0)
    fy = col_m2.number_input(f"Steel fy ({u_fc})", 100.0, 100000.0, 420.0 if not is_imperial else 60000.0)

    rebar_system = st.radio("Rebar Size Standard", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"])
    if "Metric" in rebar_system:
        main_rebar_opts = {"12 mm": {"dia": 12.0, "area": 113.1}, "16 mm": {"dia": 16.0, "area": 201.1}, "20 mm": {"dia": 20.0, "area": 314.2}}
        temp_rebar_opts = {"10 mm": {"dia": 10.0, "area": 78.5}, "12 mm": {"dia": 12.0, "area": 113.1}}
    else:
        main_rebar_opts = {"#4 (0.500 in)": {"dia": 0.500, "area": 0.20}, "#5 (0.625 in)": {"dia": 0.625, "area": 0.31}, "#6 (0.750 in)": {"dia": 0.750, "area": 0.44}}
        temp_rebar_opts = {"#3 (0.375 in)": {"dia": 0.375, "area": 0.11}, "#4 (0.500 in)": {"dia": 0.500, "area": 0.20}}

    col_r1, col_r2 = st.columns(2)
    selected_main_bar = col_r1.selectbox("Main Rebar (Transverse)", list(main_rebar_opts.keys()))
    selected_temp_bar = col_r2.selectbox("Distribution Steel (Longitudinal)", list(temp_rebar_opts.keys()))

    hook_type = st.radio("Main Rebar End Hook Type", ["None (Straight Bar)", "90-Degree Standard Hook", "180-Degree Standard Hook"])

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
        Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
        Rn = Mu_Nmm / (0.9 * b_mm * (d_mm_val**2))
        rho = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc))))
        As_main_req = max(rho, 0.0018) * b_mm * d_mm_val
        As_temp_req = 0.0018 * b_mm * (h_foot * 1000.0)
        spacing_unit = "mm"
    else:
        b_in, d_in_val = 12.0, d_eff * 12.0
        Mu_inlbs = Mu * 12000.0 * (2.0 if is_ton else 1.0)
        Rn = Mu_inlbs / (0.9 * b_in * (d_in_val**2))
        rho = (0.85 * fc / fy) * (1.0 - np.sqrt(max(0.0, 1.0 - (2.0 * Rn) / (0.85 * fc))))
        As_main_req = max(rho, 0.0018) * b_in * d_in_val
        As_temp_req = 0.0018 * b_in * (h_foot * 12.0)
        spacing_unit = "in"

    s_main = (main_rebar_opts[selected_main_bar]["area"] / As_main_req) * (1000.0 if not is_imperial else 12.0)
    s_temp = (temp_rebar_opts[selected_temp_bar]["area"] / As_temp_req) * (1000.0 if not is_imperial else 12.0)

    s_main_final = int(min(s_main, min(3 * h_foot * (1000.0 if not is_imperial else 12.0), 450.0 if not is_imperial else 18.0)))
    s_temp_final = int(min(s_temp, min(5 * h_foot * (1000.0 if not is_imperial else 12.0), 450.0 if not is_imperial else 18.0)))

    # Drawing with Correct 180 degree hook
    def draw_footing_section():
        fig, ax = plt.subplots(figsize=(7, 4.5))
        f_top, f_bottom = -Df, -Df - h_foot

        ax.fill_between([-B / 2 - 1.0, B / 2 + 1.0], [0, 0], [f_bottom - 0.4, f_bottom - 0.4], color="#E5D3B3", alpha=0.5)
        ax.add_patch(patches.Rectangle((-B / 2, f_bottom), B, h_foot, facecolor="#9CA3AF", edgecolor="black", linewidth=1.5))
        ax.add_patch(patches.Rectangle((-b_wall / 2, f_top), b_wall, Df + 0.4, facecolor="#4B5563", edgecolor="black", linewidth=1.5))

        main_y = f_bottom + cover
        left_x, right_x = -B / 2 + cover, B / 2 - cover
        ax.plot([left_x, right_x], [main_y, main_y], color="red", linewidth=2.5)

        hook_len = 0.12 if not is_imperial else 0.4
        if "90-Degree" in hook_type:
            ax.plot([left_x, left_x], [main_y, main_y + hook_len], color="red", linewidth=2.5)
            ax.plot([right_x, right_x], [main_y, main_y + hook_len], color="red", linewidth=2.5)
        elif "180-Degree" in hook_type:
            # Corrected Vertical Return
            ax.plot([left_x, left_x], [main_y, main_y + hook_len], color="red", linewidth=2.5)
            ax.plot([left_x, left_x + 0.03], [main_y + hook_len, main_y + hook_len], color="red", linewidth=2.5)
            ax.plot([left_x + 0.03, left_x + 0.03], [main_y + hook_len, main_y + 0.03], color="red", linewidth=2.5)

            ax.plot([right_x, right_x], [main_y, main_y + hook_len], color="red", linewidth=2.5)
            ax.plot([right_x, right_x - 0.03], [main_y + hook_len, main_y + hook_len], color="red", linewidth=2.5)
            ax.plot([right_x - 0.03, right_x - 0.03], [main_y + hook_len, main_y + 0.03], color="red", linewidth=2.5)

        dot_x_coords = np.linspace(left_x + 0.1, right_x - 0.1, 7)
        ax.scatter(dot_x_coords, [main_y + 0.03] * 7, color="darkblue", s=25, zorder=5)

        ax.set_xlim(-B / 2 - 0.8, B / 2 + 0.8)
        ax.set_ylim(f_bottom - 0.6, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        plt.title(f"Wall Footing Detailing ({hook_type})", fontsize=10, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return buf

    sec_img = draw_footing_section()

    with col_res:
        st.header("📊 Continuous Footing Results")
        st.subheader("1. Bearing Capacity Check")
        c1, c2 = st.columns(2)
        c1.metric("Service Soil Pressure", f"{q_service_actual:.2f} {u_stress}")
        c2.metric("Net Allowable Capacity", f"{q_net_allow:.2f} {u_stress}", delta="✅ SAFE" if q_service_actual <= q_net_allow else "❌ OVERLOADED")

        st.subheader("2. Structural Shear Check")
        st.metric("One-Way Shear (Vu / φVc)", f"{Vu_oneway:.2f} / {Phi_Vc:.2f} {u_force_per_len}", delta="✅ PASS" if Phi_Vc >= Vu_oneway else "❌ FAIL")

        st.subheader("3. Reinforcement Arrangement")
        st.markdown(f"• **Main Steel:** **{selected_main_bar} @ {s_main_final} {spacing_unit} c/c** ({hook_type})")
        st.markdown(f"• **Temp Steel:** **{selected_temp_bar} @ {s_temp_final} {spacing_unit} c/c**")

        st.image(sec_img, caption="Cross-Section Diagram")
