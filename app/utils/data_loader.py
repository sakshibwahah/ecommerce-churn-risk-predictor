"""
data_loader.py — Loads precomputed outputs and model artifacts for the Streamlit app.
"""
import os
import json
import pickle
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
MODELS_DIR  = os.path.join(BASE_DIR, 'models')
DB_PATH     = os.path.join(BASE_DIR, 'data', 'olist.db')


@st.cache_resource
def get_engine():
    return create_engine(f'sqlite:///{DB_PATH}')


@st.cache_data
def load_rfm() -> pd.DataFrame:
    path = os.path.join(OUTPUTS_DIR, 'rfm_segments.csv')
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


@st.cache_data
def load_churn_predictions() -> pd.DataFrame:
    path = os.path.join(OUTPUTS_DIR, 'churn_predictions.csv')
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


@st.cache_data
def load_clv() -> pd.DataFrame:
    path = os.path.join(OUTPUTS_DIR, 'churn_predictions.csv')
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


@st.cache_data
def load_state_summary() -> pd.DataFrame:
    path = os.path.join(OUTPUTS_DIR, 'state_summary.csv')
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


@st.cache_data
def load_eda_summary() -> dict:
    path = os.path.join(OUTPUTS_DIR, 'eda_summary.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


@st.cache_resource
def load_model():
    """
    Returns (model, iso_calibrator, scaler, feature_names).
    iso_calibrator may be None if not used.
    """
    model_path    = os.path.join(MODELS_DIR, 'xgb_churn_model.pkl')
    scaler_path   = os.path.join(MODELS_DIR, 'scaler.pkl')
    features_path = os.path.join(MODELS_DIR, 'feature_names.pkl')

    if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
        return None, None, None, None

    with open(model_path,    'rb') as f: artifact = pickle.load(f)
    with open(scaler_path,   'rb') as f: scaler   = pickle.load(f)
    with open(features_path, 'rb') as f: features = pickle.load(f)

    if isinstance(artifact, tuple):
        model, iso = artifact
    else:
        model, iso = artifact, None

    return model, iso, scaler, features
