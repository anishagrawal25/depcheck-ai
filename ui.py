import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="depcheck-ai", layout="wide")
st.title("depcheck-ai")

EXAMPLES = {
    "Clean": """import json
import requests

response = requests.get("https://api.github.com")
print(response.status_code)
""",
    "Fake Package": """import requests
import fastjsonparserx

data = fastjsonparserx.parse('{"status": "ok"}')
""",
    "Typosquat": """import reqeusts
import numpyy

print(reqeusts.__name__)
""",
}

if "code_input" not in st.session_state:
    st.session_state["code_input"] = EXAMPLES["Clean"]


def load_example(snippet: str):
    st.session_state["code_input"] = snippet


st.sidebar.header("Example Snippets")
for label, snippet in EXAMPLES.items():
    st.sidebar.button(f"Load {label}", on_click=load_example, args=(snippet,))


def render_results_table(findings):
    if not findings:
        st.info("No external imports detected.")
        return

    st.subheader("Scan Results")

    rows_html = []
    for f in findings:
        verdict = f.get("verdict", "ok")
        pkg = f.get("package", "")
        risk = f.get("risk_score", 0.0)
        reasons_list = f.get("reasons", [])
        reasons_str = "<br>• ".join([""] + reasons_list) if reasons_list else "None"

        if verdict == "ok":
            color = "#28a745"
            bg = "#e8f5e9"
        elif verdict == "suspicious":
            color = "#e65100"
            bg = "#fff3e0"
        else:  # hallucinated
            color = "#c62828"
            bg = "#ffebee"

        badge = (
            f'<span style="background-color: {bg}; color: {color}; '
            f'padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.9em; '
            f'border: 1px solid {color}40;">{verdict.upper()}</span>'
        )

        row = f"""
        <tr style="border-bottom: 1px solid #e0e0e0;">
            <td style="padding: 10px; font-weight: 600; font-family: monospace;">{pkg}</td>
            <td style="padding: 10px;">{badge}</td>
            <td style="padding: 10px; font-weight: 500;">{risk:.2f}</td>
            <td style="padding: 10px; font-size: 0.92em; line-height: 1.4;">{reasons_str}</td>
        </tr>
        """
        rows_html.append(row)

    table_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; text-align: left;">
        <thead>
            <tr style="border-bottom: 2px solid #ccc; background-color: #f8f9fa;">
                <th style="padding: 10px; font-size: 0.95em;">Package</th>
                <th style="padding: 10px; font-size: 0.95em;">Verdict</th>
                <th style="padding: 10px; font-size: 0.95em;">Risk Score</th>
                <th style="padding: 10px; font-size: 0.95em;">Reasons</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


code = st.text_area("Enter Python code to scan", key="code_input", height=200)

col1, col2 = st.columns([1, 1])
with col1:
    mode = st.radio(
        "Scan Mode",
        ["rule", "agent"],
        horizontal=True,
        format_func=lambda x: "⚡ Rule-based" if x == "rule" else "🤖 Agent Investigation",
    )
with col2:
    use_llm = st.checkbox("Enable LLM-enhanced analysis", value=False)

if st.button("Scan"):
    if not code.strip():
        st.warning("Please enter some Python code to scan.")
    else:
        try:
            params = {
                "mode": mode,
                "use_llm": "true" if use_llm else "false",
            }
            response = requests.post(f"{API_URL}/scan", params=params, json={"code": code}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                render_results_table(data.get("findings", []))
                with st.expander("Raw JSON Output"):
                    st.json(data)
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            st.error(f"Failed to connect to API: {e}")
