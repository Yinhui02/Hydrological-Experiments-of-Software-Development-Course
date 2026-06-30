"""
Primary file: Dashboard Creation
Streamlit dashboard for rainfall monitoring with alerts, prediction, and map.
"""
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import time as time_module
from weather_api import get_city_weather, get_all_cities_weather, CITIES
from alert import handle_alert, classify_alert, ALERT_LOG_FILE
st.set_page_config(page_title="Rainfall Monitoring System", layout="wide")
CITY_COORDS = {
    "Beijing": [39.9042, 116.4074],
    "Xi'an": [34.3416, 108.9398],
    "Zhengzhou": [34.7466, 113.6254],
    "Shanghai": [31.2304, 121.4737],
    "Kunming": [25.0389, 102.7183],
}
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "city", "timestamp", "rainfall", "temperature", "humidity", "alert_level"
    ])
if "last_update" not in st.session_state:
    st.session_state.last_update = time_module.time()
st.sidebar.title("Controls")
selected_city = st.sidebar.selectbox("Select City", CITIES)
api_key = st.sidebar.text_input("API Key", type="password",
                                value="5ab9fb17cb05b2f2ae76bbea5ab2fcb9")
refresh_interval = st.sidebar.slider("Auto-refresh (minutes)", 1, 30, 5)
manual_refresh = st.sidebar.button("Refresh Now")
elapsed = time_module.time() - st.session_state.last_update
if manual_refresh or elapsed >= refresh_interval * 60:
    st.session_state.last_update = time_module.time()
    st.rerun()
st.markdown(
    f'<meta http-equiv="refresh" content="{refresh_interval * 60}">',
    unsafe_allow_html=True,
)
st.title(f"Rainfall Monitor - {selected_city}")
weather_data = get_city_weather(selected_city)
if weather_data:
    rainfall = weather_data["rainfall"]
    alert_result = handle_alert(rainfall, selected_city)
    level = alert_result["level"]
    message = alert_result["message"]
    color_map = {"green": "#2ECC71", "yellow": "#F1C40F", "red": "#E74C3C"}
    alert_color = color_map.get(level, "#95A5A6")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rainfall Intensity", f"{rainfall:.1f} mm/h",
                  delta=f"{weather_data['temperature']:.1f}°C")
    with col2:
        st.markdown(
            f"<div style='background:{alert_color};padding:20px;"
            f"border-radius:10px;text-align:center;color:white;'>"
            f"<h3>Alert Level: {level.upper()}</h3>"
            f"<p style='font-size:18px;'>{message}</p></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.metric("Temperature", f"{weather_data['temperature']:.1f} °C")
        st.metric("Humidity", f"{weather_data['humidity']:.0f} %")
        st.caption(f"Updated: {weather_data['timestamp']}")
    st.info(f"Weather: {weather_data['description'].capitalize()}")
    new_row = pd.DataFrame([{
        "city": selected_city,
        "timestamp": weather_data["timestamp"],
        "rainfall": rainfall,
        "temperature": weather_data["temperature"],
        "humidity": weather_data["humidity"],
        "alert_level": level,
    }])
    st.session_state.history = pd.concat(
        [st.session_state.history, new_row], ignore_index=True
    ).tail(50)
    city_history = st.session_state.history[
        st.session_state.history["city"] == selected_city
    ]
    if len(city_history) > 1:
        st.subheader("Historical Rainfall Data")
        chart_data = city_history[["timestamp", "rainfall"]].set_index("timestamp")
        st.line_chart(chart_data, use_container_width=True)
        if len(city_history) >= 3:
            st.subheader("Rainfall Prediction (Linear Trend)")
            y = city_history["rainfall"].values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            next_val = max(0, slope * len(y) + intercept)
            pred_level = classify_alert(next_val)
            pred_color = color_map.get(pred_level, "#95A5A6")
            delta_str = f"{next_val - y[-1]:+.1f} mm/h"
            st.metric("Predicted Next Rainfall", f"{next_val:.1f} mm/h",
                      delta=delta_str)
            trend = "Increasing" if slope > 0 else "Decreasing"
            st.caption(
                f"Trend: {trend} (slope={slope:.3f}) | "
                f"Predicted alert: {pred_level.upper()}",
                help="Linear regression on last 50 data points"
            )
            st.markdown(
                f"<div style='background:{pred_color};padding:8px;"
                f"border-radius:5px;text-align:center;color:white;'>"
                f"Predicted Level: {pred_level.upper()}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Collecting more data... Need at least 2 points for a chart.")
    if level == "red" and alert_result["logged"]:
        st.error(f"⚠️ RED ALERT LOGGED — Check {ALERT_LOG_FILE}")
    st.subheader("City Map")
    m = folium.Map(location=[35.0, 110.0], zoom_start=5)
    all_data = get_all_cities_weather()
    for cd in all_data:
        city_name = cd["city"]
        if city_name in CITY_COORDS:
            rf = cd["rainfall"]
            lvl = classify_alert(rf)
            clr = {"green": "green", "yellow": "orange", "red": "red"}[lvl]
            folium.Marker(
                location=CITY_COORDS[city_name],
                popup=(
                    f"<b>{city_name}</b><br>"
                    f"Rainfall: {rf:.1f} mm/h<br>"
                    f"Temp: {cd['temperature']:.1f}°C<br>"
                    f"Alert: {lvl.upper()}"
                ),
                tooltip=city_name,
                icon=folium.Icon(color=clr),
            ).add_to(m)
    if selected_city in CITY_COORDS:
        m.location = CITY_COORDS[selected_city]
        m.zoom_start = 8
    st_folium(m, width=850, height=500, returned_objects=[])
else:
    st.error("Failed to fetch weather data. Check your API key and network.")
st.sidebar.divider()
if st.sidebar.checkbox("Show Alert Log"):
    try:
        with open(ALERT_LOG_FILE, "r", encoding="utf-8") as f:
            log_content = f.read()
        st.sidebar.text_area("Alert Log", log_content, height=300)
    except FileNotFoundError:
        st.sidebar.info("No alerts logged yet.")
next_update = st.session_state.last_update + refresh_interval * 60
remaining = max(0, int(next_update - time_module.time()))
st.caption(
    f"Auto-refreshing every {refresh_interval} min(s). "
    f"Next update in ~{remaining} seconds."
)
st.sidebar.divider()
st.sidebar.caption("Rainfall Monitoring System v2.0")