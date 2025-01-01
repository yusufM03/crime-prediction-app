import streamlit as st
import numpy as np
import pandas as pd
import joblib
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns

# Load the trained model
model = joblib.load("Checkpoints/XGB_model.joblib")
print(model.get_booster().feature_names)

# Title of the App
st.title("New York City Crime Prediction App")

# Create columns for layout
col1, col2 = st.columns([1, 2])

# Sidebar for user inputs
with st.sidebar:
    st.header("User Input Parameters")
    age = st.selectbox("Age Group", ['<18', '18-24', '25-44', '45-64', '65+'])
    date_input = st.date_input("Date", min_value=pd.to_datetime("2025-01-01"))
    race = st.selectbox("Race", ['White', 'Black', 'Asian', 'Hispanic', 'Other'])
    latitude = st.number_input("Latitude", value=40.7128, format="%.6f")
    longitude = st.number_input("Longitude", value=-74.0060, format="%.6f")
    sex = st.selectbox("Sex", ['Male', 'Female'])

# Define mappings
age_mapping = {'<18': 0, '18-24': 1, '25-44': 2, '45-64': 3, '65+': 4}
day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
               'Friday': 4, 'Saturday': 5, 'Sunday': 6}

def preprocess_input(latitude, longitude, age, race, sex, date):
    year = date.year
    month = date.month
    day_of_week = date.strftime('%A')

    data = {
        'VIC_AGE_GROUP': [age],
        'VIC_RACE': [race],
        'VIC_SEX': [sex],
        'YEAR': [year],
        'MONTH': [month],
        'DAY_OF_WEEK': [day_of_week],
        'Latitude': [latitude],
        'Longitude': [longitude],
    }
    df = pd.DataFrame(data)

    df['VIC_AGE_GROUP'] = df['VIC_AGE_GROUP'].map(age_mapping)
    df = pd.get_dummies(df, columns=['VIC_RACE', 'VIC_SEX'], drop_first=True)

    expected_columns = ['Latitude', 'Longitude', 'VIC_AGE_GROUP', 'YEAR', 'DAY_OF_WEEK', 'MONTH', 
                        'VIC_RACE_ASIAN / PACIFIC ISLANDER', 'VIC_RACE_BLACK', 'VIC_RACE_BLACK HISPANIC',
                        'VIC_RACE_OTHER', 'VIC_RACE_UNKNOWN', 'VIC_RACE_WHITE', 'VIC_RACE_WHITE HISPANIC',
                        'VIC_SEX_FEMALE', 'VIC_SEX_MALE', 'VIC_SEX_Unknown', 'month_sin', 'month_cos']
    
    df = df.reindex(columns=expected_columns, fill_value=0)
    df['YEAR'] = (df['YEAR'] - df['YEAR'].min()) / (df['YEAR'].max() - df['YEAR'].min())
    df['month_sin'] = np.sin(2 * np.pi * df['MONTH'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['MONTH'] / 12)
    df['DAY_OF_WEEK'] = df['DAY_OF_WEEK'].map(day_mapping)

    return df

# Initialize map
m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

# Predict based on user input
if st.sidebar.button("Predict"):
    inputs = preprocess_input(latitude, longitude, age, race, sex, date_input)
    prediction = model.predict_proba(inputs)[0]
    
    # Clear and update map
    m = folium.Map(location=[latitude, longitude], zoom_start=13)
    
    popup_html = f"""
    <div style='width: 200px'>
        <b>Prediction Results:</b><br>
        Felony: {prediction[0]:.2%}<br>
        Misdemeanor: {prediction[1]:.2%}<br>
        Violation: {prediction[2]:.2%}
    </div>
    """
    
    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip="Click for prediction details",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)

    # Make columns equal size
    col1, col2 = st.columns(2)

# Update visualization in prediction section:
    with col1:
        st.subheader("Prediction Results")
        
        # Larger figure with dark style
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(15, 15), dpi=150, facecolor='#1E1E1E')
        ax.set_facecolor('#1E1E1E')
        
        crime_types = ["Felony", "Misdemeanor", "Violation"]
        colors = ['#FF4B4B', '#00E3CC', '#3498DB']
        
        # Create larger bars
        bars = ax.bar(crime_types, prediction * 100, color=colors, width=0.5)
        
        # Larger fonts and labels
        ax.set_ylabel('Probability (%)', fontsize=20, fontweight='bold', color='white')
        ax.set_title('Crime Type Probability Distribution', pad=20, fontsize=24, fontweight='bold', color='white')
        
        # Larger bar value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}%',
                   ha='center', va='bottom',
                   fontsize=20,
                   fontweight='bold',
                   color='white')
        
        ax.grid(axis='y', linestyle='--', alpha=0.2, color='white')
        ax.set_ylim(0, max(prediction * 100) * 1.15)
        
        # Remove spines and style ticks
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.tick_params(colors='white', labelsize=18)
        
        plt.tight_layout()
        
        # Force large size
        st_container = st.container()
        with st_container:
            st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Location Map")
        folium_static(m, width=700, height=700)