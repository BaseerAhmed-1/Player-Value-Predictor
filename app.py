import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

st.set_page_config(page_title="Player Value Predictor", page_icon="⚽", layout="wide")

# ---------------- Custom styling ----------------
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00d26a; font-size: 1.8rem; }
    h1, h2, h3 { color: #e8e8e8; }
    .player-card {
        background: linear-gradient(135deg, #1a3a2e 0%, #0e1117 100%);
        border: 1px solid #2a5a3e;
        border-radius: 12px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

FEATURES = ["age", "reactions", "composure", "ball_control", "dribbling", "Technical_Skill"]
RADAR_ATTRS = ["reactions", "composure", "ball_control", "dribbling"]

# ---------------- Load & train (cached) ----------------
@st.cache_resource
def load_and_train():
    df = pd.read_csv("PlayerStats.csv")
    df = df.rename(columns={
        "value_euro": "value", "height_cm": "height", "weight_kgs": "weight",
        "nationality": "country", "name": "player"
    })
    df["Technical_Skill"] = df[["ball_control", "dribbling"]].mean(axis=1)

    ml_df = df[FEATURES + ["value"]].dropna()
    X, y = ml_df[FEATURES], ml_df["value"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=20, random_state=42)
    model.fit(X_train, y_train)
    test_r2 = r2_score(y_test, model.predict(X_test))

    return model, scaler, df, ml_df, test_r2

model, scaler, df_full, ml_df, test_r2 = load_and_train()

def predict_value(age, reactions, composure, ball_control, dribbling):
    tech = (ball_control + dribbling) / 2
    row = pd.DataFrame([[age, reactions, composure, ball_control, dribbling, tech]], columns=FEATURES)
    return model.predict(scaler.transform(row))[0]

def fmt_money(v):
    return f"€{v:,.0f}"

def radar_chart(name_a, vals_a, name_b=None, vals_b=None):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_a, theta=RADAR_ATTRS, fill='toself', name=name_a, line_color="#00d26a"))
    if vals_b is not None:
        fig.add_trace(go.Scatterpolar(r=vals_b, theta=RADAR_ATTRS, fill='toself', name=name_b, line_color="#ff6b6b"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                       showlegend=True, template="plotly_dark", height=400)
    return fig

# ---------------- Header ----------------
st.title("⚽ Football Player Value Predictor")
st.caption(f"Random Forest model · Test R² = {test_r2:.3f} · Trained on {len(ml_df):,} players")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Predict & Profile", "⚔️ Compare Players", "🔧 What-If Analysis",
    "🔍 Similar Players", "🏆 Leaderboard & Trends"
])

# ================= TAB 1: Predict & Profile =================
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Player Attributes")
        age = st.slider("Age", 16, 45, 25, key="p1_age")
        reactions = st.slider("Reactions", 1, 100, 65, key="p1_react")
        composure = st.slider("Composure", 1, 100, 65, key="p1_comp")
        ball_control = st.slider("Ball Control", 1, 100, 65, key="p1_bc")
        dribbling = st.slider("Dribbling", 1, 100, 65, key="p1_drib")

        pred = predict_value(age, reactions, composure, ball_control, dribbling)
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        st.metric("Predicted Market Value", fmt_money(pred))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Attribute Profile")
        st.plotly_chart(
            radar_chart("Player", [reactions, composure, ball_control, dribbling]),
            use_container_width=True
        )

# ================= TAB 2: Compare Players =================
with tab2:
    st.subheader("Compare Two Players")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Player A**")
        a_age = st.slider("Age", 16, 45, 22, key="a_age")
        a_react = st.slider("Reactions", 1, 100, 60, key="a_react")
        a_comp = st.slider("Composure", 1, 100, 60, key="a_comp")
        a_bc = st.slider("Ball Control", 1, 100, 60, key="a_bc")
        a_drib = st.slider("Dribbling", 1, 100, 60, key="a_drib")
        a_val = predict_value(a_age, a_react, a_comp, a_bc, a_drib)
    with colB:
        st.markdown("**Player B**")
        b_age = st.slider("Age", 16, 45, 28, key="b_age")
        b_react = st.slider("Reactions", 1, 100, 75, key="b_react")
        b_comp = st.slider("Composure", 1, 100, 75, key="b_comp")
        b_bc = st.slider("Ball Control", 1, 100, 75, key="b_bc")
        b_drib = st.slider("Dribbling", 1, 100, 75, key="b_drib")
        b_val = predict_value(b_age, b_react, b_comp, b_bc, b_drib)

    m1, m2 = st.columns(2)
    m1.metric("Player A Value", fmt_money(a_val))
    m2.metric("Player B Value", fmt_money(b_val), delta=fmt_money(b_val - a_val))

    st.plotly_chart(
        radar_chart("Player A", [a_react, a_comp, a_bc, a_drib],
                     "Player B", [b_react, b_comp, b_bc, b_drib]),
        use_container_width=True
    )

# ================= TAB 3: What-If Analysis =================
with tab3:
    st.subheader("What-If: How does one attribute change value?")
    base_age = st.slider("Base Age", 16, 45, 25, key="w_age")
    base_react = st.slider("Base Reactions", 1, 100, 65, key="w_react")
    base_comp = st.slider("Base Composure", 1, 100, 65, key="w_comp")
    base_bc = st.slider("Base Ball Control", 1, 100, 65, key="w_bc")
    base_drib = st.slider("Base Dribbling", 1, 100, 65, key="w_drib")

    vary_attr = st.selectbox("Vary which attribute?", ["reactions", "composure", "ball_control", "dribbling", "age"])

    x_range = range(16, 46) if vary_attr == "age" else range(1, 101)
    y_vals = []
    for v in x_range:
        args = dict(age=base_age, reactions=base_react, composure=base_comp,
                    ball_control=base_bc, dribbling=base_drib)
        args[vary_attr] = v
        y_vals.append(predict_value(**args))

    fig = px.line(x=list(x_range), y=y_vals, template="plotly_dark",
                  labels={"x": vary_attr, "y": "Predicted Value (€)"},
                  title=f"Value sensitivity to {vary_attr}")
    fig.update_traces(line_color="#00d26a")
    st.plotly_chart(fig, use_container_width=True)

# ================= TAB 4: Similar Players =================
with tab4:
    st.subheader("Find Similar Real Players")
    s_react = st.slider("Reactions", 1, 100, 65, key="s_react")
    s_comp = st.slider("Composure", 1, 100, 65, key="s_comp")
    s_bc = st.slider("Ball Control", 1, 100, 65, key="s_bc")
    s_drib = st.slider("Dribbling", 1, 100, 65, key="s_drib")

    lookup_df = df_full.dropna(subset=RADAR_ATTRS + ["player", "value"]).copy()
    input_vec = np.array([s_react, s_comp, s_bc, s_drib])
    lookup_df["distance"] = lookup_df[RADAR_ATTRS].apply(
        lambda row: np.linalg.norm(row.values - input_vec), axis=1
    )
    closest = lookup_df.sort_values("distance").head(10)
    display_cols = ["player", "country", "value"] + RADAR_ATTRS
    display_cols = [c for c in display_cols if c in closest.columns]
    st.dataframe(closest[display_cols].reset_index(drop=True), use_container_width=True)

# ================= TAB 5: Leaderboard & Trends =================
with tab5:
    st.subheader("Top 10 Highest-Value Players")
    top_players = df_full.dropna(subset=["value", "player"]).sort_values("value", ascending=False).head(10)
    fig_top = px.bar(top_players, x="value", y="player", orientation="h", template="plotly_dark",
                      color="value", color_continuous_scale="greens")
    fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

    st.subheader("Average Value by Age")
    age_trend = df_full.dropna(subset=["value", "age"]).groupby("age")["value"].median().reset_index()
    fig_age = px.line(age_trend, x="age", y="value", template="plotly_dark",
                       labels={"value": "Median Value (€)"})
    fig_age.update_traces(line_color="#00d26a")
    st.plotly_chart(fig_age, use_container_width=True)
