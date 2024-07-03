import streamlit as st
import rasterio
from rasterio.plot import show
import numpy as np
from geopy.geocoders import Nominatim
from pyproj import Transformer

# Function to get the value at a specific latitude and longitude
def get_value_at_location(geotiff_path, lat, lon, h2):
    with rasterio.open(geotiff_path) as src:
        # Transform geographic coordinates to the raster's coordinate system
        transformer = Transformer.from_crs("EPSG:4326", src.crs)
        x, y = transformer.transform(lat, lon)

        row, col = src.index(x, y)

        # Check if the calculated row and col are within bounds
        if (row < 0 or row >= src.height) or (col < 0 or col >= src.width):
            raise ValueError("Latitude and longitude are out of raster bounds.")

        # Read the value at the specified location
        v1 = src.read(1)[row, col]  # Reading the first band

        # Calculate v2 using the provided formula
        h1 = 100
        a = 1 / 7
        v2 = v1 * ((h2 / h1) ** a)

        return v2

# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")  # Replace with a unique user agent string
    location = geolocator.geocode(place_name, timeout=30)  # Adjust the timeout value as needed

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")

def calculate_wind_power(A, v):
    # Define constants
    rho = 1.2255  # Air density in kg/m³
    efficiency = 0.4  # Assumed efficiency of the turbine (40%)

    # Calculate theoretical power
    PWind = (rho / 2) * A * v ** 3

    # Calculate actual power considering efficiency
    PEffective = PWind * efficiency

    return PEffective

def calculate_annual_energy_output(power):
    # Calculate annual energy production in kWh
    hours_per_year = 24 * 365
    annual_energy_output = power * hours_per_year / 1000  # Convert from watts to kW
    return annual_energy_output

def calculate_co2_savings(annual_energy_output, co2_per_kwh=0.5):
    # Calculate CO2 savings in kg
    co2_savings = annual_energy_output * co2_per_kwh
    return co2_savings

def calculate_total_co2_savings(annual_co2_savings, years):
    # Calculate total CO2 savings in kg over the specified number of years
    total_co2_savings = annual_co2_savings * years
    return total_co2_savings

# Streamlit App
st.set_page_config(page_title="LCA Privat Windturbinen")

# Header section
st.title("Effiziente Positionierung von Windturbinen")
st.write("Diese Anwendung hilft bei der Analyse der Effizienz von Windturbinen basierend auf Standortdaten und anderen Parametern.")

# Input Data
st.write("### Eingabedaten")
A = st.number_input("Windturbine Fläche (m²)", min_value=0.0, value=200.0)
place_name = st.text_input("Ort (z.B. 'Kölner Dom, Köln')")
h2 = st.number_input("Höhe (in Metern) für die Anpassung", min_value=0.0, value=100.0)
years = st.number_input("Anzahl der Jahre für die Nutzung der Turbine", min_value=1, value=100)

# Calculate values based on inputs
if st.button("Berechnen"):
    try:
        lat, lon = get_coordinates_from_place(place_name)
        v = get_value_at_location('C:\\BORO\\suli\\aachen\\6.Semester\\BIM_LCA\\programming\\TIFF\\en_100m_klas.tif', lat, lon, h2)
        st.write(f'Die Windgeschwindigkeit an der Position ({lat:.2f}, {lon:.2f}) bei {h2} Metern Höhe beträgt **{v:.2f} m/s**')

        wind_power = calculate_wind_power(A, v)
        st.write(f"Die effektive Leistung der Windturbine beträgt: **{wind_power:.2f} W**")

        annual_energy_output = calculate_annual_energy_output(wind_power)
        st.write(f"Die jährliche Energieproduktion beträgt: **{annual_energy_output:.2f} kWh**")

        annual_co2_savings = calculate_co2_savings(annual_energy_output)
        st.success(f"Die jährliche CO2-Einsparung beträgt: **{annual_co2_savings:.2f} kg CO2**")

        total_co2_savings = calculate_total_co2_savings(annual_co2_savings, years)
        st.success(f"Die Gesamteinsparung über {years} Jahre beträgt: **{total_co2_savings:.2f} kg CO2** ")


    except ValueError as e:
        st.error(str(e))
