import streamlit as st
from streamlit_option_menu import option_menu

# --- Page Configuration ---
st.set_page_config(
    page_title="Geotechnical Suite",
    page_icon="🪨",
    layout="wide"
)

# --- Sidebar Navigation Menu ---
with st.sidebar:
    st.title("📌 Main Menu")
    
    # 1. Main Pages Menu
    main_selection = option_menu(
        menu_title=None,
        options=["Home", "Soil Classification"],
        icons=["house-fill", "journal-text"],
        default_index=0,
    )
    
    st.markdown("---")
    st.subheader("🏗️ Shallow Foundation")
    
    # 2. Shallow Foundation Sub-menu
    foundation_selection = option_menu(
        menu_title=None,
        options=["Isolated Footing", "Continuous Wall Footing"],
        icons=["square-fill", "border-style"],
        default_index=-1, # ဘာမှ မရွေးထားသော အနေအထား
    )

# --- Logic to Handle Active Page ---
# ရွေးချယ်မှုအပေါ် မူတည်ပြီး ဘယ် Page ပေါ်ရမလဲ သတ်မှတ်ခြင်း
if foundation_selection is not None:
    page = foundation_selection
else:
    page = main_selection

# --- Page Content Rendering ---

# 1. HOME PAGE
if page == "Home":
    st.title("🧱 Geotechnical Engineering Calculation Suite")
    st.markdown("""
    ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

    👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
    * **Soil Classification:** Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲရန်
    * **Shallow Foundation Design တွက်ချက်ရန်:**
        * **Isolated Footing Design:** Isolated Footing Design တွက်ချက်ရန်
        * **Continuous Wall Footing Design:** Continuous Wall Footing Design တွက်ချက်ရန်
    """)

# 2. SOIL CLASSIFICATION PAGE
elif page == "Soil Classification":
    st.title("🧪 Soil Classification Tool")
    st.info("Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲခြားသည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Soil Classification အတွက် Python Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------

# 3. ISOLATED FOOTING DESIGN PAGE
elif page == "Isolated Footing":
    st.title("📐 Isolated Footing Design")
    st.info("Single/Isolated RC Footing Design တွက်ချက်သည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Isolated Footing အတွက် Python Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------

# 4. CONTINUOUS WALL FOOTING DESIGN PAGE
elif page == "Continuous Wall Footing":
    st.title("🧱 Continuous Wall Footing Design Suite")
    st.info("Continuous RC Wall Footing Design တွက်ချက်သည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Continuous Wall Footing အတွက် ရေးထားသော Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------
