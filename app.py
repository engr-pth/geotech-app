import io
import matplotlib.patches as mpatches
import matplotlib.patches as patches
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
  else:  # cohesive
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

# Reset Calculation Function
def reset_calc():
  st.session_state.calculated = False

with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Soil Classification", "Isolated Footing", "Continuous Wall Footing", "Deep Foundation"],
        icons=["house-fill", "journal-text", "square-fill", "border-style", "layers-fill"],
        default_index=0,
        key="main_menu_nav"
    )
    
    # Sub-menu if Deep Foundation is selected
    deep_sub_selected = ""
    if selected == "Deep Foundation":
        deep_sub_selected = option_menu(
            menu_title=None,
            options=["Bored Pile"],
            icons=["pin-fill"],
            default_index=0,
            key="deep_foundation_submenu",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "orange", "font-size": "14px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            }
        )

if selected == "Home":
    st.title("🧱 Geotechnical Engineering Platform")
    st.markdown("""
    ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

    👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
    * **Soil Classification:** Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲရန်
    * **Shallow Foundation Design တွက်ချက်ရန်:**
        * **Isolated Footing Design:** Isolated Footing Design တွက်ချက်ရန်
        * **Continuous Wall Footing Design:** Continuous Wall Footing Design တွက်ချက်ရန်
    * **Deep Foundation:**
        * **Bored Pile:** Bored Pile Capacity နှင့် Design တွက်ချက်ရန်
    """)

elif selected == "Soil Classification":
    st.title("🧪 Multi-Standard Soil Classification Suite")
    st.caption("Supports USCS (ASTM D2487), AASHTO (M 145), BS 5930 / Eurocode 7, and IS 1498 (Indian Standard)")

    col_in, col_res = st.columns([1, 1.2])

    with col_in:
        st.header("1. Grain Size Distribution Inputs (%)")
        gravel = st.number_input("Gravel (> 4.75mm) %", 0.0, 100.0, 15.0, step=0.1)
        sand = st.number_input("Sand (0.075mm - 4.75mm) %", 0.0, 100.0, 35.0, step=0.1)
        silt = st.number_input("Silt (0.002mm - 0.075mm) %", 0.0, 100.0, 30.0, step=0.1)
        clay = st.number_input("Clay (< 0.002mm) %", 0.0, 100.0, 20.0, step=0.1)
        
        fines = silt + clay
        total_percent = gravel + sand + silt + clay
        
        if abs(total_percent - 100.0) > 0.01:
            st.error(f"⚠️ **Total Percentage Error:** {total_percent:.1f}% (Must equal 100%)")
        else:
            st.success(f" Total Percentage: `{total_percent:.1f}%` | **Fines (< 0.075mm):** `{fines:.1f}%`")
        
        st.header("2. Atterberg Limits (%)")
        LL = st.number_input("Liquid Limit (LL)", 0.0, 150.0, 45.0, step=0.1)
        PL = st.number_input("Plastic Limit (PL)", 0.0, 100.0, 20.0, step=0.1)
        PI = max(0.0, LL - PL)
        st.info(f"**Plasticity Index (PI):** `{PI:.1f}%`")
        
        st.header("3. Grain Size Parameters (Optional)")
        Cu = st.number_input("Uniformity Coefficient (Cu)", 0.0, 50.0, 4.0, step=0.1)
        Cc = st.number_input("Coefficient of Curvature (Cc)", 0.0, 10.0, 1.0, step=0.1)
        
        st.header("4. Select Primary Classification Standard")
        system = st.radio("Standard", ["USCS (ASTM D2487)", "AASHTO (M 145)", "BS 5930 / Eurocode", "IS 1498 (Indian Standard)"])

    A_line = 0.73 * (LL - 20) if LL >= 20 else 0.0

    def classify_uscs(gravel, sand, fines, LL, PI, Cu, Cc):
        if fines >= 50:
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
                if fines < 5:
                    return "GW (Well-graded Gravel)" if (Cu >= 4 and 1 <= Cc <= 3) else "GP (Poorly-graded Gravel)"
                elif fines > 12:
                    return "GC (Clayey Gravel)" if PI > A_line else "GM (Silty Gravel)"
                else:
                    return "GW-GM / GP-GC (Gravel with Fines)"
            else:
                if fines < 5:
                    return "SW (Well-graded Sand)" if (Cu >= 6 and 1 <= Cc <= 3) else "SP (Poorly-graded Sand)"
                elif fines > 12:
                    return "SC (Clayey Sand)" if PI > A_line else "SM (Silty Sand)"
                else:
                    return "SW-SM / SP-SC (Sand with Fines)"

    def classify_aashto(fines, LL, PI, gravel, sand):
        GI = (fines - 35) * (0.2 + 0.005 * (LL - 40)) + 0.01 * (fines - 15) * (PI - 10)
        GI = max(0, int(round(GI)))
        if fines <= 35:
            if fines <= 15 and PI <= 6:
                group = "A-1-a" if gravel > sand else "A-1-b"
            elif fines <= 25 and (LL == 0 or PI <= 6):
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

    def classify_bs(fines, LL, PI):
        if fines >= 35:
            if LL < 35: qual = "L (Low Plasticity)"
            elif 35 <= LL < 50: qual = "I (Intermediate Plasticity)"
            elif 50 <= LL < 70: qual = "H (High Plasticity)"
            elif 70 <= LL < 90: qual = "V (Very High Plasticity)"
            else: qual = "E (Extremely High Plasticity)"
            
            soil_type = "Clay (C)" if PI > A_line else "Silt (M)"
            return f"{soil_type} - {qual}"
        else:
            return "Coarse-Grained Soil (Gravel/Sand)"

    def classify_is_1498(fines, LL, PI):
        if fines >= 50:
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
        
        uscs_res = classify_uscs(gravel, sand, fines, LL, PI, Cu, Cc)
        aashto_res = classify_aashto(fines, LL, PI, gravel, sand)
        bs_res = classify_bs(fines, LL, PI)
        is_res = classify_is_1498(fines, LL, PI)
        
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
        
        st.subheader("🧱 Soil Composition Breakdown")
        fig_bar, ax_bar = plt.subplots(figsize=(6, 1.2))
        components = ['Gravel', 'Sand', 'Silt', 'Clay']
        values = [gravel, sand, silt, clay]
        colors = ['#8d6e63', '#d4e157', '#4fc3f7', '#e57373']
        
        left = 0
        for comp, val, col in zip(components, values, colors):
            if val > 0:
                ax_bar.barh('Composition', val, left=left, color=col, label=f"{comp}: {val:.1f}%")
                left += val
                
        ax_bar.set_xlim(0, 100)
        ax_bar.axis('off')
        ax_bar.legend(loc='lower center', bbox_to_anchor=(0.5, -0.8), ncol=4, frameon=False)
        st.pyplot(fig_bar)

        st.subheader("📈 Casagrande Plasticity Chart")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ll_vals = np.linspace(0, 100, 100)
        a_line_vals = 0.73 * (ll_vals - 20)
        
        ax.plot(ll_vals, a_line_vals, color='red', linestyle='--', label="A-Line")
        ax.axvline(35, color='gray', linestyle=':', label="LL=35%")
        ax.axvline(50, color='gray', linestyle=':', label="LL=50%")
        ax.scatter([LL], [PI], color='blue', s=80, zorder=5, label=f"Soil (LL={LL}, PI={PI})")
        
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 60)
        ax.set_xlabel("Liquid Limit (LL %)")
        ax.set_ylabel("Plasticity Index (PI %)")
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc="upper left")
        st.pyplot(fig)

elif selected == "Isolated Footing":
    st.title("🏗️ Single Geotechnical & Structural Footing Design Suite")
    st.info("Isolated Footing Design module is active. Please configure parameters on the left panel.")

elif selected == "Continuous Wall Footing":
    st.title("🧱 Continuous RC Wall Footing Design Suite")
    st.info("Continuous Wall Footing Design module is active. Please configure parameters on the left panel.")

elif selected == "Deep Foundation" and deep_sub_selected == "Bored Pile":
    st.title("🏗️ Bored Pile Capacity Calculator")
    st.markdown(
        "<p style='font-size: 1.1rem; margin-top: -10px; margin-bottom: 10px;'>"
        "<b>Designed & Developed by:</b> Engr. Phyo Thi Han, BE(Civil), ME(Civil Geotechnical), RE"
        "</p>",
        unsafe_allow_html=True,
    )
    st.info("Bored Pile module is successfully loaded. You can now input parameters and run design calculations.")
