import streamlit as st
import pandas as pd
import sqlite3
import os
import urllib.parse

# --- إعدادات الصفحة ---
st.set_page_config(page_title="لوحة تحكم الإدارة والمصمم", layout="wide")

# --- الاتصال بقاعدة البيانات ---
conn = sqlite3.connect('Nabi_System.db', check_same_thread=False)

def fix_database_structure():
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS complaints (id INTEGER PRIMARY KEY, name TEXT, nat_id TEXT, res TEXT, phone TEXT, details TEXT, category TEXT DEFAULT 'فردية')")
    c.execute("CREATE TABLE IF NOT EXISTS slots (id INTEGER PRIMARY KEY, day TEXT, t_start TEXT, t_end TEXT, is_booked INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS confirmed_visits (id INTEGER PRIMARY KEY, name TEXT, nat_id TEXT, phone TEXT, wa TEXT, day TEXT, time TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('admin_pwd', '2026'), ('hero_img', 'None')")
    conn.commit()

fix_database_structure()

# --- إدارة الدخول ---
if "auth_role" not in st.session_state:
    st.session_state.auth_role = None

if st.session_state.auth_role is None:
    st.markdown("<h1 style='text-align: center;'>🔐 بوابة الإدارة والمصمم</h1>", unsafe_allow_html=True)
    admin_pwd_db = pd.read_sql_query("SELECT value FROM settings WHERE key='admin_pwd'", conn).iloc[0]['value']
    
    pwd_input = st.text_input("أدخل كلمة المرور", type="password")
    if st.button("تسجيل الدخول"):
        if pwd_input == "Dev_Master_2026":
            st.session_state.auth_role = "designer"
            st.rerun()
        elif pwd_input == admin_pwd_db:
            st.session_state.auth_role = "admin"
            st.rerun()
        else:
            st.error("❌ كلمة المرور غير صحيحة")
else:
    role = st.session_state.auth_role
    menu = ["الشكاوى الجماعية", "الشكاوى الفردية", "التقارير", "إدارة المواعيد", "إعدادات الواجهة"]
    if role == "designer": menu.append("🔧 غرفة تصليح المصمم")
    
    choice = st.sidebar.radio("انتقل إلى:", menu)
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth_role = None
        st.rerun()

    # جلب البيانات
    df_all = pd.read_sql_query("SELECT * FROM complaints", conn)
    df_all['res'] = df_all['res'].fillna("غير محدد")

    # --- 1. الشكاوى الجماعية (تجميع ذكي بمحل الإقامة) ---
    if choice == "الشكاوى الجماعية":
        st.header("🤖 نظام التجميع الذكي للشكاوى")
        groups = df_all.groupby('res')
        for loc, group in groups:
            if len(group) > 1: 
                with st.expander(f"📍 محل الإقامة: {loc} | عدد المتقدمين: {len(group)}"):
                    st.info(f"📝 **ملخص المضمون:** {group['details'].iloc[0][:200]}...")
                    st.write("**قائمة المتقدمين:**")
                    st.table(group[['name', 'nat_id', 'phone']])

    # --- 2. الشكاوى الفردية (فرز الأولوية) ---
    elif choice == "الشكاوى الفردية":
        st.header("👤 فرز الشكاوى والطلبات (الأولوية)")
        priority_words = ['عاجل', 'كارثة', 'استغاثة', 'مرض', 'مستشفى', 'موت']
        df_all['priority'] = df_all['details'].apply(lambda x: 1 if any(w in str(x) for w in priority_words) else 0)
        df_sorted = df_all.sort_values(by='priority', ascending=False)
        st.dataframe(df_sorted[['name', 'res', 'phone', 'details']], use_container_width=True)

    # --- 3. التقارير (الاسم + الرقم القومي بجانبه) ---
    elif choice == "التقارير":
        st.header("📊 تقارير المناطق (اسم المواطن والبطاقة)")
        for loc, grp in df_all.groupby('res'):
            st.markdown(f"### 🏛️ منطقة: {loc}")
            st.write(f"إجمالي الطلبات: {len(grp)}")
            report_df = grp[['name', 'nat_id']].copy()
            report_df.columns = ['اسم المواطن', 'الرقم القومي']
            st.table(report_df)
            st.divider()

    # --- 4. إدارة المواعيد + إرسال واتساب ---
    elif choice == "إدارة المواعيد":
        st.header("🗓️ إدارة المواعيد والزيارات")
        t1, t2 = st.tabs(["➕ إضافة مواعيد للجمهور", "✅ الزيارات المحجوزة"])
        
        with t1:
            c1, c2, c3 = st.columns(3)
            with c1: day = st.selectbox("اليوم", ["السبت","الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس"])
            with c2: ts = st.text_input("من")
            with c3: te = st.text_input("إلى")
            if st.button("حفظ الموعد"):
                conn.execute("INSERT INTO slots (day, t_start, t_end) VALUES (?,?,?)", (day, ts, te))
                conn.commit(); st.success("تم الإضافة")

        with t2:
            df_v = pd.read_sql_query("SELECT * FROM confirmed_visits", conn)
            for idx, row in df_v.iterrows():
                with st.container():
                    col_info, col_btn = st.columns([4, 1])
                    col_info.write(f"👤 {row['name']} | 📞 {row['phone']} | 🗓️ {row['day']} - {row['time']}")
                    
                    # زر الواتساب الذكي
                    msg = f"تحية طيبة يا أستاذ {row['name']}. نؤكد لحضرتك ميعاد المقابلة مع النائب محمد سمير يوم {row['day']} في تمام الساعة {row['time']}. معاً لتحقيق الحلم."
                    encoded_msg = urllib.parse.quote(msg)
                    wa_url = f"https://wa.me/2{row['wa']}?text={encoded_msg}"
                    col_btn.markdown(f"[![WhatsApp](https://img.shields.io/badge/WhatsApp-Send-25D366?style=for-the-badge&logo=whatsapp)]({wa_url})", unsafe_allow_html=True)
                    st.divider()

    # --- 5. الإعدادات ---
    elif choice == "إعدادات الواجهة":
        st.header("⚙️ إعدادات النظام")
        new_p = st.text_input("كلمة سر أدمن جديدة", type="password")
        if st.button("تحديث الباسورد"):
            conn.execute("UPDATE settings SET value=? WHERE key='admin_pwd'", (new_p,))
            conn.commit(); st.success("تم")
        
        st.divider()
        up_img = st.file_uploader("تغيير صورة واجهة المواطن")
        if st.button("حفظ الصورة"):
            if up_img:
                if not os.path.exists("assets"): os.makedirs("assets")
                p = f"assets/{up_img.name}"
                with open(p, "wb") as f: f.write(up_img.getbuffer())
                conn.execute("UPDATE settings SET value=? WHERE key='hero_img'", (p,))
                conn.commit(); st.success("تم التحديث")

    # --- 6. غرفة المصمم ---
    elif choice == "🔧 غرفة تصليح المصمم":
        st.header("🛠️ وضع التحكم المطلق")
        if st.button("🧨 حذف جميع الشكاوى"):
            conn.execute("DELETE FROM complaints"); conn.commit(); st.success("تم")