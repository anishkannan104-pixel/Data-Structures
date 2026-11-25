import streamlit as st
import os
import sys

# Configure Streamlit Page
st.set_page_config(
    page_title="Adaptive Logistics Intelligence System",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure Project Root in Sys Path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Global Chart Typography Configuration (Enlarged for High Faculty Readability)
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.size': 13,
    'font.family': 'sans-serif',
    'axes.labelsize': 14,
    'axes.titlesize': 15,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 16
})

# Load Database Initialization & Services
from backend.database import init_db, seed_sample_data
init_db()
seed_sample_data()

# Inject Custom CSS (Applied to both Main Canvas and Sidebar)
css_path = os.path.join(PROJECT_ROOT, "frontend", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        css_payload = f"<style>\n{f.read()}\n</style>"
        st.markdown(css_payload, unsafe_allow_html=True)
        st.sidebar.markdown(css_payload, unsafe_allow_html=True)

# Import Pages
from frontend.dashboard import render_dashboard
from frontend.module1 import render_module1
from frontend.module2 import render_module2
from frontend.module3 import render_module3
from frontend.performance import render_performance
from frontend.reports import render_reports

# Sidebar Navigation
st.sidebar.markdown("""
<div style="padding: 0.85rem 0 0.5rem 0; text-align: left;">
    <div style="font-size: 1.65rem; font-weight: 950; color: #0f172a; letter-spacing: -0.035em; line-height: 1.15;">ADAPTIVE LOGISTICS</div>
    <div style="font-size: 1.15rem; font-weight: 800; color: #1d4ed8; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 5px;">Intelligence System</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

PAGES = {
    "Dashboard": render_dashboard,
    "Shipment Processing & Deadline Management": render_module1,
    "Data Management & Integrity": render_module2,
    "Vehicle Assignment & Route Optimization": render_module3,
    "Algorithm Performance Evaluation": render_performance,
    "Reports": render_reports
}

selected_page = st.sidebar.radio(
    "NAVIGATION",
    list(PAGES.keys()),
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 1.1rem; color: #334155; line-height: 1.65; background: #f8fafc; padding: 1.1rem; border-radius: 12px; border: 2px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
    <strong style="color: #0f172a; font-size: 1.22rem; display: block; margin-bottom: 0.4rem;">Engine Architecture:</strong>
    &bull; Core C Shared Library: <code style="font-size: 1.12rem; font-weight: 750; color: #0369a1;">logistics_c.dll</code><br>
    &bull; Database: SQLite (8 Relational Tables)<br>
    &bull; Interop: Python CTypes Bridge<br>
    &bull; Visualization: Matplotlib & NetworkX
</div>
""", unsafe_allow_html=True)

# Render Selected View
render_func = PAGES[selected_page]
render_func()
