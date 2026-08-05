import streamlit as st

st.set_page_config(
    page_title="Geotechnical Suite",
    page_icon="🪨",
    layout="wide"
)

st.title("🧱 Geotechnical Engineering Calculation Suite")
st.markdown("""
ဤ Web App သည် Geotechnical Engineering တွက်ချက်မှုများအတွက် Tool စုံလင်စွာ ပါဝင်သော Platform ဖြစ်ပါသည်။ 

👈 **ဘေးဘက် Sidebar မီနူးမှ မိမိအသုံးပြုလိုသည့် Tool ကို ရွေးချယ်ပါ:**
* **USCS Classification:** Grain size distribution နှင့် Atterberg limits များဖြင့် မြေဆီလွှာအမျိုးအစားခွဲရန်
* **Bearing Capacity:** Shallow Foundation များ၏ Bearing capacity တွက်ချက်ရန်
* **Slope Stability:** Factor of Safety Analysis ပြုလုပ်ရန်
* **Borehole Visualizer:** Borehole logs နှင့် SPT N-values များကို Dynamic Chart ပြသရန်
""")