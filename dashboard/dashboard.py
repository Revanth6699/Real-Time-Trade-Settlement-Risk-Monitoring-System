import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Trade Risk Dashboard",
    page_icon="📊",
    layout="wide"
)
st_autorefresh(
    interval=5000,
    key="dashboard_refresh"
)

# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "token" not in st.session_state:
    st.session_state.token = ""

if "role" not in st.session_state:
    st.session_state.role = ""
    
params = st.query_params

if (
    not st.session_state.logged_in
    and "token" in params
):

    st.session_state.logged_in = True
    st.session_state.token = params["token"]

    if "username" in params:
        st.session_state.username = params["username"]
        
# =========================================================
# API URL
# =========================================================

import os

API_URL = os.getenv(
    "API_URL",
    "http://api:8000"
)
# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #030712;
    color: white;
}

.block-container{
    padding-top: 0rem;
    padding-bottom: 0.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 96%;
}
.metric-card{
    background: linear-gradient(145deg,#0f172a,#1e2a78);
    padding:15px;
    border-radius:14px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.1);
    margin-bottom:10px;
}

.metric-title{
    font-size:20px;
    font-weight:600;
    color:white;
}

.metric-value{
    font-size:42px;
    font-weight:700;
    color:white;
}
.chart-title{
    font-size:18px;
    font-weight:bold;
    margin-bottom:10px;
    color:white;
}

div[data-testid="stVerticalBlock"] {
    gap: 1rem;
}

hr {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
}

h1 {
    margin-bottom: 0.2rem !important;
}

h4 {
    margin-bottom: 0.2rem !important;
}


.logout-btn{
    margin-top:20px;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# AUTH PAGE
# =========================================================

if not st.session_state.logged_in:

    st.markdown("""
    <h1 style='text-align:center;margin-bottom:20px;'>
    🔐 Trade Risk Dashboard Authentication
    </h1>
    """, unsafe_allow_html=True)

    auth_mode = st.radio(
        "Select",
        ["Login", "Register"],
        horizontal=True
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # =====================================================
    # LOGIN
    # =====================================================

    if auth_mode == "Login":

        if st.button("Login"):

            try:
                response = requests.post(
                    f"{API_URL}/login",
                    data={
                        "username": username,
                        "password": password
                    }
                )
                if response.status_code == 200:

                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.token = response.json().get("access_token")
                    st.session_state.role = response.json().get("role")
                    
                    st.query_params["token"] = st.session_state.token
                    st.query_params["username"] = username                    
                    st.success("Login successful")
                    st.rerun()

                else:
                    st.error(f"Login Failed: {response.text}")

            except Exception as e:
                st.error(f"Login Error: {e}")
                
        if "token" not in st.session_state:
            st.session_state.token = ""

        if "role" not in st.session_state:
            st.session_state.role = ""

    # =====================================================
    # REGISTER
    # =====================================================

    else:

        if st.button("Register"):

            try:
                response = requests.post(
                    f"{API_URL}/register",
                    data={
                        "username": username,
                        "password": password
                    }
                )
                if response.status_code == 200:
                    st.success("Registration successful")

                else:
                    st.error(f"Registration Failed: {response.text}")

            except Exception as e:
                st.error(f"Backend Error: {e}")

# =========================================================
# DASHBOARD
# =========================================================

else:

    st.markdown("""
    <h1 style='text-align:center;
    font-size:28px;
    margin-top:0px;
    margin-bottom:0px;
    padding-bottom:0px;'>
    Real-Time Trade Settlement Risk Monitoring""", unsafe_allow_html=True)


    st.divider()

    try:

        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        trades_response = requests.get(
            f"{API_URL}/trades",
            headers=headers
        )

        stats_response = requests.get(
            f"{API_URL}/stats",
            headers=headers
        )

        trades = trades_response.json()
        stats = stats_response.json()

        trades_df = pd.DataFrame(trades)

    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()

    if trades_df.empty:
        st.warning("No trade data available")
        st.stop()

    if "timestamp" not in trades_df.columns:

        if "created_at" in trades_df.columns:
            trades_df["timestamp"] = trades_df["created_at"]

        else:
            trades_df["timestamp"] = pd.date_range(
                start="2025-01-01",
                periods=len(trades_df),
                freq="min"
            )

    trades_df["timestamp"] = pd.to_datetime(
        trades_df["timestamp"],
        errors="coerce"
    )

    def fmt(n):
        if isinstance(n, (int, float)):
            if n >= 1_000_000:
                return f"{n/1_000_000:.1f}M"
            if n >= 1_000:
                return f"{n/1_000:.1f}K"
        return str(n)
    
    def money_fmt(x):
        if x >= 1_000_000_000:
            return f"${x/1_000_000_000:.2f}B"
        elif x >= 1_000_000:
            return f"${x/1_000_000:.1f}M"
        elif x >= 1_000:
            return f"${x/1_000:.1f}K"
        return f"${x:.0f}"
    
    failure_rate = 0

    if stats.get("total_trades", 0) > 0:
        failure_rate = round(
            stats["failed_trades"]
            /
            stats["total_trades"]
            * 100,
            2
        )

    k1, k2, k3, k4, k5 = st.columns(5)

    metrics = [
        ("Total Trades", stats.get("total_trades", 0)),
        ("Failed Trades", stats.get("failed_trades", 0)),
        ("High Risk Trades", stats.get("high_risk", 0)),
        ("Anomalies", stats.get("anomalies", 0)),
        ("Failure Rate %", failure_rate)
    ]

    for col, (title, value) in zip(
        [k1, k2, k3, k4, k5],
        metrics
    ):

        col.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-title'>{title}</div>
                <div class='metric-value'>{fmt(value)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # =====================================================
    # CHARTS ROW
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    # -------------------------
    # Settlement Distribution
    # -------------------------

    with c1:
        with st.container(border=True):

            st.markdown(
                "<div class='chart-title'>Settlement Distribution</div>",
                unsafe_allow_html=True
            )

            fig = px.pie(
                trades_df,
                names="settlement_status",
                template="plotly_dark"
            )

            fig.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=20, b=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    # -------------------------
    # Risk Distribution
    # -------------------------

    with c2:
        with st.container(border=True):

            st.markdown(
                "<div class='chart-title'>Risk Distribution</div>",
                unsafe_allow_html=True
            )

            fig = px.histogram(
                trades_df,
                x="risk_score",
                template="plotly_dark"
            )

            fig.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=20, b=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    # -------------------------
    # Broker Exposure
    # -------------------------

    with c3:
        with st.container(border=True):

            st.markdown(
                "<div class='chart-title'>Broker Exposure</div>",
                unsafe_allow_html=True
            )

            broker_exposure = (
                trades_df
                .groupby("broker")["risk_score"]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                broker_exposure,
                x="broker",
                y="risk_score",
                color="risk_score",
                template="plotly_dark"
            )

            fig.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=20, b=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

    # -------------------------
    # Heatmap
    # -------------------------

    with c4:
        with st.container(border=True):

            st.markdown(
                "<div class='chart-title'>Broker vs Settlement Heatmap</div>",
                unsafe_allow_html=True
            )

            heatmap_df = pd.crosstab(
                trades_df["broker"],
                trades_df["settlement_status"]
            )

            fig = px.imshow(
                heatmap_df,
                text_auto=True,
                color_continuous_scale="Plasma"
            )

            fig.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=20, b=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )
    

    left, right = st.columns(2)

    with left:

        st.markdown(
            "<h4 style='margin-bottom:0.3rem;'>📈 Latest 5 Trades</h4>",
            unsafe_allow_html=True
        )
        latest_trades = (
            trades_df
            .sort_values(
                "timestamp",
                ascending=False
            )
            .head(5)
        )

        st.dataframe(
            latest_trades[
                [
                    "trade_id",
                    "asset",
                    "broker",
                    "risk_score",
                    "settlement_status"
                ]
            ].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=140
        )

    with right:

        st.markdown(
            "<h4 style='margin-bottom:0.3rem;'>🚨 Latest 5 Alerts</h4>",
            unsafe_allow_html=True
        )
        latest_alerts = (
            trades_df[
                (trades_df["risk_score"] >= 70)
                |
                (trades_df["anomaly_flag"] == True)
            ]
            .sort_values(
                "timestamp",
                ascending=False
            )
            .head(5)
        )

        st.dataframe(
            latest_alerts[
                [
                    "trade_id",
                    "asset",
                    "broker",
                    "risk_score",
                    "settlement_status"
                ]
            ].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=140
        )


    # =====================================================
    # ADVANCED ANALYTICS DATA
    # =====================================================

    broker_risk = (
        trades_df
        .groupby("broker")
        .agg(
            Avg_Risk=("risk_score", "mean"),
            High_Risk_Trades=(
                "risk_score",
                lambda x: (x >= 70).sum()
            ),
            Failed_Trades=(
                "settlement_status",
                lambda x: (x == "FAILED").sum()
            )
        )
        .reset_index()
    )

    broker_risk["Avg_Risk"] = broker_risk["Avg_Risk"].round(2)

    high_risk_trades = (
        trades_df
        .sort_values(
            "risk_score",
            ascending=False
        )
        .head(20)
    )
    
    completed_trades = len(
        trades_df[
            trades_df["settlement_status"] == "COMPLETED"
        ]
    )

    failed_trades = len(
        trades_df[
            trades_df["settlement_status"] == "FAILED"
        ]
    )

    success_rate = round(
        completed_trades /
        (completed_trades + failed_trades) * 100,
        2
    ) if (completed_trades + failed_trades) > 0 else 0
    
      
    if "show_broker" not in st.session_state:
        st.session_state.show_broker = False

    if "show_risk" not in st.session_state:
        st.session_state.show_risk = False



    # =====================================================
    # KPI POPUP CARDS
    # =====================================================

    st.divider()

    avg_risk = round(
        broker_risk["Avg_Risk"].mean(),
        2
    )

    high_risk_exposure = (
        trades_df[
            trades_df["risk_score"] >= 70
        ]["trade_amount"].sum()
    )
    p1, p2, p3 = st.columns(3)

    with p1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">🏦 Avg Broker Risk</div>
                <div class="metric-value">{avg_risk}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "View Broker Analytics",
            key="broker_popup",
            use_container_width=True
        ):
            st.session_state.show_broker = True
    with p2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">⚠️ High Risk Exposure</div>
                <div class="metric-value">{money_fmt(high_risk_exposure)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button(
            "View High Risk Exposure",
            key="risk_popup",
            use_container_width=True
        ):
            st.session_state.show_risk = True
    with p3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    ✅ Settlement Success Rate
                </div>
                <div class="metric-value">
                    {success_rate}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )    
    
    
    # =====================================================
    # DIALOGS
    # =====================================================

    if st.session_state.get("show_broker", False):
        
        @st.dialog("Broker Analytics")
        def broker_dialog():

            broker_table = (
                broker_risk
                .sort_values(
                    "Avg_Risk",
                    ascending=False
                )
                .reset_index(drop=True)
            )

            broker_table.index = range(
                1,
                len(broker_table) + 1
            )

            st.dataframe(
                broker_table,
                use_container_width=True,
                height=400
            )

            if st.button("Close"):
                st.session_state.show_broker = False
                st.rerun()

        broker_dialog()


    if st.session_state.get("show_risk", False):

        @st.dialog("Top High Risk Trades")
        def risk_dialog():

            risk_table = (
                high_risk_trades[
                    [
                        "trade_id",
                        "asset",
                        "broker",
                        "risk_score",
                        "trade_amount",
                        "settlement_status"
                    ]
                ]
                .reset_index(drop=True)
            )

            risk_table.index = range(
                1,
                len(risk_table) + 1
            )

            st.dataframe(
                risk_table,
                use_container_width=True,
                height=450
            )

            if st.button("Close"):
                st.session_state.show_risk = False
                st.rerun()

        risk_dialog()



    # =====================================================
    # LOGOUT
    # =====================================================
    if st.button("Logout"):

        st.query_params.clear()

        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.token = ""
        st.session_state.role = ""

        st.rerun()