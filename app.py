import io
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. PAGE CONFIGURATION (Must be the VERY FIRST Streamlit command in the script)
# ==============================================================================
st.set_page_config(
    page_title="Geotechnical Suite & Bored Pile Calculator",
    page_icon="🪨",
    layout="wide"
)

# Sidebar Menu Definition with Nested Navigation
with st.sidebar:
    main_selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Soil Classification", "Shallow Foundation", "Deep Foundation"],
        icons=["house-fill", "journal-text", "layers-fill", "building"],
        default_index=0,
        key="main_menu_nav"
    )
    
    if main_selected == "Shallow Foundation":
        sub_selected = st.radio(
            "📌 Select Foundation Type:",
            ["Isolated Footing", "Continuous Wall Footing"],
            key="sub_menu_nav_shallow"
        )
        selected = sub_selected
    elif main_selected == "Deep Foundation":
        sub_selected = st.radio(
            "📌 Select Foundation Type:",
            ["Bored Pile", "Jack-in Pile"],
            key="sub_menu_nav_deep"
        )
        selected = sub_selected
    else:
        selected = main_selected

# ----------------------------------------------------
# 1. HOME PAGE
# ----------------------------------------------------
if selected == "Home":
    st.title("🧱 Geotechnical Engineering Calculation Suite")
    st.markdown("""
    ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

    👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
    * **Soil Classification:** Grain size distribution (Extended Sieve & Hydrometer) နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲရန်
    * **Shallow Foundation:** Footing Design တွက်ချက်ရန်
    * **Deep Foundation -> Bored Pile:** Bored Pile Capacity တွက်ချက်ရန်
    """)

# ----------------------------------------------------
# 2. SOIL CLASSIFICATION & SWCC PAGE
# ----------------------------------------------------
elif selected == "Soil Classification":
    st.title("🧪 Multi-Standard Soil Classification & SWCC Suite")
    st.caption("Supports USCS (ASTM D2487), AASHTO (M 145), BS 5930 / Eurocode 7, IS 1498, and Estimation of SWCC from PSD")

    col_in, col_res = st.columns([1, 1.2])

    with col_in:
        st.header("1. Select Primary Classification Standard")
        system = st.radio(
            "Standard", 
            ["USCS (ASTM D2487)", "AASHTO (M 145)", "BS 5930 / Eurocode", "IS 1498 (Indian Standard)"],
            key="soil_system_choice"
        )

        st.header("2. Grain Size Distribution Input Method")
        input_method = st.radio(
            "Select Input Type",
            ["Direct Percentages (Gravel, Sand, Silt, Clay)", "Sieve Analysis (% Passing / Retained)"],
            key="soil_input_method"
        )

        sieve_sizes = np.array([9.5, 4.75, 2.0, 0.85, 0.425, 0.15, 0.075])
        sieve_names = ["3/8 in (9.5mm)", "#4 (4.75mm)", "#10 (2.0mm)", "#20 (0.85mm)", "#40 (0.425mm)", "#100 (0.15mm)", "#200 (0.075mm)"]
        passing_data = []

        if input_method == "Direct Percentages (Gravel, Sand, Silt, Clay)":
            gravel = st.number_input("Gravel %", 0.0, 100.0, 15.0, step=0.1)
            sand = st.number_input("Sand %", 0.0, 100.0, 35.0, step=0.1)
            silt = st.number_input("Silt %", 0.0, 100.0, 30.0, step=0.1)
            clay = st.number_input("Clay %", 0.0, 100.0, 20.0, step=0.1)
            fines_total = silt + clay

            p_38 = 100.0
            p_4 = 100.0 - gravel
            p_200 = fines_total
            p_10 = p_4 - (sand * 0.3)
            p_40 = p_4 - (sand * 0.7)
            passing_data = [p_38, p_4, p_10, p_10 - (sand * 0.2), p_40, p_200 + (sand * 0.1), p_200]
            silt_ratio = (silt / fines_total * 100.0) if fines_total > 0 else 50.0

        else:
            st.markdown("Enter Sieve Analysis Data (Standard Sieves)")
            sieve_basis = st.radio("Sieve Data Format", ["% Passing", "% Retained"], horizontal=True)
            
            if sieve_basis == "% Passing":
                p38 = st.number_input("3/8 inch (9.5 mm) - % Passing", 0.0, 100.0, 100.0, step=0.1)
                p4 = st.number_input("Sieve #4 (4.75 mm) - % Passing", 0.0, 100.0, 100.0, step=0.1)
                p10 = st.number_input("Sieve #10 (2.0 mm) - % Passing", 0.0, 100.0, 100.0, step=0.1)
                p20 = st.number_input("Sieve #20 (0.85 mm) - % Passing", 0.0, 100.0, 100.0, step=0.1)
                p40 = st.number_input("Sieve #40 (0.425 mm) - % Passing", 0.0, 100.0, 98.0, step=0.1)
                p100 = st.number_input("Sieve #100 (0.15 mm) - % Passing", 0.0, 100.0, 96.0, step=0.1)
                p200 = st.number_input("Sieve #200 / 0.075mm - % Passing", 0.0, 100.0, 95.0, step=0.1)
                
                passing_data = [p38, p4, p10, p20, p40, p100, p200]

                if "AASHTO" in system or "BS 5930" in system:
                    gravel = max(0.0, 100.0 - p10)
                    sand = max(0.0, p10 - p200)
                else: 
                    gravel = max(0.0, 100.0 - p4)
                    sand = max(0.0, p4 - p200)
                    
                fines_total = max(0.0, p200)
            else:
                r38 = st.number_input("3/8 inch (9.5 mm) - % Retained", 0.0, 100.0, 0.0, step=0.1)
                r4 = st.number_input("Sieve #4 (4.75 mm) - % Retained", 0.0, 100.0, 0.0, step=0.1)
                r10 = st.number_input("Sieve #10 (2.0 mm) - % Retained", 0.0, 100.0, 0.0, step=0.1)
                r20 = st.number_input("Sieve #20 (0.85 mm) - % Retained", 0.0, 100.0, 0.0, step=0.1)
                r40 = st.number_input("Sieve #40 (0.425 mm) - % Retained", 0.0, 100.0, 2.0, step=0.1)
                r100 = st.number_input("Sieve #100 (0.15 mm) - % Retained", 0.0, 100.0, 2.0, step=0.1)
                r200 = st.number_input("Sieve #200 (0.075 mm) - % Retained", 0.0, 100.0, 1.0, step=0.1)
                
                accumulated_retained = r38 + r4 + r10 + r20 + r40 + r100 + r200
                auto_pan = max(0.0, 100.0 - accumulated_retained)
                r_pan = st.number_input("Pan - % Retained (Auto-filled)", 0.0, 100.0, auto_pan, step=0.1)
                
                p38 = 100.0 - r38
                p4 = p38 - r4
                p10 = p4 - r10
                p20 = p10 - r20
                p40 = p20 - r40
                p100 = p40 - r100
                p200 = p100 - r200
                passing_data = [p38, p4, p10, p20, p40, p100, p200]

                if "AASHTO" in system or "BS 5930" in system:
                    gravel = r38 + r4 + r10
                    sand = r20 + r40 + r100 + r200
                else:
                    gravel = r38 + r4
                    sand = r10 + r20 + r40 + r100 + r200
                    
                fines_total = r_pan

            silt_ratio = st.slider("Silt / Fines Ratio (%)", 0.0, 100.0, 60.0, step=1.0)
            silt = fines_total * (silt_ratio / 100.0)
            clay = fines_total * (1.0 - (silt_ratio / 100.0))

        if input_method == "Direct Percentages (Gravel, Sand, Silt, Clay)":
            total_percent = gravel + sand + silt + clay
            if abs(total_percent - 100.0) > 0.05:
                st.error(f"⚠️ **Total Percentage Error:** {total_percent:.1f}% (Must equal 100%)")
            else:
                st.success(f"✅ Total Percentage: `{total_percent:.1f}%`")
        else:
            total_sieve_sum = gravel + sand + fines_total
            if total_sieve_sum > 0:
                gravel = (gravel / total_sieve_sum) * 100.0
                sand = (sand / total_sieve_sum) * 100.0
                silt = (fines_total * (silt_ratio / 100.0) / total_sieve_sum) * 100.0
                clay = (fines_total * (1.0 - (silt_ratio / 100.0)) / total_sieve_sum) * 100.0
            st.success(f"✅ Fines: `{fines_total:.1f}%` | Active Standard Boundaries Applied (`{system.split()[0]}`)")

        st.header("3. Atterberg Limits (%)")
        
        if 'll_val' not in st.session_state: st.session_state.ll_val = 45.0
        if 'pl_val' not in st.session_state: st.session_state.pl_val = 20.0
        if 'pi_val' not in st.session_state: st.session_state.pi_val = 25.0

        def update_pi():
            st.session_state.pi_val = max(0.0, st.session_state.ll_val - st.session_state.pl_val)

        def update_pl_from_pi():
            st.session_state.pl_val = max(0.0, st.session_state.ll_val - st.session_state.pi_val)

        LL = st.number_input("Liquid Limit (LL)", 0.0, 150.0, key='ll_val', on_change=update_pi, step=0.1)
        PL = st.number_input("Plastic Limit (PL)", 0.0, 100.0, key='pl_val', on_change=update_pi, step=0.1)
        PI = st.number_input("Plasticity Index (PI)", 0.0, 100.0, key='pi_val', on_change=update_pl_from_pi, step=0.1)
        
        st.info(f"**Active Atterberg Parameters:** LL = `{LL:.1f}%`, PL = `{PL:.1f}%`, PI = `{PI:.1f}%`")
        
        st.header("4. Grain Size Parameters")
        Cu = st.number_input("Uniformity Coefficient (Cu)", 0.0, 50.0, 4.0, step=0.1)
        Cc = st.number_input("Coefficient of Curvature (Cc)", 0.0, 10.0, 1.0, step=0.1)

        st.header("5. SWCC Estimation Parameters")
        enable_swcc = st.checkbox("Generate Soil-Water Characteristic Curve (SWCC)", value=True)
        
        if enable_swcc:
            swcc_method = st.selectbox(
                "Select SWCC Estimation Model",
                ["Fredlund & Xing (1994) - Pedotransfer", "van Genuchten (1980) - Empirical Fit"]
            )
            e_void = st.number_input("Void Ratio (e)", 0.1, 3.0, 0.65, step=0.05)
            theta_s = e_void / (1.0 + e_void)
            st.caption(f"Calculated Porosity / Saturated Volumetric Water Content ($\Theta_s$): `{theta_s:.3f}`")

    A_line = 0.73 * (LL - 20) if LL >= 20 else 0.0

    def classify_uscs(gravel, sand, fines_val, LL, PI, Cu, Cc):
        if fines_val >= 50:
            if LL >= 50:
                return "CH (High Plasticity Clay)" if PI > A_line else "MH (Elastic Silt)"
            else:
                if PI > A_line and PI > 7:
                    return "CL (Lean Clay)"
                elif PI < A_line and PI < 4:
                    return "ML (Low Plasticity Silt)"
                else:
                    return "CL-ML (Silty Clay)"
        else:
            if gravel > sand:
                if fines_val < 5:
                    return "GW (Well-graded Gravel)" if (Cu >= 4 and 1 <= Cc <= 3) else "GP (Poorly-graded Gravel)"
                elif fines_val > 12:
                    return "GC (Clayey Gravel)" if PI > A_line else "GM (Silty Gravel)"
                else:
                    return "GW-GM / GP-GC (Gravel with Fines)"
            else:
                if fines_val < 5:
                    return "SW (Well-graded Sand)" if (Cu >= 6 and 1 <= Cc <= 3) else "SP (Poorly-graded Sand)"
                elif fines_val > 12:
                    return "SC (Clayey Sand)" if PI > A_line else "SM (Silty Sand)"
                else:
                    return "SW-SM / SP-SC (Sand with Fines)"

    def classify_aashto(fines_val, LL, PI, gravel, sand):
        GI = (fines_val - 35) * (0.2 + 0.005 * (LL - 40)) + 0.01 * (fines_val - 15) * (PI - 10)
        GI = max(0, int(round(GI)))
        if fines_val <= 35:
            if fines_val <= 15 and PI <= 6:
                group = "A-1-a" if gravel > sand else "A-1-b"
            elif fines_val <= 25 and (LL == 0 or PI <= 6):
                group = "A-3 (Fine Sand)"
            else:
                if PI <= 10:
                    group = "A-2-4" if LL <= 40 else "A-2-5"
                else:
                    group = "A-2-6" if LL <= 40 else "A-2-7"
            return f"{group} (GI = 0)"
        else:
            if LL <= 40:
                group = "A-4" if PI <= 10 else "A-6"
            else:
                group = "A-7-5" if PI <= (LL - 30) else "A-7-6"
            return f"{group} (GI = {GI})"

    def classify_bs(fines_val, LL, PI):
        if fines_val >= 35:
            if LL < 35: qual = "L (Low Plasticity)"
            elif 35 <= LL < 50: qual = "I (Intermediate Plasticity)"
            elif 50 <= LL < 70: qual = "H (High Plasticity)"
            elif 70 <= LL < 90: qual = "V (Very High Plasticity)"
            else: qual = "E (Extremely High Plasticity)"
            
            soil_type = "Clay (C)" if PI > A_line else "Silt (M)"
            return f"{soil_type} - {qual}"
        else:
            return "Coarse-Grained Soil (Gravel/Sand)"

    def classify_is_1498(fines_val, LL, PI):
        if fines_val >= 50:
            if LL > 50:
                return "CH (High Plasticity Clay)" if PI > A_line else "MH (High Plasticity Silt)"
            elif 35 <= LL <= 50:
                return "CI (Intermediate Plasticity Clay)" if PI > A_line else "MI (Intermediate Plasticity Silt)"
            else:
                return "CL (Low Plasticity Clay)" if PI > A_line else "ML (Low Plasticity Silt)"
        else:
            return "Coarse-Grained Soil (Gravel/Sand)"

    with col_res:
        st.header("📊 Classification Results")
        
        uscs_res = classify_uscs(gravel, sand, fines_total, LL, PI, Cu, Cc)
        aashto_res = classify_aashto(fines_total, LL, PI, gravel, sand)
        bs_res = classify_bs(fines_total, LL, PI)
        is_res = classify_is_1498(fines_total, LL, PI)
        
        if "USCS" in system:
            st.success(f"**USCS Symbol:** `{uscs_res}`")
        elif "AASHTO" in system:
            st.success(f"**AASHTO Group:** `{aashto_res}`")
        elif "BS 5930" in system:
            st.success(f"**BS 5930 Standard:** `{bs_res}`")
        else:
            st.success(f"**IS 1498 Symbol:** `{is_res}`")
            
        st.markdown("---")
        st.subheader("🔄 Cross-Standard Comparison")
        st.json({
            "USCS (ASTM D2487)": uscs_res,
            "AASHTO (Highway)": aashto_res,
            "BS 5930 (British/Euro)": bs_res,
            "IS 1498 (Indian Standard)": is_res
        })
        
        st.subheader("📉 Grain Size Distribution Curve")
        fig_gsd, ax_gsd = plt.subplots(figsize=(7, 4.0))
        
        d_extended = np.array([100.0, 75.0] + list(sieve_sizes) + [0.005, 0.001])
        p_extended = np.array([100.0, 100.0] + list(passing_data) + [clay, 0.0])
        
        ax_gsd.plot(d_extended, p_extended, color='#1e88e5', linewidth=2.5, marker='o', markersize=5, label="Soil Sample")
        ax_gsd.axvline(4.75, color='gray', linestyle='--', alpha=0.6)
        ax_gsd.axvline(0.075, color='gray', linestyle='--', alpha=0.6)
        ax_gsd.axvline(0.002, color='gray', linestyle='--', alpha=0.6)
        
        ax_gsd.text(15, 102, "Gravel", fontsize=8, ha='center', fontweight='bold', color='#555555')
        ax_gsd.text(0.6, 102, "Sand", fontsize=8, ha='center', fontweight='bold', color='#555555')
        ax_gsd.text(0.012, 102, "Silt", fontsize=8, ha='center', fontweight='bold', color='#555555')
        ax_gsd.text(0.001, 102, "Clay", fontsize=8, ha='center', fontweight='bold', color='#555555')

        ax_gsd.set_xscale('log')
        ax_gsd.set_xlim(100.0, 0.0005)
        ax_gsd.set_ylim(0, 105)
        ax_gsd.set_xlabel("Particle Diameter - d (mm) [Log Scale]", fontsize=9)
        ax_gsd.set_ylabel("Percent Passing (%)", fontsize=9)
        ax_gsd.grid(True, which="both", linestyle=':', alpha=0.6)
        ax_gsd.legend(loc="lower left", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig_gsd)

        st.subheader("🧱 Soil Composition Breakdown")
        fig_bar, ax_bar = plt.subplots(figsize=(7, 1.8))
        components = ['Gravel', 'Sand', 'Silt', 'Clay']
        values = [gravel, sand, silt, clay]
        colors_list = ['#8d6e63', '#d4e157', '#4fc3f7', '#e57373']
        
        left = 0
        for comp, val, col in zip(components, values, colors_list):
            if val > 0:
                ax_bar.barh('Composition', val, left=left, color=col, label=f"{comp}: {val:.1f}%")
                if val >= 8.0:
                    ax_bar.text(left + val/2, 0, f"{val:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
                left += val
                
        ax_bar.set_xlim(0, 100)
        ax_bar.axis('off')
        ax_bar.legend(loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=4, frameon=False, fontsize=8.5)
        plt.tight_layout()
        st.pyplot(fig_bar)

        st.subheader("📈 Casagrande Plasticity Chart")
        fig, ax = plt.subplots(figsize=(6, 3.2))
        ll_vals = np.linspace(0, 100, 100)
        a_line_vals = 0.73 * (ll_vals - 20)
        
        ax.plot(ll_vals, a_line_vals, color='red', linestyle='--', label="A-Line")
        ax.axvline(35, color='gray', linestyle=':', label="LL=35%")
        ax.axvline(50, color='gray', linestyle=':', label="LL=50%")
        ax.scatter([LL], [PI], color='blue', s=80, zorder=5, label=f"Soil (LL={LL:.1f}, PI={PI:.1f})")
        
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 60)
        ax.set_xlabel("Liquid Limit (LL %)")
        ax.set_ylabel("Plasticity Index (PI %)")
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc="upper left", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig)

        if enable_swcc:
            st.markdown("---")
            st.subheader("💧 Soil-Water Characteristic Curve (SWCC)")
            st.caption("Estimated from Grain Size Distribution & Volumetric Properties")

            psi = np.logspace(-2, 6, 200)

            if clay > 40:
                a_param = 300.0
                n_param = 1.2
                m_param = 0.8
                theta_r = 0.08
            elif fines_total > 50:
                a_param = 50.0
                n_param = 1.5
                m_param = 0.9
                theta_r = 0.04
            elif sand > 50:
                a_param = 5.0
                n_param = 3.0
                m_param = 1.2
                theta_r = 0.02
            else:
                a_param = 10.0
                n_param = 2.0
                m_param = 1.0
                theta_r = 0.01

            if "Fredlund & Xing" in swcc_method:
                C_psi = 1 - (np.log(1 + psi / 3000) / np.log(1 + 1e6 / 3000))
                theta_w = C_psi * (theta_s / np.power(np.log(np.e + np.power(psi / a_param, n_param)), m_param))
            else:
                m_vg = 1 - (1 / n_param) if n_param > 1 else 0.5
                alpha_vg = 1.0 / a_param
                theta_w = theta_r + (theta_s - theta_r) / np.power(1 + np.power(alpha_vg * psi, n_param), m_vg)

            fig_swcc, ax_swcc = plt.subplots(figsize=(7, 4.0))
            ax_swcc.plot(psi, theta_w, color='#00897b', linewidth=2.5, label=f"Predicted SWCC ({swcc_method.split()[0]})")
            
            ax_swcc.set_xscale('log')
            ax_swcc.set_xlim(0.01, 1000000)
            ax_swcc.set_ylim(0, theta_s * 1.1)
            ax_swcc.set_xlabel("Matric Suction - $\psi$ (kPa) [Log Scale]", fontsize=9)
            ax_swcc.set_ylabel("Volumetric Water Content - $\Theta$ ($m^3/m^3$)", fontsize=9)
            ax_swcc.grid(True, which="both", linestyle=':', alpha=0.6)
            
            ax_swcc.axvline(a_param, color='orange', linestyle='--', alpha=0.7, label=f"Est. Air Entry Value ≈ {a_param:.1f} kPa")
            ax_swcc.legend(loc="upper right", fontsize=8)
            plt.tight_layout()
            
            st.pyplot(fig_swcc)

            st.info(f"""
            📌 **Estimated SWCC Parameters Summary:**
            * **Air-Entry Value (AEV) Parameter ($a$):** `{a_param:.1f} kPa`
            * **Desaturation Rate Parameter ($n$):** `{n_param:.2f}`
            * **Saturated Volumetric Water Content ($\Theta_s$):** `{theta_s:.3f}`
            * **Residual Water Content ($\Theta_r$):** `{theta_r:.3f}`
            """)

# ----------------------------------------------------
# 3. BORED PILE PAGE
# ----------------------------------------------------
elif selected == "Bored Pile":

    def reset_calc():
        st.session_state.calculated = False

    def classify_soil(soil_type: str, n_spt: float) -> str:
        if soil_type == "cohesionless":
            if n_spt <= 4:
                return "Very Loose Sand"
            elif n_spt <= 10:
                return "Loose Sand"
            elif n_spt <= 30:
                return "Medium Dense Sand"
            elif n_spt <= 50:
                return "Dense Sand"
            else:
                return "Very Dense Sand"
        else:
            if n_spt <= 2:
                return "Very Soft Clay"
            elif n_spt <= 4:
                return "Soft Clay"
            elif n_spt <= 8:
                return "Medium Stiff Clay"
            elif n_spt <= 16:
                return "Stiff Clay"
            elif n_spt <= 32:
                return "Very Stiff Clay"
            elif n_spt <= 50:
                return "Hard Clay"
            else:
                return "Very Hard Clay"

    st.title("🏗️ Bored Pile Capacity Calculator")
    st.markdown(
        "<p style='font-size: 1.1rem; margin-top: -10px; margin-bottom: 10px;'>"
        "<b>Designed & Developed by:</b> Engr. Phyo Thi Han, BE(Civil), ME(Civil"
        " Geotechnical), RE(Construction, Geotechnical & Structural)"
        "</p>",
        unsafe_allow_html=True,
    )

    st.warning(
        "⚠️ **Disclaimer:** ယခုတွက်ချက်မှုများသည် preliminary design"
        " အတွက်သာ ရည်ရွယ်ပါသည်။ ရရှိလာသောအဖြေများကို သက်ဆိုင်ရာ Building Code နှင့်"
        " Engineering Judgement တို့ဖြင့် တိုက်ဆိုင်စစ်ဆေးရမည်ဖြစ်ပါသည်။"
    )

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
            {"Soil Name": "Sand", "Thickness": 3.0, "N_SPT": 68.0, "Gamma": 20.5, "Liquefiable": False},
        ]

    if "calculated" not in st.session_state:
        st.session_state.calculated = False

    if "delete_stage" not in st.session_state:
        st.session_state.delete_stage = {}

    st.info(
        "ℹ️ ကျေးဇူးပြု၍ အောက်ပါနေရာများတွင် Pile Parameters၊ Structural Code၊ GWT"
        " နှင့် Soil Layers များကို ထည့်သွင်းပြီး '🚀 Design Pile' ခလုတ်ကို နှိပ်ပါ။"
    )

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

    st.header("2. Soil Stratigraphy Input (မြေအလွှာဖွဲ့စည်းပုံ အချက်အလက်များ)")

    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )

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
            s_name = st.selectbox(
                "Soil Name",
                ["Clay", "Sand"],
                index=0 if layer["Soil Name"] == "Clay" else 1,
                key=f"s_name_{i}",
                label_visibility="collapsed",
                on_change=reset_calc,
            )
            st.session_state.soil_layers[i]["Soil Name"] = s_name

        with c2:
            thick = st.number_input(
                "Thickness",
                min_value=0.1,
                value=float(layer["Thickness"]),
                step=0.5,
                key=f"thick_{i}",
                label_visibility="collapsed",
                on_change=reset_calc,
            )
            st.session_state.soil_layers[i]["Thickness"] = thick

        with c3:
            n_spt = st.number_input(
                "N_SPT",
                min_value=0.0,
                value=float(layer["N_SPT"]),
                step=1.0,
                key=f"n_spt_{i}",
                label_visibility="collapsed",
                on_change=reset_calc,
            )
            st.session_state.soil_layers[i]["N_SPT"] = n_spt

        with c4:
            gamma_val = st.number_input(
                "Gamma",
                min_value=10.0,
                max_value=25.0,
                value=float(layer.get("Gamma", 18.0)),
                step=0.5,
                key=f"gamma_{i}",
                label_visibility="collapsed",
                on_change=reset_calc,
            )
            st.session_state.soil_layers[i]["Gamma"] = gamma_val

        with c5:
            liq = st.checkbox(
                "Liquefiable",
                value=bool(layer["Liquefiable"]),
                key=f"liq_{i}",
                on_change=reset_calc,
            )
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
            st.session_state.soil_layers.append({
                "Soil Name": "Clay",
                "Thickness": 1.5,
                "N_SPT": 10.0,
                "Gamma": 18.0,
                "Liquefiable": False,
            })
            st.session_state.calculated = False
            st.rerun()

    total_thickness = sum([float(l["Thickness"]) for l in st.session_state.soil_layers])
    st.metric(
        label="📊 Total Soil Thickness (စုစုပေါင်း မြေအလွှာအထူ)",
        value=f"{total_thickness:.2f} m",
    )

    st.markdown("---")

    if st.button("🚀 Design Pile (ပိုင်တိုင် ဒီဇိုင်း စတင်တွက်မည်)", type="primary", use_container_width=True):
        if len(st.session_state.soil_layers) == 0:
            st.error("Soil Layer နည်းဆုံး ၁ ခု ထည့်ပေးပါရန်!")
            st.session_state.calculated = False
        else:
            st.session_state.calculated = True

    if st.session_state.calculated and len(st.session_state.soil_layers) > 0:
        st.markdown("---")
        st.header("3. Design Report & Output (ဒီဇိုင်း အစီရင်ခံစာနှင့် ရလဒ်များ)")

        A_g = (np.pi / 4.0) * (pile_diameter**2)
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
                "Thickness": thick_val,
                "Type": s_type,
                "N_SPT": n_val,
                "Gamma": gamma_val,
                "Liquefiable": liq_val,
                "Name": classified_name,
            })

        max_depth = sum([float(layer["Thickness"]) for layer in soil_profile if float(layer["Thickness"]) > 0])
        if max_depth <= 0:
            max_depth = 30.5

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
                "Depth (m)": round(d, 2),
                "Eff. Stress (kPa)": round(eff_stress_tip, 1),
                "Cum. Qs (ton)": round(qs_ton, 2),
                "Qb (ton)": round(qb_ton, 2),
                "Qu Geotech (ton)": round(qu_ton, 2),
                "Q_allow Geotech (ton)": round(qa_ton, 2),
                "Governing Capacity (ton)": round(governing_capacity, 2),
                "Governing Mode": governing_mode,
            })

        df_res = pd.DataFrame(results)

        if P_design_comp_ton < (target_capacity * fs_factor):
            st.warning(
                f"⚠️ သတိပေးချက်: Pile Section ရဲ့ Structural Capacity ({aci_version},"
                f" $\\phi P_n$ = {P_design_comp_ton:.1f} ton) သည် Target Ultimate Load"
                " ထက် နည်းနေပါသည်။"
            )

        fig, (ax0, ax1, ax2, ax3) = plt.subplots(
            1, 4, figsize=(28, 11), dpi=350, gridspec_kw={"width_ratios": [1.1, 1.0, 1.0, 1.6]}
        )

        fig.suptitle(
            f"Bored Pile Design Report & Governing Check ({aci_version}, Dia ="
            f" {pile_diameter}m, f'c = {fc_prime}MPa)\nDesigned & Developed by:"
            " Engr. Phyo Thi Han, BE(Civil), ME(Civil Geotechnical), RE(Construction,"
            " Geotechnical & Structural)",
            fontsize=16,
            fontweight="bold",
            y=0.96,
        )

        current_d = 0.0
        y_ticks = [0.0]
        for layer in soil_profile:
            thick = float(layer["Thickness"])
            if thick <= 0:
                continue
            top = current_d
            bottom = current_d + thick

            if layer["Liquefiable"]:
                color = "#d3d3d3"
            elif layer["Type"] == "cohesive":
                color = "#e6b8af"
            else:
                color = "#f9e79f"

            ax0.add_patch(
                mpatches.Rectangle(
                    (0, top), 1, thick, facecolor=color, edgecolor="black", linewidth=1.2
                )
            )

            label_text = f"{layer['Name']}\nN={int(layer['N_SPT'])}, γ={layer['Gamma']}kN/m³"
            ax0.text(
                0.5,
                top + thick / 2,
                label_text,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                clip_on=True,
            )
            current_d = bottom
            y_ticks.append(round(current_d, 1))

        if gwt_depth <= max_depth:
            ax0.axhline(y=gwt_depth, color="blue", linestyle="--", linewidth=2.0)
            ax0.text(
                0.05,
                gwt_depth - 0.2,
                f"▼ GWT = {gwt_depth:.1f}m",
                color="blue",
                fontweight="bold",
                fontsize=11,
            )

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
                fontsize=10,
                fontweight="bold",
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

        ax3.text(
            0.01,
            0.97,
            equations_text,
            transform=ax3.transAxes,
            fontsize=13,
            verticalalignment="top",
            bbox=dict(
                boxstyle="square,pad=0.8",
                facecolor="white",
                edgecolor="gray",
                linewidth=1.5,
            ),
        )

        fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.10, wspace=0.15)

        st.pyplot(fig, use_container_width=True)

        st.markdown(
            f"<h2 style='text-align: center; margin-top: 20px;'>BORED PILE"
            f" GOVERNING CAPACITY SUMMARY ({aci_version})</h2>",
            unsafe_allow_html=True,
        )
        st.dataframe(df_res, use_container_width=True)

# ----------------------------------------------------
# 4. OTHER PAGES (PLACEHOLDERS)
# ----------------------------------------------------
else:
    st.title(f"🛠️ {selected}")
    st.info("ဤ Tool သည် လက်ရှိ မပါဝင်သေးပါ သို့မဟုတ် တည်ဆောက်ဆဲ ဖြစ်ပါသည်။")
