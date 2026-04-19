import streamlit as st
import pandas as pd
import sqlite3
import re
import os

st.set_page_config(page_title="المكتب الرقمي - المواطن", layout="wide")

# --- دالة التحقق (تم تحسينها لتكون أكثر مرونة) ---
def validate_data(name, nid, phone, is_booking=False, wa=""):
    errors = []
    name = name.strip()
    nid = nid.strip()
    phone = phone.strip()
    
    # الاسم: عربي و3 كلمات على الأقل
    name_parts = name.split()
    is_arabic = all(re.match(r"^[\u0600-\u06FF]+$", p) for p in name_parts)
    if not is_arabic or len(name_parts) < 3: errors.append("الاسم")
    
    # الرقم القومي: 14 رقم بالتمام والكمال
    if not (nid.isdigit() and len(nid) == 14): errors.append("الرقم القومي")
    
    # رقم الهاتف: يبدأ بـ 010, 011, 012, 015 وطوله 11 رقم
    if not (phone.isdigit() and len(phone) == 11 and phone.startswith(('010', '011', '012', '015'))): 
        errors.append("رقم الهاتف")
        
    if is_booking and not wa.strip(): errors.append("رقم الواتساب")
    return errors

# --- قاعدة البيانات ---
conn = sqlite3.connect('Nabi_System.db', check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS complaints (id INTEGER PRIMARY KEY, name TEXT, nat_id TEXT, res TEXT, phone TEXT, details TEXT, category TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS slots (id INTEGER PRIMARY KEY, day TEXT, t_start TEXT, t_end TEXT, is_booked INTEGER DEFAULT 0)")
conn.execute("CREATE TABLE IF NOT EXISTS confirmed_visits (id INTEGER PRIMARY KEY, name TEXT, nat_id TEXT, phone TEXT, wa TEXT, day TEXT, time TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.execute("INSERT OR IGNORE INTO settings VALUES ('hero_img', 'None'), ('admin_pwd', '2026')")
conn.commit()

# --- عرض الصورة ---
hero_path = pd.read_sql_query("SELECT value FROM settings WHERE key='hero_img'", conn).iloc[0]['value']
if hero_path != "None" and os.path.exists(hero_path):
    st.image(hero_path, use_container_width=True)

st.markdown("<h3 style='text-align: center;'>✨ معاً لتحقيق الحلم ✨</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>🏛️ المكتب الرقمي - النائب محمد سمير</h1>", unsafe_allow_html=True)

t1, t2 = st.tabs(["📝 تقديم شكوى", "🗓️ حجز موعد"])

with t1:
    # شلنا clear_on_submit عشان البيانات ما تضيعش لو فيه غلطة
    with st.form("complaint_form"):
        n = st.text_input("الاسم الرباعي (عربي)")
        i = st.text_input("الرقم القومي (14 رقم)")
        p = st.text_input("رقم الهاتف")
        r = st.text_input("محل الإقامة")
        d = st.text_area("تفاصيل الشكوى")
        f = st.file_uploader("صورة البطاقة الشخصية", type=['jpg','png','jpeg'])

        if st.form_submit_button("إرسال الشكوى"):
            errs = validate_data(n, i, p)
            if not f: errs.append("صورة البطاقة")

            if errs:
                st.error(f"❌ يوجد خطأ في {', '.join(errs)} .. معاً لتحقيق الحلم")
            else:
                conn.execute("INSERT INTO complaints (name, nat_id, res, phone, details, category) VALUES (?,?,?,?,?,?)", (n, i, r, p, d, "Pending"))
                conn.commit()
                st.success("✅ تم الإرسال بنجاح.. معاً لتحقيق الحلم")
                st.balloons() # حركة احتفالية بسيطة

with t2:
    with st.form("booking_form"):
        bn = st.text_input("الاسم الكامل")
        bi = st.text_input("الرقم القومي")
        bp = st.text_input("رقم الهاتف")
        bw = st.text_input("رقم الواتساب")

        sl = pd.read_sql_query("SELECT * FROM slots WHERE is_booked=0", conn)

        if not sl.empty:
            choice = st.selectbox("المواعيد المتاحة", sl.apply(lambda x: f"{x['day']} | {x['t_start']}-{x['t_end']}", axis=1))
            if st.form_submit_button("تأكيد الموعد"):
                errs = validate_data(bn, bi, bp, True, bw)
                if errs:
                    st.error(f"❌ يوجد خطأ في {', '.join(errs)} .. معاً لتحقيق الحلم")
                else:
                    idx = sl.index[sl.apply(lambda x: f"{x['day']} | {x['t_start']}-{x['t_end']}", axis=1) == choice][0]
                    conn.execute("INSERT INTO confirmed_visits (name, nat_id, phone, wa, day, time) VALUES (?,?,?,?,?,?)", (bn, bi, bp, bw, sl.iloc[idx]['day'], sl.iloc[idx]['t_start']))
                    conn.execute("UPDATE slots SET is_booked=1 WHERE id=?", (int(sl.iloc[idx]['id']),))
                    conn.commit()
                    st.success("✅ تم حجز الموعد.. معاً لتحقيق الحلم")
        else:
            st.warning("⚠️ لا توجد مواعيد متاحة حالياً.")
            st.form_submit_button("تأكيد", disabled=True)