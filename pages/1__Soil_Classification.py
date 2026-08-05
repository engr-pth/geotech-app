import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Multi-Standard Soil Classification", page_icon="🧪", layout="wide")
st.title("🧪 Multi-Standard Soil Classification Suite")
st.caption("Supports USCS (ASTM D2487), AASHTO (M 145), BS 5930 / Eurocode 7, and IS 1498 (Indian Standard)")

col_in, col_res = st.columns([1, 1.2])

with col_in:
    st.header("1. Sieve Analysis Inputs (%)")
    gravel = st.number_input("Gravel (> 4.75mm) %", 0.0, 100.0, 15.0)
    sand = st.number_input("Sand (0.075mm - 4.75mm) %", 0.0, 100.0, 35.0)
    fines = st.number_input("Fines (< 0.075mm / No. 200) %", 0.0, 100.0, 50.0)
    
    st.header("2. Atterberg Limits (%)")
    LL = st.number_input("Liquid Limit (LL)", 0.0, 150.0, 45.0)
    PL = st.number_input("Plastic Limit (PL)", 0.0, 100.0, 20.0)
    PI = max(0.0, LL - PL)
    st.info(f"**Plasticity Index (PI):** `{PI:.1f}%`")
    
    st.header("3. Grain Size Distribution (Optional)")
    Cu = st.number_input("Uniformity Coefficient (Cu)", 0.0, 50.0, 4.0)
    Cc = st.number_input("Coefficient of Curvature (Cc)", 0.0, 10.0, 1.0)
    
    st.header("4. Select Primary Classification Standard")
    system = st.radio("Standard", ["USCS (ASTM D2487)", "AASHTO (M 145)", "BS 5930 / Eurocode", "IS 1498 (Indian Standard)"])

# --- Classification Calculations ---
A_line = 0.73 * (LL - 20) if LL >= 20 else 0.0

# 1. USCS Logic
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

# 2. AASHTO Logic
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

# 3. BS 5930 Logic
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

# 4. IS 1498 Logic (Indian Standard)
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

# Output Display
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
    
    # Plasticity Chart
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
