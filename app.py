import io
import matplotlib.patches as patches
import matplotlib.plt as plt
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
from streamlit_option_menu import option_menu

# Page Config Setup
st.set_page_config(
    page_title="Geotechnical Suite",
    page_icon="🪨",
    layout="wide"
)

# ----------------------------------------------------
# NAVIGATION MENU (SIDEBAR)
# ----------------------------------------------------
with st.sidebar:
    selected = option_menu(
        "Main Menu",
        ["Soil Classification", "Isolated Footing", "Continuous Wall Footing"],
        icons=["moisture", "box", "border-style"],
        menu_icon="cast",
        default_index=0,
    )

# ----------------------------------------------------
# HELPER FUNCTIONS & GEOTECHNICAL LOGIC
# ----------------------------------------------------

def calculate_uscs(gravel, sand, fines, LL, PI, Cu, Cc, organic=False):
    """
    Comprehensive USCS Classification (ASTM D2487)
    Returns: (Symbol, Group Name)
    """
    A_line = 0.73 * (LL - 20) if LL >= 20 else 0.0
    
    if organic:
        if LL >= 50:
            return "OH", "Organic clay / Organic silt of high plasticity"
        else:
            return "OL", "Organic clay / Organic silt of low plasticity"
            
    # Fine-Grained Soil (>= 50% passing No. 200)
    if fines >= 50:
        if LL >= 50:
            if PI > A_line:
                symbol = "CH"
                name = "Fat clay"
            else:
                symbol = "MH"
                name = "Elastic silt"
        else:
            if PI > A_line and PI > 7:
                symbol = "CL"
                name = "Lean clay"
            elif PI < A_line or PI < 4:
                symbol = "ML"
                name = "Silt"
            else:
                symbol = "CL-ML"
                name = "Silty clay"
                
        coarse = gravel + sand
        if coarse >= 30:
            if gravel > sand:
                name += " with gravel"
            else:
                name += " with sand"
        elif 15 <= coarse < 30:
            if gravel > sand:
                name += " with gravel"
            else:
                name += " with sand"
        return symbol, name

    # Coarse-Grained Soil (< 50% passing No. 200)
    else:
        if gravel > sand:
            if fines < 5:
                well_graded = (Cu >= 4) and (1 <= Cc <= 3)
                if well_graded:
                    return "GW", "Well-graded gravel"
                else:
                    return "GP", "Poorly graded gravel"
            elif fines > 12:
                if PI > A_line and PI > 7:
                    return "GC", "Clayey gravel"
                elif PI < A_line or PI < 4:
                    return "GM", "Silty gravel"
                else:
                    return "GC-GM", "Silty clayey gravel"
            else: 
                well_graded = (Cu >= 4) and (1 <= Cc <= 3)
                prefix = "GW" if well_graded else "GP"
                suffix = "GC" if (PI > A_line and PI > 4) else "GM"
                return f"{prefix}-{suffix}", f"Gravel with silt/clay ({prefix}-{suffix})"
        else:
            if fines < 5:
                well_graded = (Cu >= 6) and (1 <= Cc <= 3)
                if well_graded:
                    return "SW", "Well-graded sand"
                else:
                    return "SP", "Poorly graded sand"
            elif fines > 12:
                if PI > A_line and PI > 7:
                    return "SC", "Clayey sand"
                elif PI < A_line or PI < 4:
                    return "SM", "Silty sand"
                else:
                    return "SC-SM", "Silty clayey sand"
            else: 
                well_graded = (Cu >= 6) and (1 <= Cc <= 3)
                prefix = "SW" if well_graded else "SP"
                suffix = "SC" if (PI > A_line and PI > 4) else "SM"
                return f"{prefix}-{suffix}", f"Sand with silt/clay ({prefix}-{suffix})"


def plot_plasticity_chart(LL, PI):
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ll_vals = np.linspace(0, 100, 200)
    a_line = 0.73 * (ll_vals - 20)
    u_line = 0.9 * (ll_vals - 8)
    
    ax.plot(ll_vals, a_line, color='darkred', linestyle='-', linewidth=1.5, label="A-Line [PI = 0.73(LL-20)]")
    ax.plot(ll_vals, u_line, color='black', linestyle=':', linewidth=1.0, label="U-Line [PI = 0.9(LL-8)]")
    ax.axvline(50, color='gray', linestyle='--', alpha=0.7, label="LL = 50%")
    
    ax.fill_between(ll_vals[ll_vals>=20], a_line[ll_vals>=20], 60, where=(ll_vals[ll_vals>=20]>=50), color='#ef9a9a', alpha=0.3, label="CH / OH")
    ax.fill_between(ll_vals, 0, a_line, where=(ll_vals>=50), color='#ffe082', alpha=0.3, label="MH / OH")
    ax.fill_between(ll_vals[(ll_vals>=15.7) & (ll_vals<50)], a_line[(ll_vals>=15.7) & (ll_vals<50)], 60, color='#90caf9', alpha=0.3, label="CL")
    ax.fill_between(ll_vals[ll_vals<50], 0, a_line[ll_vals<50], where=(ll_vals[ll_vals<50]<50), color='#a5d6a7', alpha=0.3, label="ML")
    
    ax.scatter([LL], [PI], color='blue', s=100, zorder=6, edgecolor='black', label=f"Soil Sample (LL={LL:.1f}, PI={PI:.1f})")
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.set_xlabel("Liquid Limit, LL (%)", fontsize=9, fontweight='bold')
    ax.set_ylabel("Plasticity Index, PI (%)", fontsize=9, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc="upper left", fontsize=7.5, frameon=True)
    plt.tight_layout()
    return fig


def plot_psd_curve(diameters, passing_percents):
    fig, ax = plt.subplots(figsize=(7, 4.0))
    
    ax.plot(diameters, passing_percents, color='#1565c0', linewidth=2.2, marker='o', markersize=4, label="Particle Size Distribution")
    
    ax.axvline(75.0, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(4.75, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(0.075, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(0.002, color='gray', linestyle='--', alpha=0.5)
    
    ax.text(100, 102, "Cobbles", fontsize=7.5, ha='center', fontweight='bold', color='#424242')
    ax.text(15, 102, "Gravel", fontsize=7.5, ha='center', fontweight='bold', color='#424242')
    ax.text(0.6, 102, "Sand", fontsize=7.5, ha='center', fontweight='bold', color='#424242')
    ax.text(0.015, 102, "Silt", fontsize=7.5, ha='center', fontweight='bold', color='#424242')
    ax.text(0.001, 102, "Clay", fontsize=7.5, ha='center', fontweight='bold', color='#424242')

    ax.set_xscale('log')
    ax.set_xlim(100.0, 0.0005)
    ax.set_ylim(0, 105)
    ax.set_xlabel("Particle Diameter - d (mm) [Log Scale]", fontsize=9, fontweight='bold')
    ax.set_ylabel("Percent Passing (%)", fontsize=9, fontweight='bold')
    ax.grid(True, which="both", linestyle=':', alpha=0.6)
    ax.legend(loc="lower left", fontsize=8)
    plt.tight_layout()
    return fig


# ----------------------------------------------------
# SWCC (SOIL-WATER CHARACTERISTIC CURVE) FUNCTIONS
# ----------------------------------------------------

def van_genuchten_swcc(psi, theta_s, theta_r, alpha, n):
    """
    van Genuchten (1980) Model
    psi: Suction pressure (kPa)
    theta_s: Saturated volumetric water content
    theta_r: Residual volumetric water content
    alpha: Parameter related to the inverse of air-entry value (1/kPa)
    n: Parameter related to pore-size distribution (m = 1 - 1/n)
    """
    m = 1.0 - (1.0 / n)
    # Avoid division by zero at psi = 0
    psi = np.maximum(psi, 1e-4)
    theta = theta_r + (theta_s - theta_r) / ((1.0 + (alpha * psi)**n)**m)
    return theta


def fredlund_xing_swcc(psi, theta_s, a, n, m, hr=300000.0):
    """
    Fredlund & Xing (1994) Model with C(psi) Correction Function
    psi: Suction pressure (kPa)
    theta_s: Saturated volumetric water content
    a: Parameter related to air-entry value (kPa)
    n: Parameter related to the slope of SWCC
    m: Parameter related to residual water content curvature
    hr: Residual suction parameter (default 300,000 kPa)
    """
    psi = np.maximum(psi, 1e-4)
    # Correction function C(psi)
    C_psi = 1.0 - (np.log(1.0 + psi / hr) / np.log(1.0 + 1000000.0 / hr))
    
    # Volumetric water content calculation
    denom = (np.log(np.e + (psi / a)**n))**m
    theta = C_psi * (theta_s / denom)
    return np.maximum(theta, 0.0)


def plot_swcc_curve(model_choice, theta_s, theta_r, vg_alpha, vg_n, fx_a, fx_n, fx_m, fx_hr):
    """
    Plots SWCC Curves based on chosen model(s)
    """
    # Suction values from 0.01 kPa to 1,000,000 kPa (Logarithmic scale)
    psi_vals = np.logspace(-2, 6, 500)
    
    fig, ax = plt.subplots(figsize=(7, 4.2))
    
    if model_choice in ["van Genuchten (1980)", "Both Models"]:
        theta_vg = van_genuchten_swcc(psi_vals, theta_s, theta_r, vg_alpha, vg_n)
        ax.plot(psi_vals, theta_vg, color='#2e7d32', linewidth=2.2, label="van Genuchten (1980)")
        
    if model_choice in ["Fredlund & Xing (1994)", "Both Models"]:
        theta_fx = fredlund_xing_swcc(psi_vals, theta_s, fx_a, fx_n, fx_m, fx_hr)
        ax.plot(psi_vals, theta_fx, color='#c62828', linewidth=2.2, linestyle='--', label="Fredlund & Xing (1994)")
        
    ax.set_xscale('log')
    ax.set_xlim(1e-2, 1e6)
    ax.set_ylim(0, max(theta_s * 1.1, 0.5))
    ax.set_xlabel("Matric Suction, ψ (kPa) [Log Scale]", fontsize=9, fontweight='bold')
    ax.set_ylabel("Volumetric Water Content, θ (m³/m³)", fontsize=9, fontweight='bold')
    ax.grid(True, which="both", linestyle=':', alpha=0.6)
    ax.legend(loc="upper right", fontsize=8, frameon=True)
    plt.tight_layout()
    return fig


# ----------------------------------------------------
# 1. SOIL CLASSIFICATION PAGE
# ----------------------------------------------------
if selected == "Soil Classification":
    st.title("🧪 Advanced Multi-Standard Soil Classification Suite")
    st.caption("Includes Hydrometer Integration, USCS (ASTM D2487), Plasticity Indexes, Extended PSD & SWCC Curve")

    col_in, col_res = st.columns([1.1, 1.2])

    with col_in:
        st.header("1. Classification Standard")
        system = st.radio(
            "Standard System", 
            ["USCS (ASTM D2487)", "AASHTO (M 145)", "BS 5930 / Eurocode 7"],
            key="soil_system_choice"
        )

        st.header("2. Grain Size Analysis Input Method")
        input_method = st.radio(
            "Data Source",
            ["Direct Percentages (Gravel, Sand, Silt, Clay)", "Combined Sieve & Hydrometer Data"],
            key="soil_input_method"
        )

        if input_method == "Direct Percentages (Gravel, Sand, Silt, Clay)":
            gravel = st.number_input("Gravel % (> 4.75mm)", 0.0, 100.0, 15.0, step=0.1)
            sand = st.number_input("Sand % (0.075 - 4.75mm)", 0.0, 100.0, 35.0, step=0.1)
            silt = st.number_input("Silt % (0.002 - 0.075mm)", 0.0, 100.0, 30.0, step=0.1)
            clay = st.number_input("Clay % (< 0.002mm)", 0.0, 100.0, 20.0, step=0.1)
            fines_total = silt + clay
            
            d_arr = np.array([75.0, 19.0, 4.75, 2.0, 0.425, 0.075, 0.02, 0.005, 0.001])
            p_arr = np.array([100.0, 100.0 - gravel*0.3, 100.0 - gravel, 100.0 - gravel - sand*0.3, 100.0 - gravel - sand*0.7, fines_total, clay + silt*0.5, clay, 0.0])

        else:
            st.subheader("Sieve & Hydrometer Testing Data")
            st.caption("Enter Percent Passing for Standard Sizes")
            
            p_3in = st.number_input("3 in (75 mm) % Passing", 0.0, 100.0, 100.0)
            p_no4 = st.number_input("No. 4 (4.75 mm) % Passing", 0.0, 100.0, 85.0)
            p_no10 = st.number_input("No. 10 (2.0 mm) % Passing", 0.0, 100.0, 75.0)
            p_no40 = st.number_input("No. 40 (0.425 mm) % Passing", 0.0, 100.0, 60.0)
            p_no200 = st.number_input("No. 200 (0.075 mm) % Passing", 0.0, 100.0, 40.0)
            
            st.markdown("**Hydrometer Data Points (Fines):**")
            p_02 = st.number_input("D = 0.02 mm % Passing", 0.0, 100.0, 28.0)
            p_005 = st.number_input("D = 0.005 mm % Passing", 0.0, 100.0, 18.0)
            p_002 = st.number_input("D = 0.002 mm % Passing (Clay Fraction)", 0.0, 100.0, 12.0)
            
            d_arr = np.array([75.0, 4.75, 2.0, 0.425, 0.075, 0.02, 0.005, 0.002])
            p_arr = np.array([p_3in, p_no4, p_no10, p_no40, p_no200, p_02, p_005, p_002])
            
            gravel = 100.0 - p_no4
            sand = p_no4 - p_no200
            fines_total = p_no200
            silt = fines_total - p_002
            clay = p_002

        st.header("3. Atterberg Limits & Moisture Content")
        col_a1, col_a2, col_a3 = st.columns(3)
        LL = col_a1.number_input("Liquid Limit (LL)", 0.0, 150.0, 42.0)
        PL = col_a2.number_input("Plastic Limit (PL)", 0.0, 100.0, 20.0)
        w_nat = col_a3.number_input("In-situ Water Content (w %)", 0.0, 150.0, 25.0)
        
        PI = max(0.0, LL - PL)
        LI = (w_nat - PL) / PI if PI > 0 else 0.0
        CI = (LL - w_nat) / PI if PI > 0 else 0.0
        
        is_organic = st.checkbox("Is Organic Soil? (Based on Odor/Color/Oven Dry Test)", value=False)

        st.header("4. Gradation Coefficients")
        col_c1, col_c2 = st.columns(2)
        Cu = col_c1.number_input("Uniformity Coef. (Cu = D60/D10)", 0.0, 100.0, 5.0)
        Cc = col_c2.number_input("Curvature Coef. (Cc = D30^2 / D10*D60)", 0.0, 10.0, 1.2)

        # ----------------------------------------------------
        # SWCC INPUT PARAMETERS SECTION
        # ----------------------------------------------------
        st.header("5. Soil-Water Characteristic Curve (SWCC) Input")
        swcc_model_choice = st.selectbox(
            "Select SWCC Model",
            ["van Genuchten (1980)", "Fredlund & Xing (1994)", "Both Models"],
            key="swcc_model_choice"
        )
        
        theta_s = st.number_input("Saturated Volumetric Water Content (θs)", 0.10, 0.80, 0.45, step=0.01)

        # van Genuchten Parameters
        vg_alpha, vg_n, theta_r = 0.05, 1.5, 0.05
        if swcc_model_choice in ["van Genuchten (1980)", "Both Models"]:
            st.subheader("van Genuchten (1980) Parameters")
            vg_col1, vg_col2, vg_col3 = st.columns(3)
            theta_r = vg_col1.number_input("Residual Water Content (θr)", 0.0, 0.40, 0.05, step=0.01)
            vg_alpha = vg_col2.number_input("α Parameter (1/kPa)", 0.001, 10.0, 0.05, step=0.005)
            vg_n = vg_col3.number_input("n Parameter", 1.01, 10.0, 1.5, step=0.05)

        # Fredlund & Xing Parameters
        fx_a, fx_n, fx_m, fx_hr = 20.0, 1.2, 1.0, 300000.0
        if swcc_model_choice in ["Fredlund & Xing (1994)", "Both Models"]:
            st.subheader("Fredlund & Xing (1994) Parameters")
            fx_col1, fx_col2 = st.columns(2)
            fx_a = fx_col1.number_input("a Parameter (kPa)", 0.1, 10000.0, 20.0, step=1.0)
            fx_n = fx_col2.number_input("n Parameter (Slope)", 0.1, 10.0, 1.2, step=0.1)
            
            fx_col3, fx_col4 = st.columns(2)
            fx_m = fx_col3.number_input("m Parameter (Curvature)", 0.1, 10.0, 1.0, step=0.1)
            fx_hr = fx_col4.number_input("hr Residual Suction (kPa)", 1000.0, 1000000.0, 300000.0, step=10000.0)


    with col_res:
        st.header("📊 Soil Classification Results")
        
        uscs_sym, uscs_name = calculate_uscs(gravel, sand, fines_total, LL, PI, Cu, Cc, is_organic)
        
        st.success(f"""**USCS Symbol:** `{uscs_sym}`

**USCS Group Name:** `{uscs_name}`""")
        
        st.subheader("💡 Atterberg Indices Summary")
        
        if LI > 1:
            state_str = 'Liquid behavior'
        elif 0 <= LI <= 1:
            state_str = 'Plastic behavior'
        else:
            state_str = 'Solid/Semi-solid behavior'

        st.info(f"""
* **Plasticity Index (PI):** `{PI:.1f}%`
* **Liquidity Index (LI):** `{LI:.2f}` (State: {state_str})
* **Consistency Index (CI):** `{CI:.2f}`
""")

        st.subheader("📈 Particle Size Distribution Curve")
        fig_psd = plot_psd_curve(d_arr, p_arr)
        st.pyplot(fig_psd)

        st.subheader("📈 Plasticity Chart (ASTM D2487)")
        fig_plast = plot_plasticity_chart(LL, PI)
        st.pyplot(fig_plast)

        # ----------------------------------------------------
        # SWCC DISPLAY SECTION
        # ----------------------------------------------------
        st.subheader("💧 Soil-Water Characteristic Curve (SWCC)")
        fig_swcc = plot_swcc_curve(
            swcc_model_choice, theta_s, theta_r, 
            vg_alpha, vg_n, 
            fx_a, fx_n, fx_m, fx_hr
        )
        st.pyplot(fig_swcc)

        st.subheader("🧱 Composition Breakdown")
        fig_bar, ax_bar = plt.subplots(figsize=(7, 1.5))
        comps = ['Gravel', 'Sand', 'Silt', 'Clay']
        vals = [gravel, sand, silt, clay]
        clrs = ['#8d6e63', '#d4e157', '#4fc3f7', '#e57373']
        
        left = 0
        for c, v, color in zip(comps, vals, clrs):
            if v > 0:
                ax_bar.barh('Soil Composition', v, left=left, color=color, label=f"{c}: {v:.1f}%")
                if v >= 7.0:
                    ax_bar.text(left + v/2, 0, f"{v:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8)
                left += v
                
        ax_bar.set_xlim(0, 100)
        ax_bar.axis('off')
        ax_bar.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4, frameon=False, fontsize=8)
        plt.tight_layout()
        st.pyplot(fig_bar)

# ----------------------------------------------------
# 2. ISOLATED FOOTING PAGE
# ----------------------------------------------------
elif selected == "Isolated Footing":
    st.title("🏗️ Single Geotechnical & Structural Footing Design Suite")
    # ... (Isolated Footing code remains unchanged)

# ----------------------------------------------------
# 3. CONTINUOUS WALL FOOTING PAGE
# ----------------------------------------------------
elif selected == "Continuous Wall Footing":
    st.title("🧱 Continuous RC Wall Footing Design Suite")
    # ... (Continuous Wall Footing code remains unchanged)
