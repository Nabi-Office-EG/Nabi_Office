import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import re

st.set_page_config(page_title="المكتب الرقمي - المواطن", layout="wide")

# الربط بـ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def validate_data(name, nid, phone):
    errors = []
    name_parts = name.strip().split()
    if len(name_parts) < 3: errors.append("الاسم رباعي بالعربي")
    if not (nid.isdigit() and len(nid) == 14): errors.append("الرقم القومي (14 رقم)")
    if not (phone.isdigit() and len(phone) == 11): errors.append("رقم الهاتف (11 رقم)")
    return errors

st.markdown("<h1 style='text-align: center;'>🏛️ المكتب الرقمي - النائب محمد سمير</h1>", unsafe_allow_html=True)

with st.form("complaint_form"):
    n = st.text_input("الاسم الرباعي")
    i = st.text_input("الرقم القومي")
    p = st.text_input("رقم الهاتف")
    r = st.text_input("محل الإقامة")
    d = st.text_area("تفاصيل الشكوى")
    f = st.file_uploader("صورة البطاقة الشخصية", type=['jpg','png','jpeg'])

    if st.form_submit_button("إرسال الشكوى"):
        errs = validate_data(n, i, p)
        if not f: errs.append("صورة البطاقة")
        if errs:
            st.error(f"❌ خطأ في: {', '.join(errs)}")
        else:
            # إضافة الشكوى للجدول المشترك
            existing_data = conn.read(worksheet="complaints")
            new_row = pd.DataFrame([{"name": n, "nat_id": i, "res": r, "phone": p, "details": d}])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="complaints", data=updated_df)
            st.success("تم التسليم بنجاح ✅")