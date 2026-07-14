"""
streamlit_app.py — Main 5-tab Streamlit dashboard for Olist Churn Analytics.
Run with: streamlit run app/streamlit_app.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title='Olist Churn Analytics',
    page_icon='chart_with_upwards_trend',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*='css'] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f0f2e 50%, #0a0a1a 100%);
    color: #e2e8f0;
}

[data-testid='stSidebar'] {
    background: rgba(15, 15, 46, 0.95);
    border-right: 1px solid rgba(139, 92, 246, 0.3);
}

[data-testid='metric-container'] {
    background: rgba(26, 26, 46, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 12px;
    padding: 16px;
    backdrop-filter: blur(10px);
    transition: transform 0.2s;
}

[data-testid='metric-container']:hover {
    transform: translateY(-2px);
    border-color: rgba(139, 92, 246, 0.6);
}

.stTabs [data-baseweb='tab-list'] {
    gap: 8px;
    background: rgba(15, 15, 46, 0.5);
    border-radius: 12px;
    padding: 4px;
}

.stTabs [data-baseweb='tab'] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 500;
    padding: 8px 16px;
    transition: all 0.2s;
}

.stTabs [aria-selected='true'] {
    background: rgba(139, 92, 246, 0.3) !important;
    color: #c4b5fd !important;
    border: 1px solid rgba(139, 92, 246, 0.5) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 24px;
    transition: all 0.3s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
}

div[data-testid='stDecoration'] { display: none; }
.block-container { padding-top: 1rem !important; }
h1, h2, h3 { color: #c4b5fd !important; }
.stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('# Olist Analytics')
    st.markdown('### Customer Churn & Revenue Leakage')
    st.divider()
    st.markdown('**Dataset:** Brazilian E-commerce (Olist)')
    st.markdown('**Records:** 100k+ real orders')
    st.markdown('**Model:** XGBoost + VADER NLP')
    st.markdown('**Explainability:** SHAP')
    st.divider()
    st.markdown('*Brazilian e-commerce data, 2016–2018*')
    st.markdown('*CC-BY-NC-SA-4.0 License*')

st.markdown("""
<div style='text-align:center; padding: 20px 0 10px 0;'>
    <h1 style='font-size: 2.4rem; background: linear-gradient(135deg, #8b5cf6, #06b6d4);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-weight: 700; margin: 0;'>Olist Churn & Revenue Analytics</h1>
    <p style='color: #94a3b8; margin-top: 8px; font-size: 1.05rem;'>
        End-to-end customer intelligence on 100k+ Brazilian e-commerce orders
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    'Executive Dashboard',
    'Customer Segments',
    'Churn Predictor',
    'Geospatial Analytics',
    'Intervention Simulator'
])

from tabs import tab1_executive, tab2_segments, tab3_churn_predictor, tab4_geospatial, tab5_simulator

with tab1:
    tab1_executive.render()

with tab2:
    tab2_segments.render()

with tab3:
    tab3_churn_predictor.render()

with tab4:
    tab4_geospatial.render()

with tab5:
    tab5_simulator.render()
