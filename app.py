import streamlit as st
import tempfile
import os
import time
import base64
from dotenv import load_dotenv

# Daily & Monthly pipelines
from app.daily_pipeline import run_pipeline
from app.monthly_pipeline import process_final

# ================== ENV ==================
load_dotenv()
# APP_USERNAME = os.getenv("APP_USERNAME")
# APP_PASSWORD = os.getenv("APP_PASSWORD")
APP_USERNAME = "admin"
APP_PASSWORD = "admin"

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="🐝 Honeybee Attendance Engine",
    layout="wide"
)

# ================== GLOBAL CSS ==================
st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-left: 2rem;
    padding-right: 2rem;
    margin: auto;
}
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.card {
    background: white;
    padding: 26px;
    border-radius: 18px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.10);
}
section[data-testid="stFileUploader"] {
    border: 2px dashed #f4b400;
    padding: 16px;
    border-radius: 12px;
    background-color: #fffdf5;
}
button[kind="primary"] {
    background: linear-gradient(90deg, #fbbc04, #f4b400);
    color: black;
    border-radius: 14px;
    height: 3em;
    font-weight: 600;
    font-size: 15px;
}
div[data-testid="stProgress"] > div {
    background-color: #fbbc04;
}
div[data-testid="stAlert"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ================== SESSION STATE ==================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "page" not in st.session_state:
    st.session_state.page = "🐝 Daily Attendance"

# ================== HELPERS ==================
def show_logo():
    logo_path = os.path.join("assets", "logo.png")
    if not os.path.exists(logo_path):
        return

    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-bottom:14px;">
            <img src="data:image/png;base64,{logo_b64}" width="150"/>
        </div>
        """,
        unsafe_allow_html=True
    )

def animated_progress():
    bar = st.progress(0)
    status = st.empty()

    steps = [
        ("🐝 Gathering files", 20),
        ("⚙️ Processing data", 45),
        ("🧮 Reconciling attendance", 70),
        ("📊 Generating report", 90),
        ("✅ Finalizing", 100),
    ]

    current = 0
    for text, target in steps:
        status.markdown(f"**{text}...**")
        while current < target:
            current += 1
            bar.progress(current)
            time.sleep(0.02)

# ================== LOGIN ==================
def login():
    show_logo()
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Login", use_container_width=True):
        if username == APP_USERNAME and password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)

# ================== AUTH GATE ==================
if not st.session_state.authenticated:
    login()
    st.stop()

# ================== LOGOUT ==================
col1, col2 = st.columns([5, 1])
with col2:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ================== PAGE SELECTOR ==================
st.markdown("<br>", unsafe_allow_html=True)

# ===== CSS =====
st.markdown("""
<style>

/* Normal buton */
.mode-btn button {
    width: 100% !important;
    height: 80px !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    border-radius: 16px !important;
    border: 2px solid #e5e7eb !important;
    background-color: white !important;
    color: black !important;
}

/* Hover normal */
.mode-btn button:hover {
    background-color: #f3f4f6 !important;
    border-color: #d1d5db !important;
}

/* Active (Seçili) */
.mode-btn-active button {
    width: 100% !important;
    height: 80px !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    border-radius: 16px !important;
    border: none !important;
    background: linear-gradient(90deg, #16a34a, #22c55e) !important;
    color: white !important;
}

/* Hover selected */
.mode-btn-active button:hover {
    background: linear-gradient(90deg, #15803d, #16a34a) !important;
    color: white !important;
}

/* Streamlit default kırmızı hover override */
button:hover {
    background-color: inherit !important;
}

</style>
""", unsafe_allow_html=True)

daily_active = st.session_state.page == "🐝 Daily Attendance"
monthly_active = st.session_state.page == "📅 Monthly Reconciliation"

col1, col2 = st.columns(2)

with col1:
    container_class = "mode-btn-active" if daily_active else "mode-btn"
    st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
    if st.button("🐝 Daily Attendance", key="daily_mode", use_container_width=True):
        st.session_state.page = "🐝 Daily Attendance"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    container_class = "mode-btn-active" if monthly_active else "mode-btn"
    st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
    if st.button("📅 Monthly Reconciliation", key="monthly_mode", use_container_width=True):
        st.session_state.page = "📅 Monthly Reconciliation"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ================== MAIN APP ==================
show_logo()
st.markdown("<div class='card'>", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>🐝 Honeybee Attendance Engine</h1>",
    unsafe_allow_html=True
)

st.markdown("<hr>", unsafe_allow_html=True)

# ==================================================
# DAILY PAGE
# ==================================================
if st.session_state.page == "🐝 Daily Attendance":

    procare_file = st.file_uploader("Upload Procare Excel", type=["xlsx"])
    if procare_file:
        st.success("✅ Procare file uploaded successfully")

    dhs_file = st.file_uploader("Upload DHS Excel", type=["xls"])
    if dhs_file:
        st.success("✅ DHS file uploaded successfully")

    if st.button(
        "🚀 Generate Daily Report",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_processing
    ):
        if not procare_file or not dhs_file:
            st.error("Please upload both files.")
            st.stop()

        st.session_state.is_processing = True

        with tempfile.TemporaryDirectory() as tmpdir:
            animated_progress()

            procare_path = os.path.join(tmpdir, "procare.xlsx")
            dhs_path = os.path.join(tmpdir, "dhs.xlsx")
            output_path = os.path.join(tmpdir, "final_attendance.xlsx")

            with open(procare_path, "wb") as f:
                f.write(procare_file.read())
            with open(dhs_path, "wb") as f:
                f.write(dhs_file.read())

            run_pipeline(procare_path, dhs_path, output_path)

            with open(output_path, "rb") as f:
                st.success("Report generated!")
                st.download_button(
                    "⬇️ Download Report",
                    data=f,
                    file_name="daily_attendance.xlsx"
                )

        st.session_state.is_processing = False

# ==================================================
# MONTHLY PAGE
# ==================================================
elif st.session_state.page == "📅 Monthly Reconciliation":

    procare_file = st.file_uploader("Upload Procare Excel", type=["xlsx"])
    if procare_file:
        st.success("✅ Procare file uploaded successfully")
    dhs_file = st.file_uploader("Upload DHS File", type=["pdf"])
    if dhs_file:
        st.success("✅ DHS file uploaded successfully")
    auth_file = st.file_uploader("Upload Authorization List", type=["xls"])
    if auth_file:
        st.success("✅ Authorization list uploaded successfully")

    if st.button(
        "🚀 Generate Monthly Report",
        type="primary",
        use_container_width=True
    ):
        if not procare_file or not dhs_file or not auth_file:
            st.error("Please upload all required files.")
            st.stop()

        st.session_state.is_processing = True

        with tempfile.TemporaryDirectory() as tmpdir:

            animated_progress()

            output = process_final(
                procare_file,
                dhs_file,
                auth_file
            )

        st.session_state.is_processing = False

        st.success("Monthly report ready!")

        st.download_button(
            "⬇️ Download Monthly Report",
            data=output,
            file_name="monthly_reconciliation.xlsx"
        )

st.markdown("</div>", unsafe_allow_html=True)
