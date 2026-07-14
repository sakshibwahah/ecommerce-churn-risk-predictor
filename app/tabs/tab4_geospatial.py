"""
tab4_geospatial.py — Geospatial Analytics: Folium choropleth built at runtime.

Uses Brazil state boundaries via a public GeoJSON source.
Falls back to a Plotly bar chart if the network is unavailable.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import folium
import json
import os
import requests
from utils.data_loader import load_state_summary, load_churn_predictions
from utils.charts import DARK_TEMPLATE, FONT
import plotly.express as px

BRAZIL_GEOJSON_URL = (
    'https://raw.githubusercontent.com/codeforamerica/click_that_hood/'
    'master/public/data/brazil-states.geojson'
)
GEOJSON_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'outputs', 'brazil_states.geojson'
)

STATE_ABBR_TO_NAME = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul', 'RO': 'Rondônia',
    'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
    'SE': 'Sergipe', 'TO': 'Tocantins',
}


@st.cache_data(ttl=86400)
def _load_geojson():
    if os.path.exists(GEOJSON_CACHE):
        with open(GEOJSON_CACHE) as f:
            return json.load(f)
    try:
        resp = requests.get(BRAZIL_GEOJSON_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        with open(GEOJSON_CACHE, 'w') as f:
            json.dump(data, f)
        return data
    except Exception:
        return None


def _detect_name_field(geojson):
    """Return the GeoJSON property key that holds the state name/abbreviation."""
    if not geojson or not geojson.get('features'):
        return None
    props = geojson['features'][0].get('properties', {})
    for key in ('sigla', 'UF', 'abbrev', 'SIGLA', 'id', 'name', 'NOME'):
        if key in props:
            return key
    return list(props.keys())[0] if props else None


def _build_choropleth(state_df: pd.DataFrame, metric: str, label: str,
                      geojson: dict, key_field: str, fmt: str = '.1f') -> folium.Map:
    m = folium.Map(location=[-14.2, -51.9], zoom_start=4,
                   tiles='CartoDB dark_matter')

    # Map abbreviations to GeoJSON key values
    # GeoJSON may store full names — try both abbrev and full name as key
    sample_val = geojson['features'][0]['properties'].get(key_field, '')
    use_full_name = len(sample_val) > 2

    lookup = {}
    for _, row in state_df.iterrows():
        abbr = row['customer_state']
        if use_full_name:
            lookup[STATE_ABBR_TO_NAME.get(abbr, abbr)] = row[metric]
        else:
            lookup[abbr] = row[metric]

    # Inject metric into GeoJSON features
    geo = json.loads(json.dumps(geojson))
    for feat in geo['features']:
        state_key = feat['properties'].get(key_field, '')
        feat['properties']['_metric'] = lookup.get(state_key, 0)
        feat['properties']['_abbr'] = state_key[:2].upper() if not use_full_name else state_key

    folium.Choropleth(
        geo_data=geo,
        data=state_df,
        columns=['customer_state', metric],
        key_on=f'feature.properties.{key_field}' if not use_full_name else f'feature.properties.{key_field}',
        fill_color='YlOrRd',
        fill_opacity=0.75,
        line_opacity=0.4,
        legend_name=label,
        nan_fill_color='#1a1a2e',
    ).add_to(m)

    folium.GeoJson(
        geo,
        tooltip=folium.GeoJsonTooltip(
            fields=[key_field, '_metric'],
            aliases=['State', label],
            localize=True,
            style='background-color: #1a1a2e; color: white; font-family: Inter;'
        ),
        style_function=lambda _: {'fillOpacity': 0, 'weight': 0},
    ).add_to(m)

    return m


def render():
    st.markdown('## Geospatial Analytics')
    st.markdown('*Delivery performance, churn concentration, and revenue at risk across Brazilian states.*')

    state_df = load_state_summary()
    churn_df = load_churn_predictions()

    if state_df.empty:
        st.error('State summary not found. Run the pipeline to generate outputs.')
        return

    # Merge live churn data into state_df if available
    if not churn_df.empty and 'customer_state' in churn_df.columns:
        agg = {}
        if 'churn' in churn_df.columns:
            agg['churn_rate'] = ('churn', 'mean')
        if 'churn_prob' in churn_df.columns:
            agg['avg_churn_prob'] = ('churn_prob', 'mean')
        if 'revenue_at_risk' in churn_df.columns:
            agg['revenue_at_risk'] = ('revenue_at_risk', 'sum')
        if agg:
            churn_state = churn_df.groupby('customer_state').agg(**agg).reset_index()
            state_df = state_df.merge(churn_state, on='customer_state', how='left')

    metric_options = {
        'Churn Rate by State': ('churn_rate', 'Churn Rate', '.1%'),
        'Avg Delivery Delay by State': ('avg_delay_days', 'Avg Delay (days)', '.1f'),
        'Revenue at Risk by State': ('revenue_at_risk', 'Revenue at Risk (BRL)', ',.0f'),
    }
    available = {k: v for k, v in metric_options.items() if v[0] in state_df.columns}

    if not available:
        st.warning('No state metrics available.')
        return

    map_layer = st.selectbox('Select Map Layer', list(available.keys()))
    metric_col, metric_label, _ = available[map_layer]

    geojson = _load_geojson()

    col_map, col_table = st.columns([3, 2])

    with col_map:
        if geojson:
            key_field = _detect_name_field(geojson)
            if key_field:
                m = _build_choropleth(state_df, metric_col, metric_label, geojson, key_field)
                components.html(m._repr_html_(), height=500, scrolling=False)
            else:
                st.warning('Could not parse GeoJSON state boundaries.')
        else:
            st.info('Map unavailable (no network or GeoJSON missing). Showing bar chart.')
            fig = px.bar(
                state_df.sort_values(metric_col, ascending=False).head(15),
                x='customer_state', y=metric_col,
                color=metric_col, color_continuous_scale='YlOrRd',
                labels={'customer_state': 'State', metric_col: metric_label},
                template=DARK_TEMPLATE
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, width='stretch')

    with col_table:
        st.markdown('#### State-Level Summary')
        display_cols = [c for c in ['customer_state', 'total_orders', 'total_revenue',
                                     'on_time_rate', 'avg_delay_days', 'avg_review_score',
                                     'churn_rate', 'revenue_at_risk']
                        if c in state_df.columns]
        st.dataframe(
            state_df[display_cols].sort_values(metric_col, ascending=False)
                                  .round(3)
                                  .reset_index(drop=True),
            width='stretch',
            hide_index=True
        )
