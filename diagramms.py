import streamlit as st
import rasterio
from rasterio.plot import show
import numpy as np
from geopy.geocoders import Nominatim
from pyproj import Transformer
from streamlit_folium import st_folium
import folium
from geopy.exc import GeocoderTimedOut
import matplotlib.pyplot as plt

# Streamlit page configuration
st.set_page_config(page_title="LCA Privat Windturbinen")


# Function to get the value at a specific latitude and longitude
def get_value_at_location(geotiff_path, lat, lon, h2):
    with rasterio.open(geotiff_path) as src:
        transformer = Transformer.from_crs("EPSG:4326", src.crs)
        x, y = transformer.transform(lat, lon)
        row, col = src.index(x, y)
        if (row < 0 or row >= src.height) or (col < 0 or col >= src.width):
            raise ValueError("Latitude and longitude are out of raster bounds.")
        v1 = src.read(1)[row, col]
        h1 = 100
        a = 1 / 7
        v2 = v1 * ((h2 / h1) ** a)
        return v2


# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    location = geolocator.geocode(place_name, timeout=30)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")


# Function to reverse geocode coordinates to a place name
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address
    except GeocoderTimedOut:
        return "Timeout: Unable to get the place name"


def calculate_wind_power(A, v):
    rho = 1.2255
    efficiency = 0.4
    PWind = (rho / 2) * A * v ** 3
    PEffective = PWind * efficiency
    return PEffective


def calculate_annual_energy_output(power):
    hours_per_year = 24 * 365
    annual_energy_output = power * hours_per_year / 1000
    return annual_energy_output


def calculate_co2_savings(annual_energy_output, co2_per_kwh):
    co2_savings = annual_energy_output * co2_per_kwh
    return co2_savings


def calculate_total_co2_savings(annual_co2_savings, years):
    total_co2_savings = annual_co2_savings * years
    return total_co2_savings


# Emission factors for different fossil fuels in kg CO2 per kWh
emission_factors = {
    'coal': 0.91,
    'natural_gas': 0.4,
    'oil': 0.6
}

# Header section
st.title("Effiziente Positionierung von Windturbinen")
st.write(
    "Diese Anwendung hilft bei der Analyse der Effizienz von Windturbinen basierend auf Standortdaten und anderen Parametern.")

# Input Data
st.write("### Eingabedaten")
A = st.number_input("Windturbine Fläche (m²)", min_value=0.0, value=200.0)
place_name = st.text_input("Ort (z.B. 'Kölner Dom, Köln')")
h2 = st.number_input("Höhe (in Metern) für die Anpassung", min_value=0.0, value=100.0)
years = st.number_input("Anzahl der Jahre für die Nutzung der Turbine", min_value=1, value=20)

# Folium map
st.write("### Wählen Sie einen Standort auf der Karte aus oder geben Sie einen Ort ein")
map_center = [51.1657, 10.4515]
m = folium.Map(location=map_center, zoom_start=6)
marker = folium.Marker(map_center, popup="Default Location")
m.add_child(marker)

clicked_coords = st_folium(m, width=700, height=450)

if clicked_coords:
    if 'lat' in clicked_coords['last_clicked']:
        lat = clicked_coords['last_clicked']['lat']
        lon = clicked_coords['last_clicked']['lng']
        st.write(f"Sie haben die Position ({lat:.2f}, {lon:.2f}) ausgewählt.")
        try:
            place_name = reverse_geocode(lat, lon)
            st.write(f"Dieser Ort ist: **{place_name}**")
        except ValueError as e:
            st.error(str(e))

if st.button("Berechnen"):
    try:
        if place_name:
            lat, lon = get_coordinates_from_place(place_name)

        v = get_value_at_location('C:\\BORO\\suli\\aachen\\6.Semester\\BIM_LCA\\programming\\TIFF\\en_100m_klas.tif',
                                  lat, lon, h2)
        st.write(
            f'Die Windgeschwindigkeit an der Position ({lat:.2f}, {lon:.2f}) bei {h2} Metern Höhe beträgt **{v:.2f} m/s**')

        wind_power = calculate_wind_power(A, v)
        st.write(f"Die effektive Leistung der Windturbine beträgt: **{wind_power:.2f} W**")

        annual_energy_output = calculate_annual_energy_output(wind_power)
        st.write(f"Die jährliche Energieproduktion beträgt: **{annual_energy_output:.2f} kWh**")

        annual_co2_savings_coal = calculate_co2_savings(annual_energy_output, emission_factors['coal'])
        annual_co2_savings_gas = calculate_co2_savings(annual_energy_output, emission_factors['natural_gas'])
        annual_co2_savings_oil = calculate_co2_savings(annual_energy_output, emission_factors['oil'])

        total_co2_savings_coal = calculate_total_co2_savings(annual_co2_savings_coal, years)
        total_co2_savings_gas = calculate_total_co2_savings(annual_co2_savings_gas, years)
        total_co2_savings_oil = calculate_total_co2_savings(annual_co2_savings_oil, years)

        st.success(
            f"Die jährliche CO2-Einsparung im Vergleich zum Erdgas beträgt: **{annual_co2_savings_gas:.2f} kg CO2**")




        # Plotting the results with custom colors
        fossil_fuel_types = ['Coal', 'Natural Gas', 'Oil', 'Windturbine']
        total_savings = [annual_co2_savings_coal, annual_co2_savings_gas, annual_co2_savings_oil, 0]

        # Define colors using hex color codes
        colors = ['#2d2d96', '#5858cc', '#7e7ed8', '#a4a4e3']

        fig, ax = plt.subplots()
        ax.bar(fossil_fuel_types, total_savings, color=colors)
        ax.set_xlabel('Fossil Fuel Type')
        ax.set_ylabel('Total CO2  (kg)')
        ax.set_title(f'Total CO2 for energy over a year')

        st.pyplot(fig)

    except ValueError as e:
        st.error(str(e))
