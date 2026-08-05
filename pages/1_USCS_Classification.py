import streamlit as st

st.title("🧪 USCS Soil Classification Tool")

st.sidebar.header("Inputs")
gravel = st.sidebar.number_input("Gravel (%)", 0.0, 100.0, 10.0)
sand = st.sidebar.number_input("Sand (%)", 0.0, 100.0, 40.0)
fines = st.sidebar.number_input("Fines (%)", 0.0, 100.0, 50.0)
LL = st.sidebar.number_input("Liquid Limit (LL)", 0.0, 100.0, 45.0)
PI = st.sidebar.number_input("Plasticity Index (PI)", 0.0, 100.0, 20.0)

if st.button("Classify Soil"):
    if fines >= 50:
        if LL >= 50:
            result = "CH - High Plasticity Clay" if PI > (0.73 * (LL - 20)) else "MH - Elastic Silt"
        else:
            result = "CL - Lean Clay" if PI > (0.73 * (LL - 20)) else "ML - Low Plasticity Silt"
    else:
        result = "Coarse-Grained Soil (Gravel / Sand)"
        
    st.success(f"**USCS Symbol:** {result}")
