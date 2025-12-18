import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page config
st.set_page_config(
    page_title="Shadow AI Scanner",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load data with error handling
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/shadow_ai_detections - Sheet1.csv')
        df['first_detected'] = pd.to_datetime(df['first_detected'])
        df['last_seen'] = pd.to_datetime(df['last_seen'])
        return df
    except FileNotFoundError:
        st.error("⚠️ Data file not found. Please ensure shadow_ai_detections - Sheet1.csv is in the data/ folder.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# Sidebar
st.sidebar.title("🔍 Shadow AI Scanner")
st.sidebar.markdown("**Automated AI Tool Discovery & Risk Assessment**")
st.sidebar.markdown("---")

# Filters
st.sidebar.header("Filters")

risk_levels = st.sidebar.multiselect(
    "Risk Level",
    options=['Critical', 'High', 'Medium', 'Low'],
    default=['Critical', 'High', 'Medium', 'Low']
)

departments = st.sidebar.multiselect(
    "Department",
    options=sorted(df['dept'].unique()),
    default=sorted(df['dept'].unique())
)

categories = st.sidebar.multiselect(
    "Tool Category",
    options=sorted(df['category'].unique()),
    default=sorted(df['category'].unique())
)

# Apply filters
filtered_df = df[
    (df['risk_level'].isin(risk_levels)) &
    (df['dept'].isin(departments)) &
    (df['category'].isin(categories))
]

# Sidebar info
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ How Detection Works"):
    st.markdown("""
    **Detection Layers:**
    
    1. **Network Traffic Analysis**
       - DNS queries to AI services
       - API endpoint detection
    
    2. **Browser Extension Scanning**
       - Inventory AI extensions
       - Permission analysis
    
    3. **SaaS App Discovery**
       - CASB integration
       - AI feature identification
    
    4. **API Monitoring**
       - Usage pattern analysis
       - Data sensitivity tracking
    """)

with st.sidebar.expander("📊 Risk Scoring"):
    st.markdown("""
    **Score = 0-100 based on:**
    
    - Data Sensitivity (0-40 pts)
    - Vendor Risk (0-30 pts)
    - Usage Volume (0-20 pts)
    - Control Gaps (0-10 pts)
    
    **Risk Levels:**
    - 🔴 Critical: 70-100
    - 🟠 High: 50-69
    - 🟡 Medium: 30-49
    - 🟢 Low: 0-29
    """)

# Main content
st.title("🔍 Shadow AI Scanner Dashboard")
st.markdown("**Discover, Assess, and Govern Unauthorized AI Tool Usage**")

# Scan simulation
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 🚀 Simulated Organizational Scan")
    st.markdown("*This demo uses realistic sample data to demonstrate scanner capabilities*")

with col2:
    if st.button("▶️ Run Scan", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status = st.empty()
        
        steps = [
            ("Scanning network traffic", 20),
            ("Analyzing browser extensions", 40),
            ("Checking SaaS applications", 60),
            ("Monitoring API calls", 80),
            ("Calculating risk scores", 100)
        ]
        
        for step, prog in steps:
            status.text(f"🔄 {step}...")
            import time
            time.sleep(0.3)
            progress_bar.progress(prog)
        
        status.text("✅ Scan complete!")
        st.balloons()

st.markdown("---")

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_tools = len(filtered_df)
    recent_tools = len(filtered_df[filtered_df['first_detected'] > (datetime.now() - timedelta(days=30))])
    st.metric(
        "Total AI Tools",
        total_tools,
        f"+{recent_tools} last 30 days"
    )

with col2:
    critical = len(filtered_df[filtered_df['risk_level'] == 'Critical'])
    high = len(filtered_df[filtered_df['risk_level'] == 'High'])
    st.metric(
        "High-Risk Tools",
        critical + high,
        f"{critical} Critical",
        delta_color="inverse"
    )

with col3:
    total_users = filtered_df['user_count'].sum()
    st.metric(
        "Users Affected",
        f"{total_users:,}",
        f"Avg {int(total_users/len(filtered_df))} per tool"
    )

with col4:
    avg_risk = filtered_df['risk_score'].mean()
    st.metric(
        "Avg Risk Score",
        f"{avg_risk:.0f}/100",
        "High" if avg_risk >= 50 else "Medium"
    )

st.markdown("---")

# Risk Distribution
st.subheader("📊 Risk Distribution Analysis")

col1, col2 = st.columns(2)

with col1:
    risk_counts = filtered_df['risk_level'].value_counts()
    colors_map = {'Critical': '#d62728', 'High': '#ff7f0e', 'Medium': '#ffd700', 'Low': '#2ca02c'}
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        marker=dict(colors=[colors_map.get(level, '#1f77b4') for level in risk_counts.index]),
        hole=0.4,
        textinfo='label+percent+value',
        textposition='outside'
    )])
    fig_pie.update_layout(
        title="Tools by Risk Level",
        height=350,
        showlegend=True
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    category_counts = filtered_df['category'].value_counts().head(8)
    fig_bar = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        title="Top Tool Categories",
        labels={'x': 'Number of Tools', 'y': ''},
        color=category_counts.values,
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# Department Heatmap
st.subheader("🏢 Department Risk Heatmap")

dept_risk = filtered_df.groupby(['dept', 'risk_level']).size().unstack(fill_value=0)
dept_risk = dept_risk.reindex(columns=['Critical', 'High', 'Medium', 'Low'], fill_value=0)

fig_heat = go.Figure(data=go.Heatmap(
    z=dept_risk.values.T,
    x=dept_risk.index,
    y=dept_risk.columns,
    colorscale=[[0, '#2ca02c'], [0.33, '#ffd700'], [0.66, '#ff7f0e'], [1, '#d62728']],
    text=dept_risk.values.T,
    texttemplate='%{text}',
    textfont={"size": 12},
    hoverongaps=False
))
fig_heat.update_layout(
    title="Shadow AI Tools by Department and Risk Level",
    xaxis_title="Department",
    yaxis_title="Risk Level",
    height=400
)
st.plotly_chart(fig_heat, use_container_width=True)

# Discovery Timeline
st.subheader("📅 Discovery Timeline")

timeline_df = filtered_df.set_index('first_detected').groupby([pd.Grouper(freq='W'), 'risk_level']).size().unstack(fill_value=0)
timeline_df = timeline_df.reindex(columns=['Critical', 'High', 'Medium', 'Low'], fill_value=0)

fig_timeline = go.Figure()
for risk_level, color in colors_map.items():
    if risk_level in timeline_df.columns:
        fig_timeline.add_trace(go.Scatter(
            x=timeline_df.index,
            y=timeline_df[risk_level],
            name=risk_level,
            mode='lines+markers',
            stackgroup='one',
            line=dict(color=color)
        ))

fig_timeline.update_layout(
    title="New Shadow AI Tools Discovered Over Time (Weekly)",
    xaxis_title="Week",
    yaxis_title="Number of Tools",
    height=400,
    hovermode='x unified'
)
st.plotly_chart(fig_timeline, use_container_width=True)

# High Risk Tools Table
st.subheader("⚠️ High-Risk Tools Requiring Immediate Action")

high_risk = filtered_df[filtered_df['risk_level'].isin(['Critical', 'High'])].sort_values('risk_score', ascending=False)

def get_action(score):
    if score >= 80:
        return "🚫 Block immediately"
    elif score >= 70:
        return "⚠️ Require approval"
    else:
        return "📋 Security review"

high_risk['action'] = high_risk['risk_score'].apply(get_action)

display_cols = ['tool_name', 'category', 'dept', 'user_count', 'risk_score', 'risk_level', 'data_type', 'action']
st.dataframe(
    high_risk[display_cols].head(15),
    use_container_width=True,
    height=400
)

# Detailed Tool View
st.subheader("🔎 Detailed Tool Analysis")

tool_names = sorted(filtered_df['tool_name'].unique())
selected = st.selectbox("Select a tool for detailed analysis:", tool_names)

if selected:
    tool = filtered_df[filtered_df['tool_name'] == selected].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📋 Tool Information**")
        st.markdown(f"""
        - **Name:** {tool['tool_name']}
        - **Domain:** `{tool['domain']}`
        - **Category:** {tool['category']}
        - **First Detected:** {tool['first_detected'].strftime('%Y-%m-%d')}
        - **Last Seen:** {tool['last_seen'].strftime('%Y-%m-%d')}
        """)
    
    with col2:
        st.markdown("**⚠️ Risk Assessment**")
        risk_emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}
        st.markdown(f"""
        - **Risk Score:** {tool['risk_score']}/100
        - **Risk Level:** {risk_emoji.get(tool['risk_level'], '')} {tool['risk_level']}
        - **Data Type:** {tool['data_type']}
        - **Vendor Tier:** {tool['vendor_tier']}
        - **Usage Count:** {tool['usage_count']:,} interactions
        """)
    
    with col3:
        st.markdown("**👥 Impact & Actions**")
        st.markdown(f"""
        - **Users Affected:** {tool['user_count']}
        - **Department:** {tool['dept']}
        - **Recommended Action:** {get_action(tool['risk_score'])}
        
        **Next Steps:**
        1. Contact department head
        2. Assess business need
        3. Evaluate alternatives
        4. Implement controls
        """)

# Export
st.markdown("---")
st.subheader("📥 Export Reports")

col1, col2, col3 = st.columns(3)

with col1:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        "📄 Download Full Report (CSV)",
        csv,
        f"shadow_ai_scan_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

with col2:
    high_csv = high_risk.to_csv(index=False)
    st.download_button(
        "⚠️ Download High-Risk Tools (CSV)",
        high_csv,
        f"high_risk_tools_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )

with col3:
    summary = f"""
    SHADOW AI SCAN SUMMARY
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    Total Tools Detected: {len(filtered_df)}
    Critical Risk: {len(filtered_df[filtered_df['risk_level']=='Critical'])}
    High Risk: {len(filtered_df[filtered_df['risk_level']=='High'])}
    Total Users Affected: {filtered_df['user_count'].sum()}
    Average Risk Score: {filtered_df['risk_score'].mean():.1f}/100
    
    Top 5 High-Risk Tools:
    {chr(10).join([f"{i+1}. {row['tool_name']} - Risk: {row['risk_score']}" for i, row in high_risk.head(5).iterrows()])}
    """
    st.download_button(
        "📊 Download Executive Summary",
        summary,
        f"executive_summary_{datetime.now().strftime('%Y%m%d')}.txt",
        "text/plain"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <strong>Shadow AI Scanner</strong> | Built by AD Dewberry<br>
    Automated detection and risk assessment of unauthorized AI tool usage<br>
    <a href='https://adariandewberry.com'>Portfolio</a> | 
    <a href='https://github.com/yourusername/shadow-ai-scanner'>GitHub</a> | 
    <a href='https://linkedin.com/in/adariandewberry'>LinkedIn</a>
</div>
""", unsafe_allow_html=True)
```

---

### **Step 3: Paste It**

1. **Select ALL the code above** (click before `import`, scroll to bottom, Shift+click after the last line)

2. **Copy it:** Ctrl+C (Windows) or Cmd+C (Mac)

3. **Go to VS Code** and click inside your blank `app.py` file

4. **Paste:** Ctrl+V (Windows) or Cmd+V (Mac)

5. **Save:** Ctrl+S (Windows) or Cmd+S (Mac)

**You should now see LOTS of colorful code in your app.py file!**

---

### **Step 4: Create requirements.txt**

1. **Hover over "SHADOW-AI-SCANNER"** again in the left sidebar

2. **Click the "New File" icon** (📄)

3. **Type:** `requirements.txt`

4. **Press Enter**

5. **Paste this into the blank file:**
```
streamlit==1.29.0
pandas==2.1.4
plotly==5.18.0
numpy==1.26.2
```

6. **Save:** Ctrl+S

---

## **STATUS CHECK:**

**Your left sidebar should now show:**
```
▼ SHADOW-AI-SCANNER
  ▶ data/
  app.py