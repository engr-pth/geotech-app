import io
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# Page Configuration Setup
st.set_page_config(
    page_title="RC Wall Footing Design", page_icon="🧱", layout="wide"
)
st.title("🧱 Reinforced Concrete Wall Footing Design Suite")
st.caption(
    "Design of Strip/Continuous Footing under Wall Load per ACI 318 Standard"
)

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

    # Unit Labels
    u_len = "ft" if is_imperial else "m"
    u_force_per_m = (
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

    st.header("2. Applied Wall Loads (Per Unit Length)")
    P_dl = st.number_input(
        f"Dead Load P_DL ({u_force_per_m})",
        0.0,
        5000.0,
        100.0 if not is_imperial else 8.0,
    )
    P_ll = st.number_input(
        f"Live Load P_LL ({u_force_per_m})",
        0.0,
        5000.0,
        50.0 if not is_imperial else 4.0,
    )

    st.header("3. Geometry & Soil Parameters")
    b_wall = st.number_input(
        f"Wall Thickness ({u_len})",
        0.1,
        5.0,
        0.25 if not is_imperial else 0.833,
    )
    B = st.number_input(
        f"Footing Width B ({u_len})", 0.5, 20.0, 1.5 if not is_imperial else 5.0
    )
    h_foot = st.number_input(
        f"Footing Thickness h ({u_len})",
        0.1,
        5.0,
        0.35 if not is_imperial else 1.0,
    )
    Df = st.number_input(
        f"Embedment Depth Df ({u_len})",
        0.0,
        10.0,
        1.0 if not is_imperial else 3.0,
    )

    gamma_soil = st.number_input(
        f"Soil Unit Weight γ ({u_gamma})",
        0.0,
        300.0,
        18.0 if not is_imperial else 115.0,
    )
    q_allow = st.number_input(
        f"Allowable Soil Bearing Capacity q_allow ({u_stress})",
        1.0,
        10000.0,
        150.0 if not is_imperial else 3.0,
    )

    st.header("4. Material & Rebar Selection")
    aci_version = st.selectbox(
        "ACI Standard Code",
        ["ACI 318-22", "ACI 318-19", "ACI 318-14", "ACI 318-11"],
    )
    fc = st.number_input(
        f"Concrete Strength f'c ({u_fc})",
        10.0,
        10000.0,
        24.0 if not is_imperial else 3000.0,
    )
    fy = st.number_input(
        f"Steel Yield Strength fy ({u_fc})",
        100.0,
        100000.0,
        420.0 if not is_imperial else 60000.0,
    )

    rebar_system = st.radio(
        "Rebar Size System", ["Metric Sizes (mm)", "Imperial Sizes (# / in)"]
    )
    if "Metric" in rebar_system:
        rebar_options = {
            "12 mm": {"dia": 12.0, "area": 113.1, "is_metric": True},
            "16 mm": {"dia": 16.0, "area": 201.1, "is_metric": True},
            "20 mm": {"dia": 20.0, "area": 314.2, "is_metric": True},
        }
    else:
        rebar_options = {
            "#4 (0.500 in)": {"dia": 0.500, "area": 0.20, "is_metric": False},
            "#5 (0.625 in)": {"dia": 0.625, "area": 0.31, "is_metric": False},
            "#6 (0.750 in)": {"dia": 0.750, "area": 0.44, "is_metric": False},
        }

    selected_rebar = st.selectbox(
        "Select Transverse Rebar", list(rebar_options.keys())
    )
    bar_tolerance = st.number_input(
        "Market Bar Tolerance Loss (%)", 0.0, 15.0, 0.0, step=0.5
    )

    calc_trigger = st.button(
        "🚀 Calculate Wall Footing", type="primary", use_container_width=True
    )

# --- Calculation Engine ---
if calc_trigger or "wall_calc" in st.session_state:
    st.session_state["wall_calc"] = True

    # 1. Service Loads & Net Allowable Bearing Capacity
    gamma_conc = 24.0 if not is_imperial else (2.4 if is_ton else 150.0)
    if is_ton and not is_imperial:
        gamma_conc = 2.4

    surcharge = (Df * gamma_soil) + (h_foot * gamma_conc)
    q_net_allow = q_allow - surcharge

    P_service = P_dl + P_ll
    q_service_actual = P_service / B

    # 2. Ultimate Strength Design (Factored Loads)
    Pu = (1.2 * P_dl) + (1.6 * P_ll)
    qu_factored = Pu / B  # Uniform pressure across footing

    # 3. Structural Shear Check (One-Way Shear at d from Wall Face)
    cover = 0.075 if not is_imperial else (3.0 / 12.0)  # Standard 3 inches
    d_eff = h_foot - cover

    cantilever_arm = (B - b_wall) / 2.0
    crit_shear_dist = cantilever_arm - d_eff

    Vu_oneway = qu_factored * max(0.0, crit_shear_dist)

    # Size effect factor λs
    if aci_version in ["ACI 318-19", "ACI 318-22"]:
        d_mm = d_eff * 1000 if not is_imperial else d_eff * 12 * 25.4
        lambda_s = min(1.0, np.sqrt(2 / (1 + 0.004 * d_mm)))
    else:
        lambda_s = 1.0

    phi_shear = 0.75
    if not is_imperial:
        vc = 0.17 * lambda_s * np.sqrt(fc)
        mult = 1.0 / 9.81 if is_ton else 1.0
        Phi_Vc = phi_shear * vc * (1.0 * 1000) * (d_eff * 1000) / 1000.0 * mult
    else:
        vc = 2.0 * lambda_s * np.sqrt(fc)
        mult = 0.5 if is_ton else 1.0
        Phi_Vc = phi_shear * vc * (12.0) * (d_eff * 12.0) / 1000.0 * mult

    # 4. Moment & Flexural Design (At Wall Face)
    Mu = (qu_factored * (cantilever_arm**2)) / 2.0

    if not is_imperial:
        b_mm, d_mm_val = 1000.0, d_eff * 1000.0
        Mu_Nmm = Mu * 1e6 * (9.81 if is_ton else 1.0)
        Rn = Mu_Nmm / (0.9 * b_mm * (d_mm_val**2))
        rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
        rho_req = max(rho, 0.0018)
        As_req = rho_req * b_mm * d_mm_val  # mm²/m
        area_unit = "mm²/m"
        spacing_unit = "mm"
    else:
        b_in, d_in_val = 12.0, d_eff * 12.0
        Mu_inlbs = Mu * 12000.0 * (2.0 if is_ton else 1.0)
        Rn = Mu_inlbs / (0.9 * b_in * (d_in_val**2))
        rho = (0.85 * fc / fy) * (1 - np.sqrt(max(0.0, 1 - (2 * Rn) / (0.85 * fc))))
        rho_req = max(rho, 0.0018)
        As_req = rho_req * b_in * d_in_val  # in²/ft
        area_unit = "in²/ft"
        spacing_unit = "in"

    # Rebar Spacing Calculation
    nom_area = rebar_options[selected_rebar]["area"]
    actual_area = nom_area * (1.0 - (bar_tolerance / 100.0))

    if "Metric" in rebar_system:
        spacing = (actual_area / As_req) * 1000.0
    else:
        spacing = (actual_area / As_req) * 12.0

    spacing = min(int(spacing), 450 if not is_imperial else 18)

    # Cross-Section Visual Drawing
    def draw_wall_footing():
        fig, ax = plt.subplots(figsize=(6, 4))
        # Soil Background
        ax.fill_between(
            [-B / 2 - 0.5, B / 2 + 0.5],
            [0, 0],
            [-Df - h_foot - 0.2, -Df - h_foot - 0.2],
            color="#E5D3B3",
            alpha=0.5,
        )

        # Footing & Wall
        ax.add_patch(
            plt.Rectangle(
                (-B / 2, -Df - h_foot),
                B,
                h_foot,
                facecolor="#9CA3AF",
                edgecolor="black",
                linewidth=1.5,
            )
        )
        ax.add_patch(
            plt.Rectangle(
                (-b_wall / 2, -Df),
                b_wall,
                Df + 0.4,
                facecolor="#4B5563",
                edgecolor="black",
                linewidth=1.5,
            )
        )

        # Rebar
        rebar_y = -Df - h_foot + cover
        ax.plot(
            [-B / 2 + cover, B / 2 - cover],
            [rebar_y, rebar_y],
            color="red",
            linewidth=2.5,
            label="Transverse Steel",
        )
        ax.scatter(
            np.linspace(-B / 2 + cover, B / 2 - cover, 5),
            [rebar_y + 0.03] * 5,
            color="blue",
            s=20,
            zorder=5,
            label="Temperature Steel",
        )

        ax.set_xlim(-B / 2 - 0.5, B / 2 + 0.5)
        ax.set_ylim(-Df - h_foot - 0.3, 0.5)
        ax.set_aspect("equal")
        ax.axis("off")
        plt.title(
            "Continuous RC Wall Footing Structural Cross-Section",
            fontsize=9,
            fontweight="bold",
        )
        plt.tight_layout()
        return fig

    # Output Presentation
    with col_res:
        st.header("📊 Design Verification & Results")

        st.subheader("1. Bearing Capacity Check")
        st.write(
            f"Actual Service Pressure (q_service): `{q_service_actual:.2f} {u_stress}`"
        )
        st.write(
            f"Net Allowable Capacity (q_net_allow): `{q_net_allow:.2f} {u_stress}`"
        )
        if q_service_actual <= q_net_allow:
            st.success("✅ Bearing Capacity Pass")
        else:
            st.error("❌ Soil Overloaded! Increase Footing Width (B)")

        st.subheader("2. One-Way Beam Shear Check")
        st.write(
            f"Ultimate Shear Vu: `{Vu_oneway:.2f} {u_force_per_m}` | Capacity φVc: `{Phi_Vc:.2f} {u_force_per_m}`"
        )
        if Phi_Vc >= Vu_oneway:
            st.success("✅ One-Way Shear Capacity Pass")
        else:
            st.error("❌ Shear Failure! Increase Thickness (h)")

        st.subheader("3. Reinforcement Detail")
        st.markdown(
            f"Required Reinforcement Steel: `{As_req:.2f} {area_unit}`"
        )
        st.info(
            f"**Provide Main Bar:** **{selected_rebar} @ {spacing} {spacing_unit} c/c** (Bottom Transverse Rebar)"
        )

        st.pyplot(draw_wall_footing())
