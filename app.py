import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
from datetime import datetime, timedelta
import io


def generate_demo_data(n=40):
    np.random.seed(42)
    tool_names = [f"Tool {i}" for i in range(1, n + 1)]
    domains = [f"{name.lower().replace(' ', '')}.ai" for name in tool_names]
    categories = np.random.choice(
        ["Collaboration", "Content", "Analytics", "Assistant"], n
    )
    depts = np.random.choice(["HR", "Sales", "IT", "Marketing", "Finance", "Legal"], n)
    user_count = np.random.randint(5, 500, n)
    usage_count = np.random.randint(1, 5000, n)
    start = datetime.now() - timedelta(days=365)
    first_detected = [
        start + timedelta(days=int(x)) for x in np.random.randint(0, 365, n)
    ]
    last_seen = [
        fd + timedelta(days=int(np.random.randint(1, 90))) for fd in first_detected
    ]
    data_types = np.random.choice(
        ["sensitive", "personal", "metadata", "other"], n, p=[0.15, 0.35, 0.35, 0.15]
    )
    vendor_tiers = np.random.choice(
        ["Tier 1", "Tier 2", "Tier 3", "Unknown"], n, p=[0.25, 0.35, 0.25, 0.15]
    )
    df = pd.DataFrame(
        {
            "tool_name": tool_names,
            "domain": domains,
            "category": categories,
            "dept": depts,
            "user_count": user_count,
            "usage_count": usage_count,
            "first_detected": pd.to_datetime(first_detected),
            "last_seen": pd.to_datetime(last_seen),
            "data_type": data_types,
            "vendor_tier": vendor_tiers,
            "risk_score": np.nan,
            "risk_level": "",
        }
    )
    return df


def load_data():
    data_dir = os.path.join(os.getcwd(), "data")
    if os.path.isdir(data_dir):
        csvs = glob.glob(os.path.join(data_dir, "*.csv"))
        for path in csvs:
            try:
                df = pd.read_csv(path)
                expected = {
                    "tool_name",
                    "domain",
                    "category",
                    "dept",
                    "user_count",
                    "usage_count",
                    "first_detected",
                    "last_seen",
                    "data_type",
                    "vendor_tier",
                }
                if expected.issubset(set(df.columns)):
                    df["first_detected"] = pd.to_datetime(
                        df["first_detected"], errors="coerce"
                    )
                    df["last_seen"] = pd.to_datetime(df["last_seen"], errors="coerce")
                    return df
            except Exception:
                continue
    return generate_demo_data()


def infer_controls(row):
    if str(row.get("vendor_tier", "")).lower().startswith("tier 1"):
        return True
    if row.get("usage_count", 0) < 100:
        return True
    return False


def compute_risk_scores(df):
    df = df.copy()
    if "risk_score" not in df.columns:
        df["risk_score"] = np.nan
    dt_map = {"sensitive": 45, "personal": 30, "metadata": 10, "other": 20}
    vt_map = {"Tier 1": 0, "Tier 2": 10, "Tier 3": 20, "Unknown": 15}
    usage = df["usage_count"].fillna(0).astype(float)
    if usage.max() > 0:
        usage_scaled = (usage / usage.max()) * 30
    else:
        usage_scaled = usage * 0
    controls = df.apply(infer_controls, axis=1)
    control_adj = np.where(controls, -15, 0)
    base = df["data_type"].map(dt_map).fillna(20)
    vendor = df["vendor_tier"].map(vt_map).fillna(15)
    computed = base + vendor + usage_scaled + control_adj
    computed = np.clip(computed, 0, 100)
    df.loc[df["risk_score"].isna(), "risk_score"] = computed[df["risk_score"].isna()]
    df["risk_score"] = df["risk_score"].round(0).astype(int)

    def level_from_score(s):
        if s >= 70:
            return "Critical"
        if s >= 50:
            return "High"
        if s >= 30:
            return "Medium"
        return "Low"

    df["risk_level"] = df["risk_score"].apply(level_from_score)
    df["controls_present"] = controls
    return df


def recommended_action(row):
    if row["risk_level"] == "Critical":
        return "Immediate intake + restrict + policy review"
    if row["risk_level"] == "High":
        return "Triage & remediate controls; engage vendor"
    if row["risk_level"] == "Medium":
        return "Monitor, add controls, update policy mapping"
    return "Low priority — document and allow with governance"


def make_executive_summary(df, metrics):
    lines = []
    lines.append("Shadow AI Discovery & Risk Intake — Executive Summary")
    lines.append("")
    lines.append(
        "Disclaimer: Demo uses simulated telemetry; metadata-first; no prompt/content inspection; privacy-aware."
    )
    lines.append("")
    lines.append(f"Total tools detected: {metrics['total_tools']}")
    lines.append(f"High-risk tools (High + Critical): {metrics['high_risk_count']}")
    lines.append(f"Users affected (sum): {metrics['users_affected']}")
    lines.append(f"Average risk score: {metrics['avg_risk']:.1f}")
    lines.append("")
    top = df.sort_values("risk_score", ascending=False).head(5)
    lines.append("Top 5 high-risk tools (illustrative):")
    for _, r in top.iterrows():
        lines.append(
            f"- {r['tool_name']} ({r['domain']}): {r['risk_level']} {r['risk_score']}"
        )
    return "\n".join(lines)


def main():
    st.set_page_config(page_title="Shadow AI Discovery & Risk Intake", layout="wide")

    st.markdown(
        "<style>"
        "body{color:#2A2926;background-color:#FFFFFF}"
        ".metric-card{background:#FAF8F4;border:1px solid #E7DCCE;padding:12px;border-radius:8px}"
        "</style>",
        unsafe_allow_html=True,
    )

    st.title("Shadow AI Discovery & Risk Intake")
    st.markdown(
        "**Disclaimer:** Demo uses simulated telemetry; metadata-first; no prompt/content inspection; privacy-aware."
    )
    st.markdown(
        "Governance-first discovery: enablement and policy-aligned intake and triage."
    )

    # --- Load + prep data ---
    df = load_data()

    for col in ["first_detected", "last_seen"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Shift dates so latest last_seen = today (keeps demo “current”)
    max_date = df["last_seen"].max()
    today = pd.Timestamp.today().normalize()
    delta = today - max_date

    df["first_detected"] = df["first_detected"] + delta
    df["last_seen"] = df["last_seen"] + delta

    df = compute_risk_scores(df)

    # --- Filters ---
    st.sidebar.header("Filters")

    levels = st.sidebar.multiselect(
        "Risk level",
        options=sorted(df["risk_level"].unique().tolist()),
        default=sorted(df["risk_level"].unique().tolist()),
    )

    depts = st.sidebar.multiselect(
        "Department",
        options=sorted(df["dept"].unique().tolist()),
        default=sorted(df["dept"].unique().tolist()),
    )

    cats = st.sidebar.multiselect(
        "Category",
        options=sorted(df["category"].unique().tolist()),
        default=sorted(df["category"].unique().tolist()),
    )

    filtered = df[
        df["risk_level"].isin(levels)
        & df["dept"].isin(depts)
        & df["category"].isin(cats)
    ]

    # --- Metrics ---
    total_tools = int(filtered["tool_name"].nunique())
    high_risk_count = int(
        filtered[filtered["risk_level"].isin(["High", "Critical"])].shape[0]
    )
    users_affected = int(filtered["user_count"].sum())
    avg_risk = float(filtered["risk_score"].mean()) if not filtered.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(
        f"<div class='metric-card'><h3 style='margin:0'>{total_tools}</h3><div>Total tools detected</div></div>",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"<div class='metric-card'><h3 style='margin:0'>{high_risk_count}</h3><div>High-risk count</div></div>",
        unsafe_allow_html=True,
    )
    col3.markdown(
        f"<div class='metric-card'><h3 style='margin:0'>{users_affected}</h3><div>Users affected</div></div>",
        unsafe_allow_html=True,
    )
    col4.markdown(
        f"<div class='metric-card'><h3 style='margin:0'>{avg_risk:.1f}</h3><div>Average risk score</div></div>",
        unsafe_allow_html=True,
    )

    # --- Visuals ---
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Risk distribution")
        fig = px.histogram(
            filtered,
            x="risk_level",
            color="risk_level",
            category_orders={"risk_level": ["Critical", "High", "Medium", "Low"]},
            color_discrete_sequence=["#9b1b00", "#cd8f7a", "#f2c08d", "#d7e3c7"],
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Discovery timeline (first detected)")
        t = filtered.copy()
        t["month"] = (
            pd.to_datetime(t["first_detected"]).dt.to_period("M").dt.to_timestamp()
        )
        timeline = t.groupby("month").size().reset_index(name="count")
        if not timeline.empty:
            fig2 = px.line(timeline, x="month", y="count", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No timeline data in current filter")

    with right:
        st.subheader("Department heatmap")
        pivot = pd.pivot_table(
            filtered,
            index="dept",
            columns="risk_level",
            values="tool_name",
            aggfunc="count",
            fill_value=0,
        )
        if not pivot.empty:
            pivot = pivot[
                [c for c in ["Critical", "High", "Medium", "Low"] if c in pivot.columns]
            ]
            fig3 = px.imshow(
                pivot,
                labels=dict(x="Risk Level", y="Department", color="Count"),
                color_continuous_scale="Reds",
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No department data in current filter")

    # --- Tables ---
    st.subheader("High-risk tools & recommended action (illustrative)")
    high_df = filtered[filtered["risk_level"].isin(["High", "Critical"])].copy()
    if not high_df.empty:
        high_df["recommended_action"] = high_df.apply(recommended_action, axis=1)
        st.dataframe(
            high_df[
                [
                    "tool_name",
                    "domain",
                    "dept",
                    "risk_level",
                    "risk_score",
                    "user_count",
                    "recommended_action",
                ]
            ].sort_values("risk_score", ascending=False),
            use_container_width=True,
        )
    else:
        st.info("No high-risk tools in selected filter")

    st.subheader("Detailed tool view")
    tool_choice = st.selectbox(
        "Select a tool", options=sorted(df["tool_name"].unique().tolist())
    )
    if tool_choice:
        row = df[df["tool_name"] == tool_choice].iloc[0]
        st.markdown(f"**{row['tool_name']}** — {row['domain']}")
        st.markdown(f"- Department: {row['dept']}")
        st.markdown(f"- Category: {row['category']}")
        st.markdown(f"- Users: {row['user_count']}")
        st.markdown(f"- Usage (approx): {row['usage_count']}")
        st.markdown(f"- Data type: {row['data_type']}")
        st.markdown(f"- Vendor tier: {row['vendor_tier']}")
        st.markdown(f"- Risk: {row['risk_level']} ({row['risk_score']})")
        st.markdown(f"- Controls present: {row['controls_present']}")

    # --- Exports ---
    st.markdown("---")
    st.subheader("Exports")

    buf_full = io.StringIO()
    df.to_csv(buf_full, index=False)
    buf_full.seek(0)
    st.download_button(
        "Download full report (CSV)",
        data=buf_full.getvalue(),
        file_name="shadow_ai_full_report.csv",
        mime="text/csv",
        key="dl_full",
    )

    buf_high = io.StringIO()
    high_df.to_csv(buf_high, index=False)
    buf_high.seek(0)
    st.download_button(
        "Download high-risk CSV",
        data=buf_high.getvalue(),
        file_name="shadow_ai_high_risk.csv",
        mime="text/csv",
        key="dl_high",
    )

    metrics = {
        "total_tools": total_tools,
        "high_risk_count": high_risk_count,
        "users_affected": users_affected,
        "avg_risk": avg_risk,
    }
    summary_txt = make_executive_summary(df, metrics)
    st.download_button(
        "Download executive summary (TXT)",
        data=summary_txt,
        file_name="shadow_ai_exec_summary.txt",
        mime="text/plain",
        key="dl_txt",
    )

    st.markdown("---")
    st.markdown(
        "Built by Adarian Dewberry — [Portfolio](#) | [GitHub](#) | [LinkedIn](#)"
    )


if __name__ == "__main__":
    main()
