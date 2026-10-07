import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
    /* ============ BASE ============ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
        color: #1A1A1A;
    }

    .stApp {
        background-color: #FFFFFF;
    }

    /* ============ TITRES ============ */
    h1, h2, h3 {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1A1A1A;
    }

    h1 { font-size: 2.5rem !important; margin-bottom: 0.25rem !important; }
    h2 { font-size: 1.6rem !important; margin-top: 2rem !important; }
    h3 { font-size: 1.25rem !important; }

    /* ============ SIDEBAR ============ */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EBE6DC;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    /* ============ BOUTONS ============ */
    .stButton > button {
        background-color: #1A1A1A;
        color: #FFFFFF;
        border: 1px solid #1A1A1A;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.15s ease;
        box-shadow: none;
    }
    .stButton > button:hover {
        background-color: #333333;
        border-color: #333333;
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background-color: #D97757;
        border-color: #D97757;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #C25E3E;
    }

    /* ============ METRICS (KPIs) ============ */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #EBE6DC;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        transition: all 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #D97757;
        box-shadow: 0 4px 12px rgba(217,119,87,0.08);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6B6B6B !important;
        font-weight: 500;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'Fraunces', serif;
        font-size: 2rem !important;
        font-weight: 700;
        color: #1A1A1A;
    }

    /* ============ INPUTS ============ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border: 1px solid #EBE6DC !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
        padding: 0.5rem 0.75rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #D97757 !important;
        box-shadow: 0 0 0 3px rgba(217,119,87,0.1) !important;
    }

    /* ============ ONGLETS ============ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid #EBE6DC;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.25rem;
        font-weight: 500;
        color: #6B6B6B;
        background-color: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border-bottom: 2px solid #D97757 !important;
    }

    /* ============ EXPANDERS (dossiers) ============ */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] details summary {
        background-color: #FFFFFF;
        border: 1px solid #EBE6DC;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .streamlit-expanderHeader:hover,
    [data-testid="stExpander"] details summary:hover {
        border-color: #D97757;
        background-color: #FFFCF9;
    }

    /* ============ DIVIDERS ============ */
    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid #EBE6DC;
    }

    /* ============ ALERTES ============ */
    .stAlert {
        border-radius: 10px;
        border: 1px solid #EBE6DC;
    }

    /* ============ CAPTION ============ */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6B6B6B !important;
        font-size: 0.9rem !important;
    }

    /* ============ SCROLLBAR ============ */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #FAF8F4; }
    ::-webkit-scrollbar-thumb { background: #D5CFC4; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #B8B0A0; }

        /* ============ EXPANDERS : badges de statut ============ */
    [data-testid="stExpander"] details summary p {
        font-size: 1rem;
        font-weight: 500;
    }

    /* ============ TITRES DE SECTION ============ */
    h3 {
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    </style>
    """, unsafe_allow_html=True)