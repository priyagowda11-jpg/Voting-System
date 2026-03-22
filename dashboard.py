import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
import plotly.graph_objects as go  # type: ignore
import plotly.express as px  # type: ignore
import numpy as np  # type: ignore
import os
from datetime import datetime, date
import hashlib
import time
from dotenv import load_dotenv  # type: ignore

load_dotenv()  # reads .env locally; Streamlit Cloud uses st.secrets

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Election Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── PALETTE ───────────────────────────────────────────────────────────────────
NAVY = "#106EBE"
NAVY_DK = "#0a4f8c"
NAVY_LT = "#1a82d8"
MINT = "#0FFCBE"
MINT_DK = "#0bd4a0"
BG = "#f4f8fd"
BORDER = "#d6e4f0"
MUTED = "#6b7e93"
TEXT = "#1a2b3c"

C = [
    "#0FFCBE",
    "#106EBE",
    "#f59e0b",
    "#8b5cf6",
    "#ef4444",
    "#1a82d8",
    "#059669",
    "#f472b6",
    "#0ea5e9",
    "#a78bfa",
]

DARK_BG = "#1a2035"
DARK_CARD = "#1e2a45"
DARK_GRID = "rgba(255,255,255,0.06)"

# ── OFFICIALS ─────────────────────────────────────────────────────────────────
OFFICIALS = {
    "admin@election.gov": (
        hashlib.sha256("Admin@123".encode()).hexdigest(),
        "Super Admin",
        "ALL",
    ),
    "delhi@election.gov": (
        hashlib.sha256("Delhi@123".encode()).hexdigest(),
        "Ravi Kumar",
        "Delhi",
    ),
    "mumbai@election.gov": (
        hashlib.sha256("Mumbai@123".encode()).hexdigest(),
        "Priya Shah",
        "Mumbai",
    ),
    "bangalore@election.gov": (
        hashlib.sha256("Blr@123".encode()).hexdigest(),
        "Anita Rao",
        "Bangalore",
    ),
    "chennai@election.gov": (
        hashlib.sha256("Chennai@123".encode()).hexdigest(),
        "Suresh Babu",
        "Chennai",
    ),
}

# ── SESSION INIT ──────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.officer_name = ""
    st.session_state.officer_city = ""

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Roboto:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Roboto', sans-serif !important; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
.stApp { background-color: #f4f8fd !important; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 1200px !important; }

.lp-left {
    background: linear-gradient(160deg, #0a4f8c 0%, #106EBE 55%, #1a82d8 100%);
    border-radius: 20px; padding: 48px 36px; min-height: 560px;
    display: flex; flex-direction: column; justify-content: space-between;
    position: relative; overflow: hidden;
}
.lp-left::before { content:''; position:absolute; bottom:-60px; right:-60px; width:200px; height:200px; background:rgba(15,252,190,0.08); border-radius:50%; }
.lp-left::after  { content:''; position:absolute; top:-40px;  left:-40px;  width:130px; height:130px; background:rgba(15,252,190,0.05); border-radius:50%; }
.lp-icon  { width:52px; height:52px; background:#0FFCBE; border-radius:14px; display:inline-flex; align-items:center; justify-content:center; font-size:26px; margin-bottom:16px; }
.lp-title { font-family:'Playfair Display',serif; font-size:28px; font-weight:800; color:white; line-height:1.25; margin:0 0 10px; }
.lp-sub   { font-size:13px; color:rgba(255,255,255,.65); line-height:1.7; margin:0; }
.lp-feat  { margin:0; padding:0; list-style:none; display:flex; flex-direction:column; gap:13px; }
.lp-feat li { font-size:13px; color:rgba(255,255,255,.85); display:flex; align-items:center; gap:10px; }
.lp-feat li::before { content:''; width:8px; height:8px; background:#0FFCBE; border-radius:50%; flex-shrink:0; }
.lp-footer { font-size:11px; color:rgba(255,255,255,.4); }

.stTextInput > div > div > input {
    border:1.5px solid #d6e4f0 !important; border-radius:10px !important;
    padding:12px 14px !important; font-size:14px !important;
    background:#fafcfe !important; color:#1a2b3c !important;
}
.stTextInput > div > div > input:focus { border-color:#106EBE !important; box-shadow:0 0 0 3px rgba(16,110,190,.10) !important; }
.stTextInput > label { font-weight:500 !important; font-size:13px !important; color:#1a2b3c !important; }

.stButton > button { background:#106EBE !important; color:white !important; border:none !important; border-radius:10px !important; font-weight:600 !important; font-size:15px !important; padding:12px 28px !important; transition:all .2s !important; }
.stButton > button:hover { background:#1a82d8 !important; }

.topnav { background:#106EBE; padding:0 32px; height:68px; display:flex; align-items:center; justify-content:space-between; border-radius:0 0 12px 12px; margin:-1rem -1rem 2rem -1rem; box-shadow:0 4px 20px rgba(16,110,190,.25); }
.brand-row   { display:flex; align-items:center; gap:14px; }
.brand-icon  { width:42px; height:42px; background:#0FFCBE; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:22px; }
.brand-title { font-family:'Playfair Display',serif!important; font-size:18px; font-weight:700; color:#fff; margin:0; }
.brand-sub   { font-size:10px; color:rgba(255,255,255,.6); letter-spacing:1.5px; text-transform:uppercase; margin:0; }
.officer-pill{ background:rgba(15,252,190,.15); border:1px solid rgba(15,252,190,.35); color:#0FFCBE; padding:5px 14px; border-radius:20px; font-size:11px; font-weight:600; }
.city-badge  { background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.25); color:white; padding:5px 14px; border-radius:20px; font-size:12px; font-weight:500; }

div[data-testid="stMetric"] { background:white !important; border:1px solid #d6e4f0 !important; border-radius:14px !important; padding:20px 18px !important; box-shadow:0 2px 12px rgba(16,110,190,.08) !important; transition:transform .2s !important; }
div[data-testid="stMetric"]:hover { transform:translateY(-2px) !important; }
div[data-testid="stMetricLabel"]  { font-size:11px!important; font-weight:600!important; text-transform:uppercase!important; letter-spacing:1px!important; color:#6b7e93!important; }
div[data-testid="stMetricValue"]  { font-family:'Playfair Display',serif!important; font-size:2rem!important; font-weight:800!important; color:#106EBE!important; }
div[data-testid="stMetricDelta"]  { font-size:12px!important; color:#0bd4a0!important; }

.stDataFrame { border-radius:12px!important; border:1px solid #d6e4f0!important; overflow:hidden!important; }
.stDownloadButton>button { background:#106EBE!important; color:white!important; border:none!important; border-radius:10px!important; font-weight:600!important; font-size:13px!important; padding:10px 16px!important; width:100%!important; }
.stDownloadButton>button:hover { background:#1a82d8!important; }
.stSuccess,div[data-testid="stSuccessMessageContainer"] { background:#e6fdf5!important; border-left:4px solid #0bd4a0!important; border-radius:10px!important; }
.stInfo { background:#e8f4fd!important; border-left:4px solid #106EBE!important; border-radius:10px!important; }
hr { border:none!important; border-top:1px solid #d6e4f0!important; margin:1.5rem 0!important; }
.sec-h2 { font-family:'Playfair Display',serif!important; font-size:22px!important; font-weight:700!important; color:#106EBE!important; margin-bottom:4px!important; }
.sec-div { height:3px; width:48px; background:#0bd4a0; border-radius:2px; margin-bottom:14px; }
.turnout-bg   { background:#d6e4f0; border-radius:10px; height:26px; overflow:hidden; margin-bottom:8px; }
.turnout-fill { height:100%; background:linear-gradient(90deg,#106EBE,#0bd4a0); border-radius:10px; display:flex; align-items:center; justify-content:flex-end; padding-right:12px; color:white; font-weight:700; font-size:13px; min-width:50px; }
.dash-footer  { text-align:center; padding:20px; color:#6b7e93; font-size:12px; border-top:1px solid #d6e4f0; margin-top:2rem; }
.dash-footer strong { color:#106EBE; font-family:'Playfair Display',serif; }
</style>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
def check_login(email, pw):
    e = email.strip().lower()
    if e in OFFICIALS:
        h, name, city = OFFICIALS[e]
        if h == hashlib.sha256(pw.encode()).hexdigest():
            return name, city
    return None


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def login_page():
    st.markdown(
        """
    <style>
    [data-testid="column"]:nth-child(2) > div:first-child {
        background: white; border-radius: 20px; border: 1px solid #d6e4f0;
        box-shadow: 0 8px 40px rgba(16,110,190,0.12);
        padding: 40px 36px 36px 36px !important; min-height: 560px;
    }
    [data-testid="column"]:nth-child(1) > div:first-child { min-height: 560px; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1, 1], gap="medium")

    with left_col:
        st.markdown(
            """
        <div class="lp-left">
            <div>
                <div class="lp-icon">🗳️</div>
                <p class="lp-title">Aadhaar<br>Voting System</p>
                <p class="lp-sub">Secure · Verified · Democratic<br>Election Commission Portal</p>
            </div>
            <ul class="lp-feat">
                <li>Real-time vote analytics</li>
                <li>Fraud detection monitoring</li>
                <li>ESP32 fingerprint integration</li>
                <li>Export reports (.xlsx / .csv)</li>
                <li>City-wise officer access</li>
            </ul>
            <div class="lp-footer">Authorized officers only · All activity is logged</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
        <p style="font-family:'Playfair Display',serif;font-size:26px;
            font-weight:700;color:#106EBE;margin:0 0 6px 0;">Welcome Back</p>
        <p style="font-size:14px;color:#6b7e93;margin:0 0 6px 0;">
            Sign in to access the election dashboard</p>
        <div style="height:3px;width:44px;background:#0FFCBE;
            border-radius:2px;margin-bottom:24px;"></div>
        """,
            unsafe_allow_html=True,
        )

        email = st.text_input(
            "Official Email", placeholder="city@election.gov", key="li_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="li_password",
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if st.button("➔  Sign In", use_container_width=True, key="li_btn"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                result = check_login(email, password)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.officer_name = result[0]
                    st.session_state.officer_city = result[1]
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")

        st.markdown(
            """
        <div style="background:#f4f8fd;border:1px solid #d6e4f0;border-radius:10px;
            padding:14px 16px;margin-top:16px;">
            <p style="font-size:11px;color:#6b7e93;font-weight:600;
                text-transform:uppercase;letter-spacing:1px;margin:0 0 6px;">Demo Credentials</p>
            <p style="font-size:12px;color:#106EBE;line-height:2;margin:0;">
                Super Admin &rarr; admin@election.gov / Admin@123<br>
                Delhi &rarr; delhi@election.gov / Delhi@123<br>
                Mumbai &rarr; mumbai@election.gov / Mumbai@123<br>
                Bangalore &rarr; bangalore@election.gov / Blr@123
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# CHART HELPERS — white background, premium styled
# ══════════════════════════════════════════════════════════════════════════════
CP = [
    NAVY,
    MINT_DK,
    "#f59e0b",
    "#8b5cf6",
    "#ef4444",
    "#1a82d8",
    "#059669",
    "#f472b6",
    "#0ea5e9",
    "#a78bfa",
]
CH_BG = "#ffffff"
CH_PLOT = "#ffffff"
CH_GRID = "rgba(210,220,235,0.6)"
CH_TICK = "#9aabbf"
CH_TEXT = TEXT


def _base(title_text, h=340, extra=None):
    b = dict(
        paper_bgcolor=CH_BG,
        plot_bgcolor=CH_PLOT,
        font=dict(family="Roboto, sans-serif", color=CH_TEXT, size=12),
        margin=dict(l=20, r=20, t=56, b=48),
        height=h,
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(size=14, color=NAVY, family="Roboto"),
            x=0.0,
            xanchor="left",
            pad=dict(l=6, t=4),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=CH_TEXT),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        xaxis=dict(
            gridcolor=CH_GRID,
            zeroline=False,
            linecolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=11, color=CH_TICK),
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor=CH_GRID,
            zeroline=False,
            linecolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=11, color=CH_TICK),
            showgrid=True,
        ),
    )
    if extra:
        b.update(extra)
    return b


def plotly_bar(cats, vals, title):
    mx = max(vals) if vals else 1
    fig = go.Figure(
        go.Bar(
            x=cats,
            y=[int(v) for v in vals],
            marker=dict(
                color=CP[: len(cats)], opacity=0.88, line=dict(width=0), cornerradius=6
            ),
            text=[f"<b>{v}</b>" for v in vals],
            textposition="outside",
            textfont=dict(size=13, color=NAVY, family="Roboto"),
            hovertemplate="<b>%{x}</b><br>Votes: %{y}<extra></extra>",
            width=0.55,
        )
    )
    fig.update_layout(
        **_base(
            title,
            extra=dict(
                showlegend=False,
                yaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TICK),
                    range=[0, mx * 1.35],
                    showgrid=True,
                    dtick=max(1, mx // 5),
                ),
                xaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=12, color=CH_TEXT, family="Roboto"),
                    showgrid=False,
                ),
            ),
        )
    )
    return fig


def plotly_horizontal_bar(cats, vals, title):
    mx = max(vals) if vals else 1
    fig = go.Figure(
        go.Bar(
            y=cats,
            x=[int(v) for v in vals],
            orientation="h",
            marker=dict(
                color=CP[: len(cats)], opacity=0.88, line=dict(width=0), cornerradius=4
            ),
            text=[f"  <b>{v}</b>" for v in vals],
            textposition="outside",
            textfont=dict(size=13, color=NAVY, family="Roboto"),
            hovertemplate="<b>%{y}</b><br>Votes: %{x}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base(
            title,
            h=max(280, len(cats) * 56 + 100),
            extra=dict(
                showlegend=False,
                xaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TICK),
                    range=[0, mx * 1.3],
                    showgrid=True,
                    dtick=max(1, mx // 5),
                ),
                yaxis=dict(
                    gridcolor="rgba(0,0,0,0)",
                    zeroline=False,
                    tickfont=dict(size=12, color=CH_TEXT, family="Roboto"),
                    showgrid=False,
                    automargin=True,
                ),
                bargap=0.35,
            ),
        )
    )
    return fig


def plotly_donut(labels, vals, title):
    total = sum(vals)
    mx_i = vals.index(max(vals)) if vals else 0
    pull = [0.05 if i == mx_i else 0 for i in range(len(vals))]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=[int(v) for v in vals],
            hole=0.62,
            pull=pull,
            marker=dict(colors=CP[: len(labels)], line=dict(color="#ffffff", width=3)),
            textinfo="percent+label",
            textfont=dict(size=11, color=CH_TEXT, family="Roboto"),
            hovertemplate="<b>%{label}</b><br>Votes: %{value}<br>%{percent}<extra></extra>",
            insidetextorientation="radial",
        )
    )
    fig.update_layout(
        **_base(
            title,
            h=360,
            extra=dict(
                showlegend=True,
                annotations=[
                    dict(
                        text=(
                            f"<b style='font-size:22px;color:{NAVY}'>{total}</b>"
                            f"<br><span style='font-size:11px;color:{MUTED}'>votes</span>"
                        ),
                        x=0.5,
                        y=0.5,
                        font=dict(size=22, color=NAVY, family="Playfair Display"),
                        showarrow=False,
                    )
                ],
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.22,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11, color=CH_TEXT),
                    bgcolor="rgba(0,0,0,0)",
                ),
            ),
        )
    )
    return fig


def plotly_area(x_vals, y_vals, title):
    y_int = [int(v) for v in y_vals]
    mx = max(y_int) if y_int else 1
    xi = list(range(len(x_vals)))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xi,
            y=y_int,
            mode="none",
            fill="tozeroy",
            fillcolor="rgba(16,110,190,0.10)",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xi,
            y=y_int,
            mode="lines+markers",
            line=dict(color=NAVY, width=3, shape="spline", smoothing=0.8),
            marker=dict(
                color=MINT_DK,
                size=8,
                line=dict(color="#ffffff", width=2),
                symbol="circle",
            ),
            fill="tozeroy",
            fillcolor="rgba(11,212,160,0.08)",
            text=x_vals,
            hovertemplate="<b>%{text}</b><br>Votes: %{y}<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_layout(
        **_base(
            title,
            h=300,
            extra=dict(
                showlegend=False,
                xaxis=dict(
                    tickvals=xi,
                    ticktext=x_vals,
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=10, color=CH_TICK),
                    showgrid=False,
                ),
                yaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TICK),
                    rangemode="tozero",
                    dtick=max(1, mx // 5),
                ),
            ),
        )
    )
    return fig


def plotly_multiline(x_vals, series_dict, title):
    xi = list(range(len(x_vals)))
    fig = go.Figure()
    for i, (name, vals) in enumerate(series_dict.items()):
        y_int = [int(v) for v in vals]
        fig.add_trace(
            go.Scatter(
                x=xi,
                y=y_int,
                name=name,
                mode="lines+markers",
                line=dict(
                    color=CP[i % len(CP)], width=2.8, shape="spline", smoothing=0.8
                ),
                marker=dict(
                    color=CP[i % len(CP)], size=7, line=dict(color="#ffffff", width=1.8)
                ),
                text=x_vals,
                hovertemplate=f"<b>{name}</b> · %{{text}}<br>Votes: %{{y}}<extra></extra>",
            )
        )
    all_vals = [int(v) for s in series_dict.values() for v in s]
    mx = max(all_vals) if all_vals else 1
    fig.update_layout(
        **_base(
            title,
            h=340,
            extra=dict(
                xaxis=dict(
                    tickvals=xi,
                    ticktext=x_vals,
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=10, color=CH_TICK),
                    showgrid=False,
                ),
                yaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TICK),
                    rangemode="tozero",
                    dtick=max(1, mx // 5),
                ),
            ),
        )
    )
    return fig


def plotly_stacked_bar(categories, series, title):
    fig = go.Figure()
    for i, (name, vals) in enumerate(series.items()):
        fig.add_trace(
            go.Bar(
                name=name,
                x=categories,
                y=[int(v) for v in vals],
                marker=dict(
                    color=CP[i % len(CP)],
                    opacity=0.88,
                    line=dict(width=0),
                    cornerradius=4,
                ),
                hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y}} votes<extra></extra>",
            )
        )
    fig.update_layout(
        **_base(
            title,
            h=380,
            extra=dict(
                barmode="stack",
                xaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TEXT),
                    showgrid=False,
                ),
                yaxis=dict(
                    gridcolor=CH_GRID,
                    zeroline=False,
                    tickfont=dict(size=11, color=CH_TICK),
                    rangemode="tozero",
                ),
            ),
        )
    )
    return fig


CHART_CONFIG = dict(displayModeBar=False, responsive=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE  ←  CHANGED: sqlite3 → psycopg2 / Supabase
# ══════════════════════════════════════════════════════════════════════════════
def _get_db_url():
    """
    Priority:
      1. st.secrets["DATABASE_URL"]  — Streamlit Cloud secrets
      2. os.environ["DATABASE_URL"]  — local .env / Render env var
    """
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        return os.environ.get("DATABASE_URL", "")


@st.cache_resource
def get_conn():
    """
    Persistent psycopg2 connection — cached for the whole session.
    sslmode=require is mandatory for Supabase.
    """
    url = _get_db_url()
    if not url:
        st.error("❌ DATABASE_URL is not set. Check your .env or Streamlit secrets.")
        st.stop()
    return psycopg2.connect(url, sslmode="require")


@st.cache_data(ttl=8)
def load_data():
    """
    Load all 4 tables from Supabase via pandas.
    pd.read_sql_query works with psycopg2 connections directly.
    """
    conn = get_conn()
    try:
        voters = pd.read_sql_query("SELECT * FROM voters", conn)
        votes = pd.read_sql_query("SELECT * FROM votes", conn)
        migrated = pd.read_sql_query("SELECT * FROM migrated_votes", conn)
        frauds = pd.read_sql_query("SELECT * FROM fraud_logs", conn)
    except Exception as e:
        # Connection may have timed out — clear cache and reconnect
        st.cache_resource.clear()
        conn = get_conn()
        voters = pd.read_sql_query("SELECT * FROM voters", conn)
        votes = pd.read_sql_query("SELECT * FROM votes", conn)
        migrated = pd.read_sql_query("SELECT * FROM migrated_votes", conn)
        frauds = pd.read_sql_query("SELECT * FROM fraud_logs", conn)
    return voters, votes, migrated, frauds


def filter_city(df, col, city):
    if city == "ALL" or df.empty or col not in df.columns:
        return df
    return df[df[col].str.strip().str.lower() == city.strip().lower()].copy()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD  (unchanged from original)
# ══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    name = st.session_state.officer_name
    city = st.session_state.officer_city
    is_admin = city == "ALL"
    city_lbl = "All Cities" if is_admin else city
    role_lbl = "SUPER ADMIN" if is_admin else f"OFFICER · {city.upper()}"

    st.markdown(
        f"""
    <div class="topnav">
        <div class="brand-row">
            <div class="brand-icon">🗳️</div>
            <div>
                <p class="brand-title">Election Commission Dashboard</p>
                <p class="brand-sub">Live · Secure · Official</p>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
            <span class="city-badge">📍 {city_lbl}</span>
            <span class="officer-pill">⚡ {role_lbl}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        st.caption(f"👤 Logged in as **{name}**  |  ⏱️ {now}")
    with c2:
        st.caption("📡 Auto-refresh every 10s")
    with c3:
        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.officer_name = ""
            st.session_state.officer_city = ""
            st.rerun()

    voters_all, votes_all, migrated_all, frauds_all = load_data()

    voters = filter_city(voters_all, "city", city)
    votes = filter_city(votes_all, "city", city)
    migrated = filter_city(migrated_all, "voting_city", city)

    if (
        not is_admin
        and not frauds_all.empty
        and not voters.empty
        and "aadhaar_no" in voters.columns
    ):
        city_aa = voters["aadhaar_no"].tolist()
        frauds = (
            frauds_all[frauds_all["aadhaar_no"].isin(city_aa)].copy()
            if "aadhaar_no" in frauds_all.columns
            else frauds_all
        )
    else:
        frauds = frauds_all.copy()

    if not frauds.empty and "issue" in frauds.columns:
        frauds_only = frauds[
            ~frauds["issue"].str.lower().str.contains("migrat|city", na=False)
        ].copy()
    else:
        frauds_only = pd.DataFrame()

    total_voters = len(voters)
    total_votes = len(votes) + len(migrated)
    total_migrated = len(migrated)
    fraud_count = len(frauds_only)
    turnout_pct = (total_votes / total_voters * 100) if total_voters > 0 else 0

    if "registration_time" in voters.columns and not voters.empty:
        voters["registration_time"] = pd.to_datetime(
            voters["registration_time"], errors="coerce"
        )
        new_today = len(voters[voters["registration_time"].dt.date == date.today()])
    else:
        new_today = 0

    st.markdown(
        '<p class="sec-h2">📊 Election Overview</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("🧾 Registered", total_voters)
    with k2:
        st.metric("🆕 New Today", new_today)
    with k3:
        st.metric("🗳️ Votes Cast", total_votes)
    with k4:
        st.metric("🌍 Migrated", total_migrated)
    with k5:
        st.metric("⚠️ Fraud Alerts", fraud_count, delta_color="inverse")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-h2">📈 Voter Turnout</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )

    t1, t2 = st.columns([2.2, 1])
    with t1:
        fw = max(int(turnout_pct), 4) if turnout_pct > 0 else 0
        st.markdown(
            f"""
        <div style="background:white;padding:22px 26px;border-radius:14px;
            border:1px solid #d6e4f0;box-shadow:0 2px 12px rgba(16,110,190,.06);">
            <p style="font-family:'Playfair Display',serif;font-size:15px;font-weight:700;color:#106EBE;margin:0 0 12px;">
                Turnout — {city_lbl}</p>
            <div class="turnout-bg"><div class="turnout-fill" style="width:{fw}%;">{turnout_pct:.1f}%</div></div>
            <p style="color:#6b7e93;font-size:13px;margin:6px 0 0;">
                <strong style="color:#106EBE;">{total_votes}</strong> of
                <strong style="color:#106EBE;">{total_voters}</strong> registered voters</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with t2:
        st.metric(
            "📊 Turnout Rate",
            f"{turnout_pct:.1f}%",
            delta=f"{total_votes} votes" if total_votes > 0 else "No votes yet",
        )
        st.metric("👥 Remaining", total_voters - total_votes)

    vlist = []
    if not votes.empty:
        vn = votes.copy()
        vn["vote_type"] = "Normal"
        vn["vote_city"] = vn["city"] if "city" in vn.columns else ""
        vn["reg_city"] = vn["city"] if "city" in vn.columns else ""
        vlist.append(vn)
    if not migrated.empty:
        vm = migrated.copy()
        vm["vote_type"] = "Migrated"
        vm["vote_city"] = vm.get("voting_city", vm.get("city", ""))
        vm["reg_city"] = vm.get("registered_city", vm.get("city", ""))
        vlist.append(vm)

    votes_df = pd.concat(vlist, ignore_index=True) if vlist else pd.DataFrame()
    has_votes = not votes_df.empty and "candidate" in votes_df.columns

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-h2">📊 Vote Analytics</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )

    if has_votes:
        cc = votes_df["candidate"].value_counts()
        cands = cc.index.tolist()
        cvals = cc.values.tolist()

        r1, r2 = st.columns(2)
        with r1:
            st.plotly_chart(
                plotly_bar(cands, cvals, "🏆 Votes per Candidate"),
                use_container_width=True,
                config=CHART_CONFIG,
            )
        with r2:
            st.plotly_chart(
                plotly_donut(cands, cvals, "🍩 Party Vote Share"),
                use_container_width=True,
                config=CHART_CONFIG,
            )

        r3, r4 = st.columns(2)
        with r3:
            si = sorted(range(len(cvals)), key=lambda i: cvals[i])
            st.plotly_chart(
                plotly_horizontal_bar(
                    [cands[i] for i in si], [cvals[i] for i in si], "📊 Party Rankings"
                ),
                use_container_width=True,
                config=CHART_CONFIG,
            )
        with r4:
            if "vote_time" in votes_df.columns:
                vt = votes_df.copy()
                vt["vote_time"] = pd.to_datetime(vt["vote_time"], errors="coerce")
                vt = vt.dropna(subset=["vote_time"])
                if len(vt) > 1:
                    vt["hour"] = vt["vote_time"].dt.strftime("%H:00")
                    hourly = (
                        vt.groupby("hour")
                        .size()
                        .reset_index(name="count")
                        .sort_values("hour")
                    )
                    st.plotly_chart(
                        plotly_area(
                            hourly["hour"].tolist(),
                            hourly["count"].tolist(),
                            "📈 Voting Activity by Hour",
                        ),
                        use_container_width=True,
                        config=CHART_CONFIG,
                    )
                else:
                    st.info("Not enough data for timeline yet.")
            else:
                st.info("No timestamp data available.")

        if "vote_time" in votes_df.columns and len(votes_df) > 2:
            vt2 = votes_df.copy()
            vt2["vote_time"] = pd.to_datetime(vt2["vote_time"], errors="coerce")
            vt2 = vt2.dropna(subset=["vote_time"])
            vt2["hour"] = vt2["vote_time"].dt.strftime("%H:00")
            hours = sorted(vt2["hour"].unique().tolist())
            if len(hours) > 1:
                series = {
                    cand: [
                        len(vt2[(vt2["hour"] == h) & (vt2["candidate"] == cand)])
                        for h in hours
                    ]
                    for cand in cands
                }
                st.plotly_chart(
                    plotly_multiline(hours, series, "📉 Candidate Votes Over Time"),
                    use_container_width=True,
                    config=CHART_CONFIG,
                )

        if is_admin and "vote_city" in votes_df.columns:
            cities = [c for c in votes_df["vote_city"].dropna().unique().tolist() if c]
            if len(cities) > 1:
                series = {
                    cand: [
                        len(
                            votes_df[
                                (votes_df["vote_city"] == c)
                                & (votes_df["candidate"] == cand)
                            ]
                        )
                        for c in cities
                    ]
                    for cand in cands
                }
                st.plotly_chart(
                    plotly_stacked_bar(cities, series, "🏙️ Votes by City × Candidate"),
                    use_container_width=True,
                    config=CHART_CONFIG,
                )

        if is_admin:
            r5, r6 = st.columns(2)
            with r5:
                nc, mc = len(votes), len(migrated)
                if nc + mc > 0:
                    st.plotly_chart(
                        plotly_bar(
                            ["Normal", "Migrated"], [nc, mc], "🌍 Normal vs Migrated"
                        ),
                        use_container_width=True,
                        config=CHART_CONFIG,
                    )
            with r6:
                if "city" in voters_all.columns and not voters_all.empty:
                    cv = voters_all["city"].value_counts()
                    st.plotly_chart(
                        plotly_horizontal_bar(
                            cv.index.tolist()[::-1],
                            cv.values.tolist()[::-1],
                            "🏙️ Voters per City",
                        ),
                        use_container_width=True,
                        config=CHART_CONFIG,
                    )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-h2">🏆 Candidate Results</p><div class="sec-div"></div>',
            unsafe_allow_html=True,
        )
        total_v = sum(cvals)
        res = cc.reset_index()
        res.columns = ["Candidate", "Votes"]
        res["Share %"] = (res["Votes"] / total_v * 100).round(1).astype(str) + "%"
        res.insert(0, "Rank", range(1, len(res) + 1))
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.info("📊 No votes recorded yet. Charts will appear once voting begins.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-h2">⚠️ Fraud Detection</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )

    if not frauds_only.empty:
        fw_df = frauds_only.copy()
        if "aadhaar_no" in fw_df.columns and "aadhaar_no" in voters_all.columns:
            fw_df = fw_df.merge(
                voters_all[["aadhaar_no", "name"]], on="aadhaar_no", how="left"
            )
            fw_df["name"] = fw_df["name"].fillna("Unknown")
        f1, f2, f3 = st.columns(3)
        with f1:
            st.metric(
                "🚫 Duplicate Attempts",
                len(
                    frauds_only[
                        frauds_only["issue"].str.contains(
                            "duplicate|Already", case=False, na=False
                        )
                    ]
                ),
            )
        with f2:
            st.metric(
                "👆 Fingerprint Frauds",
                len(
                    frauds_only[
                        frauds_only["issue"].str.contains(
                            "fingerprint", case=False, na=False
                        )
                    ]
                ),
            )
        with f3:
            st.metric(
                "🔒 Unregistered",
                len(
                    frauds_only[
                        frauds_only["issue"].str.contains(
                            "Unregistered", case=False, na=False
                        )
                    ]
                ),
            )
        with st.expander(
            f"🚨 View All Fraud Attempts ({len(fw_df)} records)", expanded=False
        ):
            dcols = [
                c
                for c in ["name", "aadhaar_no", "issue", "attempt_time"]
                if c in fw_df.columns
            ]
            st.dataframe(
                fw_df[dcols].rename(
                    columns={
                        "name": "Name",
                        "aadhaar_no": "Aadhaar",
                        "issue": "Type",
                        "attempt_time": "Time",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.success("✅ No fraud detected — all votes are legitimate!")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-h2">📡 Live Voting Data</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )
    if not votes_df.empty:
        disp = votes_df.copy()
        if "vote_time" in disp.columns:
            disp = disp.sort_values("vote_time", ascending=False)
        disp = disp.reset_index(drop=True)
        disp.index += 1
        disp.index.name = "Sl.No"

        def hi(row):
            return (
                ["background-color:#e8f4fd;color:#106EBE"] * len(row)
                if row.get("vote_type") == "Migrated"
                else [""] * len(row)
            )

        with st.expander(f"📋 All Votes ({len(disp)} records)", expanded=False):
            st.dataframe(
                disp.style.apply(hi, axis=1), use_container_width=True, height=360
            )
    else:
        st.info("No votes recorded yet.")

    if is_admin and not voters_all.empty:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-h2">👥 Voter Registry</p><div class="sec-div"></div>',
            unsafe_allow_html=True,
        )
        with st.expander(
            f"📋 Full Registry ({len(voters_all)} voters)", expanded=False
        ):
            st.dataframe(voters_all, use_container_width=True, hide_index=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-h2">📥 Export</p><div class="sec-div"></div>',
        unsafe_allow_html=True,
    )
    e1, e2, e3, e4 = st.columns(4)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    with e1:
        if not voters.empty:
            st.download_button(
                "📊 Voters List",
                voters.to_csv(index=False).encode(),
                f"voters_{city}_{ts}.csv",
                "text/csv",
                use_container_width=True,
            )
    with e2:
        if not frauds_only.empty:
            st.download_button(
                "⚠️ Fraud Logs",
                frauds_only.to_csv(index=False).encode(),
                f"fraud_{city}_{ts}.csv",
                "text/csv",
                use_container_width=True,
            )
    with e3:
        if not votes_df.empty:
            st.download_button(
                "🗳️ Voting Data",
                votes_df.to_csv(index=False).encode(),
                f"votes_{city}_{ts}.csv",
                "text/csv",
                use_container_width=True,
            )
    with e4:
        rpt = pd.DataFrame(
            {
                "Metric": [
                    "Registered",
                    "New Today",
                    "Votes Cast",
                    "Migrated",
                    "Fraud Alerts",
                    "Turnout %",
                    "Scope",
                    "Officer",
                    "Generated",
                ],
                "Value": [
                    total_voters,
                    new_today,
                    total_votes,
                    total_migrated,
                    fraud_count,
                    f"{turnout_pct:.1f}%",
                    city_lbl,
                    name,
                    now,
                ],
            }
        )
        st.download_button(
            "📋 Full Report",
            rpt.to_csv(index=False).encode(),
            f"report_{city}_{ts}.csv",
            "text/csv",
            use_container_width=True,
        )

    st.markdown(
        """
    <div class="dash-footer">
        <strong>Election Commission of India — Aadhaar Voting System</strong><br>
        Secure · Verified · Democratic &nbsp;|&nbsp; Built by Priya G
    </div>
    """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    login_page()
else:
    show_dashboard()
    time.sleep(10)
    st.rerun()
