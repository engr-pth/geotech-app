import io
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Geotechnical Suite",
    page_icon="🪨",
    layout="wide"
)

# ==========================================
# 0. AUTOMATIC SOIL CLASSIFICATION FUNCTION
# ==========================================
def classify_soil(soil_type: str, n_spt: float) -> str:
    if soil_type == "cohesionless":
        if n_spt <= 4: return "Very Loose Sand"
        elif n_spt <= 10: return "Loose Sand"
        elif n_spt <= 30: return "Medium Dense Sand"
        elif n_spt <= 50: return "Dense Sand"
        else: return "Very Dense Sand"
    else: # cohesive
        if n_spt <= 2: return "Very Soft Clay"
        elif n_spt <= 4: return "Soft Clay"
        elif n_spt <= 8: return "Medium Stiff Clay"
        elif n_spt <= 16: return "Stiff Clay"
        elif n_spt <= 32: return "Very Stiff Clay"
        elif n_spt <= 50: return "Hard Clay"
        else: return "Very Hard Clay"

def reset_calc():
    st.session_state.calculated = False

with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Soil Classification", "Isolated Footing", "Continuous Wall Footing", "Deep Foundation (Bored Pile)"],
        icons=["house-fill", "journal-text", "square-fill", "border-style", "layers-fill"],
        default_index=0,
        key="main_menu_nav"
    )

if selected == "Home":
    st.title("🧱 Geotechnical Engineering Calculation Suite")
    st.markdown("""
    ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

    👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
    * **Soil Classification:** Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲရန်
    * **Shallow Foundation Design:** Isolated Footing နှင့် Continuous Wall Footing တွက်ချက်ရန်
    * **Deep Foundation (Bored Pile):** Bored Pile Capacity နှင့် Structural/Geotechnical Design တွက်ချက်ရန်
    """)

elif selected == "Soil Classification":
    st.title("🧪 Soil Classification Tool")
    st.info("Soil Classification Module (USCS, AASHTO, BS 5930, IS 1498)")

elif selected == "Isolated Footing":
    st.title("📐 Isolated Footing Design")
    st.info("Isolated Footing Design Module")

elif selected == "Continuous Wall Footing":
    st.title("🧱 Continuous Wall Footing Design Suite")
    st.info("Continuous Wall Footing Design Module")

elif selected == "Deep Foundation (Bored Pile)":
    # Header Title & Author Attribution
    st.title("🏗️ Bored Pile Capacity Calculator")
    st.markdown(
        "<p style='font-size: 1.1rem; margin-top: -10px; margin-bottom: 10px;'>"
        "<b>Designed & Developed by:</b> Engr. Phyo Thi Han, BE(Civil), ME(Civil Geotechnical), RE(Construction, Geotechnical & Structural)"
        "</p>",
        unsafe_allow_html=True
    )

    # Engineering Disclaimer Notice
    st.warning("⚠️ **Disclaimer:** ယခုတွက်ချက်မှုများသည် preliminary design အတွက်သာ ရည်ရွယ်ပါသည်။ ရရှိလာသောအဖြေများကို သက်ဆိုင်ရာ Building Code နှင့် Engineering Judgement တို့ဖြင့် တိုက်ဆိုင်စစ်ဆေးရမည်ဖြစ်ပါသည်။")

    # Session State Initializations
    if "soil_layers" not in st.session_state:
        st.session_state.soil_layers = [
            {"Soil Name": "Clay", "Thickness": 2.0, "N_SPT": 10.0, "Gamma": 17.0, "Liquefiable": False},
            {"Soil Name": "Clay", "Thickness": 1.5, "N_SPT": 12.0, "Gamma": 17.5, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 1.5, "N_SPT": 8.0, "Gamma": 18.0, "Liquefiable": True},
            {"Soil Name": "Sand", "Thickness": 1.5, "N_SPT": 14.0, "Gamma": 18.5, "Liquefiable": False},
            {"Soil Name": "Clay", "Thickness": 1.5, "N_SPT": 16.0, "Gamma": 18.0, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 1.5, "N_SPT": 19.0, "Gamma": 19.0, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 3.0, "N_SPT": 20.0, "Gamma": 19.0, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 3.0, "N_SPT": 21.0, "Gamma": 19.5, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 3.0, "N_SPT": 23.0, "Gamma": 19.5, "Liquefiable": False},
            {"Soil Name": "Clay", "Thickness": 3.0, "N_SPT": 52.0, "Gamma": 20.0, "Liquefiable": False},
            {"Soil Name": "Clay", "Thickness": 3.0, "N_SPT": 48.0, "Gamma": 20.0, "Liquefiable": False},
            {"Soil Name": "Clay", "Thickness": 3.0, "N_SPT": 40.0, "Gamma": 20.0, "Liquefiable": False},
            {"Soil Name": "Sand", "Thickness": 3.0, "N_SPT": 68.0, "Gamma": 20.5, "Liquefiable": False}
        ]

    if "calculated" not in st.session_state:
        st.session_state.calculated = False

    if "delete_stage" not in st.session_state:
        st.session_state.delete_stage = {}

    st.info("ℹ️ ကျေးဇူးပြု၍ အောက်ပါနေရာများတွင် Pile Parameters၊ Structural Code၊ GWT နှင့် Soil Layers များကို ထည့်သွင်းပြီး '🚀 Design Pile' ခလုတ်ကို နှိပ်ပါ။")

    # ==========================================
    # 1. PILE & MATERIAL PARAMETERS INPUT
    # ==========================================
    st.header("1. General, Material & Pile Parameters (အထွေထွေနှင့် ပိုင်တိုင် ကန့်သတ်ချက်များ)")

    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    with col_p1:
        pile_diameter = st.number_input("Pile Diameter (m) - ပိုင်တိုင် အချင်း", value=0.50, step=0.05, on_change=reset_calc)
    with col_p2:
        fs_factor = st.number_input("Geotech FS - ဘေးကင်းကိန်း", value=2.00, step=0.10, on_change=reset_calc)
    with col_p3:
        target_capacity = st.number_input("Target Q_allow (ton) - လိုအပ်သော ဝန်ထမ်းအား", value=100.00, step=10.0, on_change=reset_calc)
    with col_p4:
        step = st.number_input("Calculation Step (m) - တွက်ချက်မည့် အလွှာအထူ အတိုင်းအတာ", value=0.50, step=0.1, on_change=reset_calc)
    with col_p5:
        gwt_depth = st.number_input("GWT Depth (m) - ရေမျက်နှာပြင် အနက်", value=2.00, step=0.5, min_value=0.0, on_change=reset_calc)

    st.subheader("RC Structural Parameters & Standard Code (ကွန်ကရစ် တည်ဆောက်ပုံဆိုင်ရာ ကန့်သတ်ချက်များ)")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    with col_s1:
        aci_version = st.selectbox("Structural Code - ဒီဇိုင်းကုဒ်", ["ACI 318-19", "ACI 318-14", "ACI 318-11"], index=0, on_change=reset_calc)
    with col_s2:
        fc_prime = st.number_input("Concrete f'c (MPa) - ကွန်ကရစ် ခိုင်ခံ့အား", value=25.0, step=1.0, on_change=reset_calc)
    with col_s3:
        fy_rebar = st.number_input("Steel fy (MPa) - သံချောင်း ခိုင်ခံ့အား", value=400.0, step=10.0, on_change=reset_calc)
    with col_s4:
        rebar_ratio_pct = st.number_input("Steel Ratio ρ (%) - သံချောင်းပါဝင်မှု ရာခိုင်နှုန်း", value=1.0, step=0.1, min_value=0.5, max_value=4.0, on_change=reset_calc)
    with col_s5:
        phi_structural = st.number_input("Strength Factor (ϕ) - လျှော့ချကိန်း", value=0.75, step=0.05, help="Spiral = 0.75, Tied = 0.65", on_change=reset_calc)

    st.markdown("---")

    # ==========================================
    # 2. SOIL STRATIGRAPHY INPUT WITH soil-scroll-wrapper
    # ==========================================
    st.header("2. Soil Stratigraphy Input (မြေအလွှာဖွဲ့စည်းပုံ အချက်အလက်များ)")

    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .soil-scroll-wrapper {
            width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch !important;
            padding-bottom: 15px !important;
            margin-bottom: 10px !important;
        }
        .soil-scroll-wrapper div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            min-width: 720px !important;
            width: 720px !important;
        }
        .soil-scroll-wrapper div[data-testid="column"] {
            flex: 1 0 auto !important;
            min-width: 110px !important;
            max-width: none !important;
            width: auto !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="soil-scroll-wrapper">', unsafe_allow_html=True)

    h1, h2_col, h3, h4, h5, h6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.5, 1.0])
    with h1: st.markdown("**Soil Name**\n*(မြေအမျိုးအစား)*")
    with h2_col: st.markdown("**Thickness (m)**\n*(အထူ)*")
    with h3: st.markdown("**N_SPT**\n*(စံချိန်စံညွှန်း)*")
    with h4: st.markdown("**Unit Wt. γ**\n*(kN/m³)*")
    with h5: st.markdown("**Liquefiable**\n*(မြေပျော့ပြိုလဲမှု)*")
    with h6: st.markdown("**Action**\n*(လုပ်ဆောင်ချက်)*")

    st.markdown("---")

    index_to_remove = None

    for i, layer in enumerate(st.session_state.soil_layers):
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.5, 1.0])
        
        with c1:
            s_name = st.selectbox("Soil Name", ["Clay", "Sand"], index=0 if layer["Soil Name"] == "Clay" else 1, key=f"s_name_{i}", label_visibility="collapsed", on_change=reset_calc)
            st.session_state.soil_layers[i]["Soil Name"] = s_name
            
        with c2:
            thick = st.number_input("Thickness", min_value=0.1, value=float(layer["Thickness"]), step=0.5, key=f"thick_{i}", label_visibility="collapsed", on_change=reset_calc)
            st.session_state.soil_layers[i]["Thickness"] = thick
            
        with c3:
            n_spt = st.number_input("N_SPT", min_value=0.0, value=float(layer["N_SPT"]), step=1.0, key=f"n_spt_{i}", label_visibility="collapsed", on_change=reset_calc)
            st.session_state.soil_layers[i]["N_SPT"] = n_spt
            
        with c4:
            gamma_val = st.number_input("Gamma", min_value=10.0, max_value=25.0, value=float(layer.get("Gamma", 18.0)), step=0.5, key=f"gamma_{i}", label_visibility="collapsed", on_change=reset_calc)
            st.session_state.soil_layers[i]["Gamma"] = gamma_val
            
        with c5:
            liq = st.checkbox("Liquefiable", value=bool(layer["Liquefiable"]), key=f"liq_{i}", on_change=reset_calc)
            st.session_state.soil_layers[i]["Liquefiable"] = liq
            
        with c6:
            stage = st.session_state.delete_stage.get(i, "init")
            if stage == "init":
                if st.button("🗑️", key=f"del_btn_{i}", help="ဖျက်မည်"):
                    st.session_state.delete_stage[i] = "delete_shown"
                    st.rerun()
            elif stage == "delete_shown":
                if st.button("သေချာ?", key=f"del_txt_{i}"):
                    st.session_state.delete_stage[i] = "confirm_shown"
                    st.rerun()
            elif stage == "confirm_shown":
                if st.button("Yes", key=f"conf_btn_{i}", type="primary"):
                    index_to_remove = i

    st.markdown("</div>", unsafe_allow_html=True)

    if index_to_remove is not None:
        st.session_state.soil_layers.pop(index_to_remove)
        st.session_state.delete_stage = {}
        st.session_state.calculated = False
        st.rerun()

    b_col1, b_col2 = st.columns([2, 4])
    with b_col1:
        if st.button("➕ Add Soil Layer (မြေအလွှာ အသစ်ထပ်ရန်)", use_container_width=True):
            st.session_state.soil_layers.append({"Soil Name": "Clay", "Thickness": 1.5, "N_SPT": 10.0, "Gamma": 18.0, "Liquefiable": False})
            st.session_state.calculated = False
            st.rerun()

    total_thickness = sum([float(l["Thickness"]) for l in st.session_state.soil_layers])
    st.metric(label="📊 Total Soil Thickness (စုစုပေါင်း မြေအလွှာအထူ)", value=f"{total_thickness:.2f} m")

    st.markdown("---")

    # ==========================================
    # DESIGN BUTTON
    # ==========================================
    if st.button("🚀 Design Pile (ပိုင်တိုင် ဒီဇိုင်း စတင်တွက်မည်)", type="primary", use_container_width=True):
        if len(st.session_state.soil_layers) == 0:
            st.error("Soil Layer နည်းဆုံး ၁ ခု ထည့်ပေးပါရန်!")
            st.session_state.calculated = False
        else:
            st.session_state.calculated = True

    # ==========================================
    # 3. CALCULATION & REPORT DISPLAY
    # ==========================================
    if st.session_state.calculated and len(st.session_state.soil_layers) > 0:
        st.markdown("---")
        st.header("3. Design Report & Output (ဒီဇိုင်း အစီရင်ခံစာနှင့် ရလဒ်များ)")

        # --- A. STRUCTURAL CAPACITY CALCULATION ---
        A_g = (np.pi / 4.0) * (pile_diameter ** 2)
        A_st = (rebar_ratio_pct / 100.0) * A_g
        A_c = A_g - A_st

        K_alpha = 0.85
        P_n_max_kN = K_alpha * (0.85 * (fc_prime * 1e3) * A_c + (fy_rebar * 1e3) * A_st)
        P_design_comp_kN = phi_structural * P_n_max_kN
        P_design_comp_ton = P_design_comp_kN / 9.80665

        P_n_tensile_kN = A_st * (fy_rebar * 1e3)
        P_design_tensile_ton = (0.90 * P_n_tensile_kN) / 9.80665

        struct_allow_service_ton = P_design_comp_ton / 1.4

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Gross Section Area (Ag)", f"{A_g:.3f} m²")
        sc2.metric("Steel Area (Ast)", f"{(A_st * 1e4):.1f} cm² ({rebar_ratio_pct}%)")
        sc3.metric(f"Structural Capacity ({aci_version})", f"{P_design_comp_ton:.1f} ton", help=f"Design strength ϕPn per {aci_version}")
        sc4.metric("Structural Tension Capacity", f"{P_design_tensile_ton:.1f} ton")

        # --- B. GEOTECHNICAL CAPACITY CALCULATION ---
        soil_profile = []
        for row in st.session_state.soil_layers:
            s_name_input = str(row["Soil Name"])
            s_type = "cohesive" if "Clay" in s_name_input else "cohesionless"
            n_val = float(row["N_SPT"])
            thick_val = float(row["Thickness"])
            gamma_val = float(row.get("Gamma", 18.0))
            liq_val = bool(row["Liquefiable"])
            
            classified_name = classify_soil(s_type, n_val)
            soil_profile.append({
                "Thickness": thick_val, "Type": s_type, "N_SPT": n_val, 
                "Gamma": gamma_val, "Liquefiable": liq_val, "Name": classified_name
            })

        max_depth = sum([float(layer["Thickness"]) for layer in soil_profile if float(layer["Thickness"]) > 0])
        if max_depth <= 0: max_depth = 30.5

        perimeter = np.pi * pile_diameter
        base_area = A_g
        depths = np.arange(step, max_depth + step / 2, step)
        gamma_w = 9.81

        results = []
        req_depth = None

        for d in depths:
            eff_stress_tip = 0.0
            curr_z = 0.0
            for layer in soil_profile:
                thick = float(layer["Thickness"])
                gamma = float(layer["Gamma"])
                l_top = curr_z
                l_bot = curr_z + thick
                if d > l_top:
                    slice_thick = min(d, l_bot) - l_top
                    slice_top = l_top
                    slice_bot = l_top + slice_thick
                    if slice_bot <= gwt_depth:
                        eff_stress_tip += gamma * slice_thick
                    elif slice_top >= gwt_depth:
                        eff_stress_tip += (gamma - gamma_w) * slice_thick
                    else:
                        dry_part = gwt_depth - slice_top
                        sub_part = slice_bot - gwt_depth
                        eff_stress_tip += gamma * dry_part + (gamma - gamma_w) * sub_part
                curr_z = l_bot

            current_depth = 0.0
            total_qs = 0.0
            for layer in soil_profile:
                thick = float(layer["Thickness"])
                l_type = str(layer["Type"])
                n_spt = float(layer["N_SPT"])
                liq = bool(layer["Liquefiable"])
                layer_top = current_depth
                layer_bottom = current_depth + thick

                if d > layer_top:
                    eff_thick = min(d, layer_bottom) - layer_top
                    mid_depth = layer_top + eff_thick / 2.0
                    if liq:
                        f_s = 0.0
                    else:
                        if l_type == "cohesive":
                            cu = 6.25 * n_spt
                            alpha = 0.55 if cu <= 60 else max(0.35, 0.55 - 0.005 * (cu - 60))
                            f_s = alpha * cu
                        else:
                            beta = max(0.25, 1.5 - 0.245 * np.sqrt(mid_depth))
                            f_s_beta = beta * eff_stress_tip
                            f_s_spt = 2.0 * n_spt
                            f_s = min(f_s_spt, f_s_beta, 100.0)
                        f_s = min(f_s, 150.0)
                    total_qs += f_s * perimeter * eff_thick
                current_depth = layer_bottom

            tip_layer = soil_profile[-1] if len(soil_profile) > 0 else {"Type": "cohesionless", "N_SPT": 10, "Liquefiable": False}
            current_depth = 0.0
            for layer in soil_profile:
                current_depth += float(layer["Thickness"])
                if round(d, 4) <= round(current_depth, 4):
                    tip_layer = layer
                    break

            if bool(tip_layer["Liquefiable"]):
                q_b = 0.0
            else:
                tip_n = float(tip_layer["N_SPT"])
                if str(tip_layer["Type"]) == "cohesive":
                    cu_tip = 6.25 * tip_n
                    q_b = 9.0 * cu_tip
                else:
                    q_b_spt = 40.0 * tip_n
                    q_b_eff = 3.0 * tip_n * eff_stress_tip / 100.0 if eff_stress_tip > 0 else q_b_spt
                    q_b = min(q_b_spt, q_b_eff, 4000.0)
                q_b = min(q_b, 5000.0)

            end_bearing = q_b * base_area
            ultimate = total_qs + end_bearing
            allowable = ultimate / fs_factor

            qs_ton = total_qs / 9.80665
            qb_ton = end_bearing / 9.80665
            qu_ton = ultimate / 9.80665
            qa_ton = allowable / 9.80665

            if qa_ton <= struct_allow_service_ton:
                governing_mode = "Geotechnical"
                governing_capacity = qa_ton
            else:
                governing_mode = "Structural"
                governing_capacity = struct_allow_service_ton

            if req_depth is None and qa_ton >= target_capacity and qa_ton <= struct_allow_service_ton:
                req_depth = d

            results.append({
                "Depth (m)": round(d, 2), "Eff. Stress (kPa)": round(eff_stress_tip, 1),
                "Cum. Qs (ton)": round(qs_ton, 2), "Qb (ton)": round(qb_ton, 2),
                "Qu Geotech (ton)": round(qu_ton, 2), "Q_allow Geotech (ton)": round(qa_ton, 2),
                "Governing Capacity (ton)": round(governing_capacity, 2), "Governing Mode": governing_mode
            })

        df_res = pd.DataFrame(results)

        if P_design_comp_ton < (target_capacity * fs_factor):
            st.warning(f"⚠️ သတိပေးချက်: Pile Section ရဲ့ Structural Capacity ({aci_version}, $\\phi P_n$ = {P_design_comp_ton:.1f} ton) သည် Target Ultimate Load ထက် နည်းနေပါသည်။")

        # ==========================================
        # 4. MATPLOTLIB REPORT GENERATION
        # ==========================================
        fig, (ax0, ax1, ax2, ax3) = plt.subplots(1, 4, figsize=(28, 11), dpi=350, gridspec_kw={'width_ratios': [1.1, 1.0, 1.0, 1.6]})

        fig.suptitle(
            f"Bored Pile Design Report & Governing Check ({aci_version}, Dia = {pile_diameter}m, f'c = {fc_prime}MPa)\nDesigned & Developed by: Engr. Phyo Thi Han, BE(Civil), ME(Civil Geotechnical), RE(Construction, Geotechnical & Structural)",
            fontsize=16, fontweight="bold", y=0.96
        )

        current_d = 0.0
        y_ticks = [0.0]
        for layer in soil_profile:
            thick = float(layer["Thickness"])
            if thick <= 0: continue
            top = current_d
            bottom = current_d + thick
            
            if layer["Liquefiable"]: color = "#d3d3d3"
            elif layer["Type"] == "cohesive": color = "#e6b8af"
            else: color = "#f9e79f"
            
            ax0.add_patch(mpatches.Rectangle((0, top), 1, thick, facecolor=color, edgecolor="black", linewidth=1.2))
            
            label_text = f"{layer['Name']}\nN={int(layer['N_SPT'])}, γ={layer['Gamma']}kN/m³"
            ax0.text(0.5, top + thick / 2, label_text, ha="center", va="center", fontsize=11, fontweight="bold", clip_on=True)
            current_d = bottom
            y_ticks.append(round(current_d, 1))

        if gwt_depth <= max_depth:
            ax0.axhline(y=gwt_depth, color="blue", linestyle="--", linewidth=2.0)
            ax0.text(0.05, gwt_depth - 0.2, f"▼ GWT = {gwt_depth:.1f}m", color="blue", fontweight="bold", fontsize=11)

        ax0.set_ylim(max_depth, 0)
        ax0.set_xlim(0, 1)
        ax0.set_xticks([])
        ax0.set_yticks(y_ticks)
        ax0.tick_params(axis="y", labelsize=11)
        ax0.set_ylabel("Depth (m)", fontsize=13, fontweight="bold")
        ax0.set_title("Soil Profile & Water Table", fontsize=13, fontweight="bold")

        ax1.plot(df_res["Cum. Qs (ton)"], df_res["Depth (m)"], "b-", linewidth=2.5, label="Cumulative Shaft Res. ($Q_s$)")
        ax1.plot(df_res["Qb (ton)"], df_res["Depth (m)"], "--", color="orange", linewidth=2.5, label="End Bearing ($Q_b$)")
        ax1.set_ylim(max_depth, 0)
        ax1.tick_params(axis="both", labelsize=11)
        ax1.set_xlabel("Resistance (ton)", fontsize=13, fontweight="bold")
        ax1.set_title("Components Capacity Breakdown", fontsize=13, fontweight="bold")
        ax1.legend(loc="upper right", fontsize=10)
        ax1.grid(True, linestyle=":", alpha=0.6)

        ax2.plot(df_res["Q_allow Geotech (ton)"], df_res["Depth (m)"], "g-", linewidth=2.5, label=f"Geotech $Q_{{allow}}$ (FS={fs_factor})")
        ax2.axvline(x=struct_allow_service_ton, color="darkred", linestyle="-.", linewidth=2.2, label=f"Struct. Allowable Limit")
        ax2.axvline(x=target_capacity, color="purple", linestyle="--", linewidth=2.0, label=f"Target $Q_{{allow}}$ ({target_capacity}t)")

        if req_depth is not None:
            ax2.plot(target_capacity, req_depth, "ro", markersize=10)
            ax2.annotate(
                f"Req. Depth = {req_depth:.2f} m\nfor $Q_{{allow}}$ = {target_capacity:.1f} ton",
                xy=(target_capacity, req_depth),
                xytext=(max(10.0, target_capacity - 60), min(max_depth - 1.5, req_depth + 3)),
                bbox=dict(boxstyle="round,pad=0.5", fc="yellow", ec="orange", lw=1.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color="red"),
                fontsize=10, fontweight="bold"
            )

        ax2.set_ylim(max_depth, 0)
        ax2.tick_params(axis="both", labelsize=11)
        ax2.set_xlabel("Allowable Capacity (ton)", fontsize=13, fontweight="bold")
        ax2.set_title("Capacity & Governing Check", fontsize=13, fontweight="bold")
        ax2.legend(loc="lower right", fontsize=10)
        ax2.grid(True, linestyle=":", alpha=0.6)

        ax3.axis("off")
        ax3.set_title("Design Governing Criteria", fontsize=13, fontweight="bold")

        equations_text = (
            f"1. Structural Capacity ({aci_version}):\n"
            f"   • f'c = {fc_prime} MPa, fy = {fy_rebar} MPa, ρ = {rebar_ratio_pct}%\n"
            f"   • Design Strength ϕPn = {P_design_comp_ton:.1f} ton\n\n"
            "2. Governing Rule:\n"
            "   • Q_allow,final = min(Q_allow,geo , P_struct,allow)\n"
            f"   • If Geo < Struct ➔ **Geotechnical Governs**\n"
            f"   • If Geo > Struct ➔ **Structural Governs**\n\n"
            "3. Geotechnical Formulas & Limitations:\n"
            "   • Q_u = Q_s + Q_b,  Q_allow = Q_u / FS\n"
            "   • Cohesive (Clay):\n"
            "     - c_u = 6.25 · N\n"
            "     - f_s = min(α·c_u, 150 kPa), α via c_u\n"
            "     - q_b = min(9·c_u, 5000 kPa)\n"
            "   • Cohesionless (Sand):\n"
            "     - β = max(0.25, 1.5 - 0.245√z)\n"
            "     - f_s = min(2N, β·σ'_v, 100, 150)\n"
            "     - q_b = min(40N, 3N·σ'_v/100, 4000, 5000)"
        )

        ax3.text(0.01, 0.97, equations_text, transform=ax3.transAxes, fontsize=13, verticalalignment="top", bbox=dict(boxstyle="square,pad=0.8", facecolor="white", edgecolor="gray", linewidth=1.5))

        fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.10, wspace=0.15)

        st.pyplot(fig, use_container_width=True)

        st.markdown(f"<h2 style='text-align: center; margin-top: 20px;'>BORED PILE GOVERNING CAPACITY SUMMARY ({aci_version})</h2>", unsafe_allow_html=True)
        st.dataframe(df_res, use_container_width=True)
