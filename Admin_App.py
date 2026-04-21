import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="لوحة تحكم الإدارة", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

if "auth_role" not in st.session_state: st.session_state.auth_role = None

if st.session_state.auth_role is None:
    st.markdown("<h1 style='text-align: center;'>🔐 تسجيل دخول المسؤول</h1>", unsafe_allow_html=True)
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        # الباسورد اللي أنت اخترتها
        if pwd == "Dev_Master_2026": 
            st.session_state.auth_role = "admin"
            st.rerun()
        else: st.error("❌ كلمة المرور خطأ")
else:
    # قراءة البيانات المشتركة
    df = conn.read(worksheet="complaints")
    
    menu = ["الشكاوى الجماعية", "كافة الشكاوى", "إعدادات"]
    choice = st.sidebar.radio("القائمة", menu)

    if choice == "الشكاوى الجماعية":
        st.subheader("📍 الشكاوى حسب المنطقة")
        if not df.empty:
            for loc, group in df.groupby('res'):
                with st.expander(f"منطقة: {loc} ({len(group)} طلب)"):
                    st.table(group[['name', 'nat_id', 'phone']])
        else: st.info("لا توجد شكاوى حتى الآن")

    elif choice == "كافة الشكاوى":
        st.subheader("📋 جميع البيانات الواردة")
        st.dataframe(df)

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth_role = None
        st.rerun()