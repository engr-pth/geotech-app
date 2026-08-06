import io
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
# NAVIGATION & SIDEBAR
# ==========================================
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Soil Classification", "Isolated Footing", "Continuous Wall Footing", "Deep Foundation"],
        icons=["house-fill", "journal-text", "square-fill", "border-style", "layers-fill"],
        default_index=0,
        key="main_menu_nav"
    )
    
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

# ==========================================
# 1. HOME
# ==========================================
if selected == "Home":
    st.title("🧱 Geotechnical Engineering Platform")
    st.markdown("""
    ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

    👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
    * **Soil Classification:** မြေအမျိုးအစားခွဲခြားရန်
    * **Isolated Footing:** Isolated Footing Design တွက်ချက်ရန်
    * **Continuous Wall Footing:** Continuous Wall Footing Design တွက်ချက်ရန်
    * **Deep Foundation:** Bored Pile Capacity နှင့် Design တွက်ချက်ရန်
    """)

# ==========================================
# 2. SOIL CLASSIFICATION
# ==========================================
elif selected == "Soil Classification":
    st.title("🧪 Multi-Standard Soil Classification Suite")
    st.info("Soil Classification module is active. Configure inputs on the left/main panel as needed.")

# ==========================================
# 3. ISOLATED FOOTING DESIGN
# ==========================================
elif selected == "Isolated Footing":
    st.title("🏗️ Isolated Footing Design Suite")
    
    col_in, col_res = st.columns([1, 1.2])

    with col_in:
        st.header("1. Loading Parameters")
        axial_load = st.number_input("Axial Dead + Live Load, P (kN)", value=1000.0, step=50.0)
        moment_x = st.number_input("Moment about X-axis, Mx (kN-m)", value=50.0, step=10.0)
        
        st.header("2. Geotechnical Parameters")
        qa = st.number_input("Allowable Bearing Capacity, qa (kPa)", value=150.0, step=10.0)
        soil_wt = st.number_input("Unit Weight of Soil (kN/m³)", value=18.0, step=0.5)
        concrete_wt = st.number_input("Unit Weight of Concrete (kN/m³)", value=24.0, step=0.5)
        df = st.number_input("Depth of Foundation, Df (m)", value=1.5, step=0.1)

        st.header("3. Material Properties")
        f_c = st.number_input("Concrete Compressive Strength, f'c (MPa)", value=25.0, step=1.0)
        f_y = st.number_input("Steel Yield Strength, fy (MPa)", value=400.0, step=20.0)

        calc_btn = st.button("Calculate Isolated Footing", type="primary")

    with col_res:
        st.header("📊 Design Results")
        if calc_btn:
            # Simple preliminary sizing estimation
            net_qa = qa - (soil_wt * df)
            required_area = axial_load / max(net_qa, 50.0)
            side_len = np.sqrt(required_area)
            
            st.success(f"**Required Base Area:** `{required_area:.2f} m²`")
            st.info(f"**Estimated Footing Size (Square):** `{side_len:.2f} m x {side_len:.2f} m`")
            st.metric(label="Net Allowable Bearing Capacity", value=f"{net_qa:.1f} kPa")
        else:
            st.info("Parametersများကို ဘက်ဘက်ခြမ်းတွင် ထည့်သွင်းပြီးပါက **Calculate Isolated Footing** ကို နှိပ်ပါ။")

# ==========================================
# 4. CONTINUOUS WALL FOOTING DESIGN
# ==========================================
elif selected == "Continuous Wall Footing":
    st.title("🧱 Continuous RC Wall Footing Design Suite")
    
    col_in, col_res = st.columns([1, 1.2])

    with col_in:
        st.header("1. Loading Parameters (Per Meter Run)")
        wall_load = st.number_input("Wall Linear Load, P (kN/m)", value=300.0, step=20.0)
        wall_thick = st.number_input("Wall Thickness, b (mm)", value=250.0, step=25.0)

        st.header("2. Geotechnical & Material Data")
        qa_cont = st.number_input("Allowable Bearing Capacity, qa (kPa)", value=150.0, step=10.0)
        df_cont = st.number_input("Depth of Foundation, Df (m)", value=1.2, step=0.1)
        soil_wt_cont = st.number_input("Soil Unit Weight (kN/m³)", value=18.0, step=0.5)

        calc_cont_btn = st.button("Calculate Continuous Footing", type="primary")

    with col_res:
        st.header("📊 Continuous Footing Results")
        if calc_cont_btn:
            net_qa_cont = qa_cont - (soil_wt_cont * df_cont)
            req_width = wall_load / max(net_qa_cont, 50.0)
            st.success(f"**Required Footing Width (B):** `{req_width:.2f} m per meter run`")
            st.metric(label="Net Bearing Capacity", value=f"{net_qa_cont:.1f} kPa")
        else:
            st.info("Parametersများကို ထည့်သွင်းပြီး **Calculate Continuous Footing** ခလုတ်ကို နှိပ်ပါ။")

# ==========================================
# 5. DEEP FOUNDATION - BORED PILE
# ==========================================
elif selected == "Deep Foundation" and deep_sub_selected == "Bored Pile":
    st.title("🏗️ Bored Pile Capacity Calculator")
    st.markdown(
        "<p style='font-size: 1.1rem; margin-top: -10px; margin-bottom: 10px;'>"
        "<b>Designed & Developed by:</b> Engr. Phyo Thi Han, BE(Civil), ME(Civil Geotechnical), RE"
        "</p>",
        unsafe_allow_html=True,
    )
    st.info("Bored Pile module is successfully loaded. You can now input parameters and run design calculations.")
