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
* **Soil Classification:** Grain size distribution နှင့် Atterberg limits များဖြင့် မြေအမျိုးအစားခွဲရန်
* **Isolated Footing Design:** Shallow Foundation တစ်ခုဖြစ်သော Isolated Footing Design တွက်ချက်ရန်
* **Continuous Wall Footing Design:** Shallow Foundation တစ်ခုဖြစ်သော Continuous Wall Footing Design တွက်ချက်ရန်
""")
