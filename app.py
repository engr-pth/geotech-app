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
    selected = option_menu(
        menu_title="Main Menu",
        options=[
            "Home", 
            "Soil Classification", 
            "Isolated Footing", 
            "Continuous Wall Footing"
        ],
        icons=[
            "house-fill", 
            "journal-text", 
            "square-fill", 
            "border-style"
        ],
        # Menu မှာ Sub-group စာသားပုံစံပြချင်ရင် ရိုးရှင်းစွာပဲ နာမည်တပ်နိုင်ပါတယ်
        menu_icon="cast",
        default_index=0,
        key="main_menu_nav" # Session state conflict မဖြစ်အောင် key သီးသန့်ပေးထားပါသည်
    )

# --- Page Content Rendering ---

# 1. HOME PAGE
if selected == "Home":
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
elif selected == "Soil Classification":
    st.title("🧪 Soil Classification Tool")
    st.info("Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲခြားသည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Soil Classification အတွက် Python Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------

# 3. ISOLATED FOOTING DESIGN PAGE
elif selected == "Isolated Footing":
    st.title("📐 Isolated Footing Design")
    st.info("Single/Isolated RC Footing Design တွက်ချက်သည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Isolated Footing အတွက် Python Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------

# 4. CONTINUOUS WALL FOOTING DESIGN PAGE
elif selected == "Continuous Wall Footing":
    st.title("🧱 Continuous Wall Footing Design Suite")
    st.info("Continuous RC Wall Footing Design တွက်ချက်သည့် Tool ဖြစ်ပါသည်။")
    # -------------------------------------------------------------
    # Continuous Wall Footing အတွက် ရေးထားသော Code များကို ဤနေရာတွင် ထည့်ပါ
    # -------------------------------------------------------------
