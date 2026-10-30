import json
import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="depcheck-ai | AI Dependency Security Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for state-of-the-art Dark Cyber Glassmorphic UI
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Global Reset & Base */
:root {
    --bg-dark: #07090e;
    --card-bg: rgba(17, 24, 39, 0.75);
    --card-border: rgba(255, 255, 255, 0.08);
    --primary-gradient: linear-gradient(135deg, #38bdf8 0%, #6366f1 50%, #a855f7 100%);
    --accent-cyan: #38bdf8;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

html, body, [class*="st-"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
}

.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
                #07090e !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08) !important;
}

/* Header Banner */
.hero-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.hero-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-top: 0.35rem;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* IDE / Editor Container */
.ide-wrapper {
    background: #0d121f;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.6);
    margin-bottom: 1.5rem;
}

.ide-header {
    background: #111827;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.ide-dots {
    display: flex;
    gap: 6px;
}

.ide-dot {
    width: 11px;
    height: 11px;
    border-radius: 50%;
}

.dot-red { background: #ef4444; }
.dot-yellow { background: #f59e0b; }
.dot-green { background: #10b981; }

.ide-tab {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Streamlit Text Area Overrides */
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem !important;
    background-color: #0b0f19 !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    padding: 14px !important;
    line-height: 1.6 !important;
}

.stTextArea textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
}

/* KPI Summary Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.5rem 0 2rem 0;
}

.kpi-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.25rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(8px);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
}

.kpi-cyan::before { background: var(--accent-cyan); }
.kpi-emerald::before { background: var(--accent-emerald); }
.kpi-amber::before { background: var(--accent-amber); }
.kpi-rose::before { background: var(--accent-rose); }

.kpi-title {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}

.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-top: 0.3rem;
}

/* Finding Cards */
.finding-card {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(10px);
    transition: all 0.25s ease;
}

.finding-card:hover {
    border-color: rgba(255, 255, 255, 0.16);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.5);
}

.finding-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.pkg-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.verdict-tag {
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.verdict-ok {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);
}

.verdict-suspicious {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.15);
}

.verdict-hallucinated {
    background: rgba(244, 63, 94, 0.18);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.4);
    box-shadow: 0 0 20px rgba(244, 63, 94, 0.2);
}

.metric-bar-container {
    margin: 1rem 0;
}

.metric-bar-bg {
    width: 100%;
    height: 7px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    overflow: hidden;
}

.metric-bar-fill {
    height: 100%;
    border-radius: 9999px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.reasons-list {
    margin: 0.75rem 0;
    padding-left: 0;
    list-style: none;
}

.reason-item {
    font-size: 0.92rem;
    color: #cbd5e1;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: flex-start;
    gap: 8px;
    line-height: 1.5;
}

.suggested-fix-box {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%);
    border: 1px dashed rgba(168, 85, 247, 0.4);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-top: 0.85rem;
    font-size: 0.92rem;
    color: #e0e7ff;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Action button */
.stButton > button {
    width: 100%;
    background: var(--primary-gradient) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.55) !important;
}

/* Sidebar Preset Buttons */
.preset-btn {
    display: block;
    width: 100%;
    padding: 10px 14px;
    margin-bottom: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    color: var(--text-primary);
    text-align: left;
    font-size: 0.88rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.preset-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(99, 102, 241, 0.5);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Example Snippets
EXAMPLES = {
    "🛡️ Clean Code": """import json
import requests

response = requests.get("https://api.github.com")
print(response.status_code)
""",
    "⚠️ Typosquat Attack": """import reqeusts
import numpyy

print(reqeusts.__name__)
""",
    "🚨 Hallucinated Package": """import requests
import fastjsonparserx

data = fastjsonparserx.parse('{"status": "ok"}')
""",
    "🔍 Invalid API Call": """import requests

# 'gett' does not exist in requests public API
res = requests.gett("https://api.github.com")
""",
}

if "code_input" not in st.session_state:
    st.session_state["code_input"] = EXAMPLES["⚠️ Typosquat Attack"]


def load_example(snippet: str):
    st.session_state["code_input"] = snippet


# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 1.3rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🛡️ depcheck-ai
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                v0.1.0 • Supply Chain Sentinel
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚡ Preset Snippets")
    for label, snippet in EXAMPLES.items():
        st.button(label, on_click=load_example, args=(snippet,), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔬 Protection Layers")
    st.markdown(
        """
        - **AST Parser**: Alias resolution & stdlib filter
        - **PyPI Registry**: Release count, age, repository
        - **Typosquat Index**: Levenshtein distance check
        - **OSV Database**: Live CVE advisory scan
        - **Chroma RAG**: Public API symbol validation
        - **LangGraph Agent**: Deep autonomous verification
        """
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.78rem; color: #64748b;">
            Built with FastAPI, Streamlit, LangGraph & ChromaDB.<br>
            <a href="http://localhost:8000/docs" target="_blank" style="color: #818cf8; text-decoration: none;">📖 API Docs (Swagger)</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Top Hero Banner
st.markdown(
    """
    <div class="hero-container">
        <div>
            <h1 class="hero-title">🛡️ depcheck-ai</h1>
            <div class="hero-subtitle">
                Real-time security scanner for AI-hallucinated and typosquatted package dependencies.
            </div>
        </div>
        <div class="status-badge">
            <span class="pulse-dot"></span>
            <span>OSV & PyPI Connected</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Two-Column Layout
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.markdown(
        """
        <div class="ide-header" style="border-radius: 12px 12px 0 0;">
            <div class="ide-dots">
                <span class="ide-dot dot-red"></span>
                <span class="ide-dot dot-yellow"></span>
                <span class="ide-dot dot-green"></span>
            </div>
            <div class="ide-tab">
                <span>📄 snippet.py</span>
            </div>
            <div style="font-size: 0.75rem; color: #64748b;">Python AST Scanner</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    code = st.text_area(
        "Python Code Editor",
        key="code_input",
        height=240,
        label_visibility="collapsed",
    )

    # Configuration Controls
    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        mode = st.radio(
            "Scan Mode",
            ["rule", "agent"],
            horizontal=True,
            format_func=lambda x: "⚡ Rule-Based" if x == "rule" else "🤖 LangGraph Agent",
            help="Rule-based runs deterministic checks; Agent mode initiates tool-guided deep reasoning.",
        )
    with ctrl_col2:
        use_llm = st.toggle("✨ LLM Explanation", value=False, help="Generate natural language vulnerability breakdown.")

    scan_button = st.button("🚀 Run Security Scan", use_container_width=True)

# Scan Execution and Findings Display
with col_right:
    if scan_button:
        if not code.strip():
            st.warning("⚠️ Please provide Python code or import statements to scan.")
        else:
            with st.spinner("🔍 Inspecting imports against PyPI registry, OSV database & vector index..."):
                try:
                    params = {
                        "mode": mode,
                        "use_llm": "true" if use_llm else "false",
                    }
                    response = requests.post(
                        f"{API_URL}/scan",
                        params=params,
                        json={"code": code},
                        timeout=30,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        findings = data.get("findings", [])
                        scanned_count = data.get("scanned_imports", len(findings))

                        # Calculate KPIs
                        hallucinated_cnt = sum(1 for f in findings if f.get("verdict") == "hallucinated")
                        suspicious_cnt = sum(1 for f in findings if f.get("verdict") == "suspicious")
                        ok_cnt = sum(1 for f in findings if f.get("verdict") == "ok")

                        # KPI Row
                        st.markdown(
                            f"""
                            <div class="kpi-grid">
                                <div class="kpi-card kpi-cyan">
                                    <div class="kpi-title">Scanned</div>
                                    <div class="kpi-value">{scanned_count}</div>
                                </div>
                                <div class="kpi-card kpi-emerald">
                                    <div class="kpi-title">Clean</div>
                                    <div class="kpi-value">{ok_cnt}</div>
                                </div>
                                <div class="kpi-card kpi-amber">
                                    <div class="kpi-title">Suspicious</div>
                                    <div class="kpi-value">{suspicious_cnt}</div>
                                </div>
                                <div class="kpi-card kpi-rose">
                                    <div class="kpi-title">Hallucinated</div>
                                    <div class="kpi-value">{hallucinated_cnt}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if not findings:
                            st.markdown(
                                """
                                <div style="padding: 2rem; text-align: center; background: rgba(16, 185, 129, 0.08); border: 1px dashed rgba(16, 185, 129, 0.3); border-radius: 12px;">
                                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                                    <div style="font-weight: 700; color: #34d399;">No External Dependencies Found</div>
                                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">Only built-in standard library imports or local modules were detected.</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown("### 📋 Security Findings")

                            for f in findings:
                                pkg = f.get("package", "unknown")
                                verdict = f.get("verdict", "ok")
                                risk = float(f.get("risk_score", 0.0))
                                confidence = float(f.get("confidence", 0.0))
                                reasons = f.get("reasons", [])
                                fix = f.get("suggested_fix")

                                # Styling based on verdict
                                if verdict == "ok":
                                    badge_class = "verdict-ok"
                                    badge_icon = "✓"
                                    bar_color = "linear-gradient(90deg, #10b981, #34d399)"
                                elif verdict == "suspicious":
                                    badge_class = "verdict-suspicious"
                                    badge_icon = "⚠️"
                                    bar_color = "linear-gradient(90deg, #f59e0b, #fbbf24)"
                                else:
                                    badge_class = "verdict-hallucinated"
                                    badge_icon = "🚨"
                                    bar_color = "linear-gradient(90deg, #f43f5e, #fb7185)"

                                reasons_html = "".join([
                                    f'<li class="reason-item"><span>•</span><span>{r}</span></li>'
                                    for r in reasons
                                ])

                                fix_html = ""
                                if fix:
                                    fix_html = f"""
                                    <div class="suggested-fix-box">
                                        <span>💡</span>
                                        <span><strong>Suggested Fix:</strong> {fix}</span>
                                    </div>
                                    """

                                pypi_link = f"https://pypi.org/project/{pkg}/"
                                finding_card_html = f"""
                                <div class="finding-card">
                                    <div class="finding-header">
                                        <div class="pkg-name">
                                            <span>📦</span>
                                            <a href="{pypi_link}" target="_blank" style="color: #ffffff; text-decoration: none;">{pkg}</a>
                                        </div>
                                        <span class="verdict-tag {badge_class}">
                                            <span>{badge_icon}</span>
                                            <span>{verdict}</span>
                                        </span>
                                    </div>

                                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #94a3b8; margin-bottom: 4px;">
                                        <span>Risk Score: <strong style="color: #f8fafc;">{risk:.2f}</strong></span>
                                        <span>Confidence: <strong style="color: #f8fafc;">{int(confidence * 100)}%</strong></span>
                                    </div>
                                    <div class="metric-bar-bg">
                                        <div class="metric-bar-fill" style="width: {int(risk * 100)}%; background: {bar_color};"></div>
                                    </div>

                                    <ul class="reasons-list">
                                        {reasons_html}
                                    </ul>

                                    {fix_html}
                                </div>
                                """
                                st.markdown(finding_card_html, unsafe_allow_html=True)

                        with st.expander("🛠️ Raw API Response Payload"):
                            st.json(data)

                    else:
                        st.error(f"❌ Scan failed ({response.status_code}): {response.text}")

                except requests.RequestException as e:
                    st.error(f"❌ Failed to reach backend API at {API_URL}: {e}")

    else:
        # Placeholder / Empty State before scanning
        st.markdown(
            """
            <div style="padding: 3rem 2rem; text-align: center; background: rgba(17, 24, 39, 0.4); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 14px; margin-top: 1rem;">
                <div style="font-size: 2.8rem; margin-bottom: 0.75rem;">🛡️</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc;">Ready for Dependency Inspection</div>
                <div style="font-size: 0.9rem; color: #94a3b8; max-width: 380px; margin: 0.5rem auto 1.5rem auto; line-height: 1.5;">
                    Select an example snippet or paste your Python code on the left, then click <strong>Run Security Scan</strong>.
                </div>
                <div style="display: inline-flex; gap: 12px; font-size: 0.8rem; color: #64748b;">
                    <span>⚡ PyPI Live Checks</span> •
                    <span>🔒 OSV CVE Detection</span> •
                    <span>🤖 Autonomous Agent</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
