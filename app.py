"""
app.py
------
Streamlit dashboard for the Pest Detection + Weather Early-Warning system.

Run with:
    streamlit run app.py
"""

import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from risk_engine import compute_risk, PEST_PROFILES  # noqa: E402
from alert_system import build_alert_message, log_alert  # noqa: E402

st.set_page_config(page_title="Pest Early Warning System", page_icon="🌾", layout="wide")

st.title("🌾 Pest Detection with Regional Weather Early Warning")
st.caption("Fuses image-based pest detection with regional weather forecasts "
           "to flag outbreak risk before it spreads.")

with st.sidebar:
    st.header("Region & Pest")
    lat = st.number_input("Latitude", value=15.4800, format="%.4f")
    lon = st.number_input("Longitude", value=78.4900, format="%.4f")
    region_name = st.text_input("Region name", value="Nandyal, Andhra Pradesh")
    pest = st.selectbox("Pest species", list(PEST_PROFILES.keys()))

    st.header("Optional: Image Detection")
    uploaded = st.file_uploader("Upload a field/leaf photo", type=["jpg", "jpeg", "png"])
    manual_confidence = st.slider(
        "Or manually set detection confidence (0 = none)", 0.0, 1.0, 0.0, 0.05
    )

    run_button = st.button("Compute Risk & Alert", type="primary")

if run_button:
    detection_confidence = None

    if uploaded is not None:
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
            from predict import predict_image  # local import, needs trained model

            tmp_path = os.path.join("logs", "_tmp_upload.jpg")
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            result = predict_image(tmp_path)
            detection_confidence = result["confidence"]
            st.success(f"Detected: {result['pest_class']} ({detection_confidence:.1%} confidence)")
        except FileNotFoundError:
            st.warning("No trained model found yet — run model_train.py first. "
                       "Falling back to manual confidence / weather-only mode.")
    elif manual_confidence > 0:
        detection_confidence = manual_confidence

    with st.spinner("Fetching regional weather and computing risk..."):
        risk_result = compute_risk(pest, lat, lon, detection_confidence)
        log_alert(risk_result, region_name)

    color = {"HIGH": "🔴", "MODERATE": "🟠", "LOW": "🟢"}[risk_result["risk_level"]]
    st.subheader(f"{color} Risk: {risk_result['risk_score']}/100 — {risk_result['risk_level']}")
    st.write(build_alert_message(risk_result, region_name))

    st.markdown("### 7-Day Weather Favorability Forecast")
    df = pd.DataFrame(risk_result["daily_weather_favorability"])
    st.bar_chart(df.set_index("date")["favorability"])
    st.dataframe(df, use_container_width=True)
else:
    st.info("Set your region and pest in the sidebar, then click "
            "**Compute Risk & Alert** to generate an early-warning report.")
