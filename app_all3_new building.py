
import streamlit as st
import rasterio
import numpy as np
from geopy.geocoders import Nominatim
from pyproj import Transformer
from streamlit_folium import st_folium
import folium
from geopy.exc import GeocoderTimedOut
import matplotlib.pyplot as plt
import requests
from datetime import date, timedelta
from owslib.wms import WebMapService
from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw

# Function to get the wind speed at a specific height
def get_wind_speed_at_height(geotiff_path, lat, lon, h2):
    with rasterio.open(geotiff_path) as src:
        # Transform geographic coordinates to the raster's coordinate system
        transformer = Transformer.from_crs("EPSG:4326", src.crs)
        x, y = transformer.transform(lat, lon)

        row, col = src.index(x, y)

        # Check if the calculated row and col are within bounds
        if (row < 0 or row >= src.height) or (col < 0 or col >= src.width):
            raise ValueError("Latitude and longitude are out of raster bounds.")

        # Read the wind speed at the specified location and height
        v1 = src.read(1)[row, col]  # Reading the first band (wind speed at ground level)

        # Calculate wind speed at height h2 using power law profile
        h1 = 100  # Standard height (e.g., 100 meters)
        a = 1 / 7  # Power law exponent
        v2 = v1 * ((h2 / h1) ** a)

        return v2

# Function to calculate wind speed reduction due to nearby buildings
def calculate_wind_speed_reduction(Cd, h, r):
    # Function logic from second code
    delta_V = Cd * h / r
    return delta_V

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

# Function to fetch historical weather data
def fetch_historical_weather(api_key, location, start_date, end_date):
    # Function logic from second code
    base_url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history'
    params = {
        'aggregateHours': '24',
        'startDateTime': start_date,
        'endDateTime': end_date,
        'unitGroup': 'metric',
        'contentType': 'json',
        'dayStartTime': '0:0:00',
        'dayEndTime': '0:0:00',
        'location': location,
        'key': api_key,
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

# Function to calculate the average wind direction
def calculate_average_wind_direction(data):
    # Function logic from second code
    if 'locations' in data and data['locations']:
        location_data = data['locations'][list(data['locations'].keys())[0]]
        if 'values' in location_data and location_data['values']:
            values = location_data['values']

            wind_directions = [entry['wdir'] for entry in values]

            wind_directions = pd.Series(pd.to_numeric(wind_directions, errors='coerce'))

            angles = wind_directions.dropna() * (2 * np.pi / 360)
            sin_sum = sum(np.sin(angles))
            cos_sum = sum(np.cos(angles))
            average_direction = np.arctan2(sin_sum, cos_sum) * (360 / (2 * np.pi))

            if average_direction < 0:
                average_direction += 360

            return average_direction
        else:
            print("No 'values' found in the API response. Check the data structure.")
            return None
    else:
        print("No 'locations' found in the API response. Check the data structure.")
        return None

# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    # Function logic from first code
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    location = geolocator.geocode(place_name, timeout=30)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")


# Function to reverse geocode coordinates to a place name
def reverse_geocode(lat, lon):
    # Function logic from first code
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address
    except GeocoderTimedOut:
        return "Timeout: Unable to get the place name"


def calculate_wind_power(A, v1):
    # Function logic from first code
    rho = 1.2255
    efficiency = 0.4
    PWind = (rho / 2) * A * v ** 3
    PEffective = PWind * efficiency
    return PEffective

def calculate_annual_energy_output(power):
    # Function logic from first code
    hours_per_year = 24 * 365
    annual_energy_output = power * hours_per_year / 1000
    return annual_energy_output

def calculate_co2_savings(annual_energy_output, co2_per_kwh):
    # Function logic from first code
    co2_savings = annual_energy_output * co2_per_kwh
    return co2_savings

def calculate_total_co2_savings(annual_co2_savings, years):
    # Function logic from first code
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
# Function to generate building image
# Function to generate a rectangle image
def generate_rectangle_image(length_meters, width_meters, rotation_degrees):
    # Convert meters to inches
    length_inches = length_meters * 39.37  # 1 meter = 39.37 inches
    width_inches = width_meters * 39.37    # 1 meter = 39.37 inches

    # Create a blank transparent image
    rectangle_fig = Image.new('RGBA', (800, 600), (0, 0, 0, 0))  # Transparent RGBA image
    draw = ImageDraw.Draw(img)

    # Calculate coordinates for the rectangle
    cx, cy = 400, 300  # Center of the image
    corners = [
        (-length_inches / 2, -width_inches / 2),
        (length_inches / 2, -width_inches / 2),
        (length_inches / 2, width_inches / 2),
        (-length_inches / 2, width_inches / 2),
    ]

    # Rotate the rectangle around its center
    theta = np.radians(rotation_degrees)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    rotated_corners = [
        (cx + (x * cos_theta - y * sin_theta), cy + (x * sin_theta + y * cos_theta))
        for (x, y) in corners
    ]

    # Draw the rotated rectangle on the transparent image
    draw.polygon(rotated_corners, fill=(255, 0, 0, 128))  # Semi-transparent red rectangle

    return rectangle_fig



st.title("Rechteck-Generator")

length_meters = st.number_input("Length of the rectangle (in meters)", min_value=1.0, value=10.0)
width_meters = st.number_input("Width of the rectangle (in meters)", min_value=1.0, value=5.0)
rotation_degrees = st.number_input("Rotation of the rectangle (in degrees)", min_value=0, max_value=360, value=0)

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
                                  lat, lon,h2)
        st.write(
            f'Die Windgeschwindigkeit an der Position ({lat:.2f}, {lon:.2f}) bei {h2} Metern Höhe beträgt **{v:.2f} m/s**')

        st.write(
            f'Die  endgültige Windgeschwindigkeit an der Position ({lat:.2f}, {lon:.2f}) beträgt **{v:.2f} m/s**')

        wind_power = calculate_wind_power(A,v)
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

        # Fetch historical weather data
        api_key = 'RZVMEQKLB4H52H7TGUUZ6GGDK'
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        weather_data = fetch_historical_weather(api_key, place_name, start_date, end_date)

        if weather_data:
            average_direction = calculate_average_wind_direction(weather_data)
            if average_direction is not None:
                st.write(f"Durchschnittliche Windrichtung: {average_direction:.2f} Grad")

        # Calculate wind speed reduction due to nearby buildings
        Cd = 0.8  # Example value for drag coefficient
        h_building = 20  # Example value for building height
        r_distance = 50  # Example value for distance to building
        wind_speed_reduction = calculate_wind_speed_reduction(Cd, h_building, r_distance)
        st.write(f"Windgeschwindigkeitsreduktion durch Gebäude: {wind_speed_reduction:.2f} m/s")

        # Fetch height data from WMS
        wms_url = 'https://www.wms.nrw.de/geobasis/wms_nw_ndom'
        wms = WebMapService(wms_url)

        bbox_size = 0.001
        bbox = (lon - bbox_size, lat - bbox_size, lon + bbox_size, lat + bbox_size)
        width = 400
        height = 300

        img = wms.getmap(layers=['nw_ndom'], srs='EPSG:4326', bbox=bbox, size=(width, height),
                         format='image/png', transparent=True)

        image_bytes = BytesIO(img.read())
        image = Image.open(image_bytes)
        image = image.convert('RGBA')

        # Color to height mapping
        color_to_height = {
            (255, 255, 255, 255): (0, 1.5),
            (31, 120, 180, 255): (1.5, 3.0),
            (54, 214, 209, 255): (3.0, 5.0),
            (64, 207, 39, 255): (5.0, 10.0),
            (255, 255, 71, 255): (10.0, 15.0),
            (255, 206, 71, 255): (15.0, 20.0),
            (255, 127, 0, 255): (20.0, 25.0),
            (215, 25, 28, 255): (25.0, 50.0),
            (114, 0, 11, 255): 50.0
        }

        width, height = image.size
        height_map = np.zeros((height, width))
        pixels = image.load()

        # First pass: Assign height values based on color
        for y in range(height):
            for x in range(width):
                rgba = pixels[x, y]
                if rgba in color_to_height:
                    height_value = color_to_height[rgba]
                    if isinstance(height_value, tuple):
                        height_map[y, x] = np.mean(height_value)
                    else:
                        height_map[y, x] = height_value
                else:
                    height_map[y, x] = np.nan

        # Apply bilinear interpolation to smooth transitions between height ranges
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if not np.isnan(height_map[y, x]):
                    surrounding_values = [
                        height_map[y - 1, x], height_map[y + 1, x],
                        height_map[y, x - 1], height_map[y, x + 1]
                    ]
                    valid_values = [v for v in surrounding_values if not np.isnan(v)]
                    if valid_values:
                        height_map[y, x] = np.mean(valid_values)

        # Reproject the height map from EPSG:4326 to EPSG:3857
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x_coords = np.linspace(bbox[0], bbox[2], width)
        y_coords = np.linspace(bbox[1], bbox[3], height)
        X, Y = np.meshgrid(x_coords, y_coords)
        X, Y = transformer.transform(X, Y)

        # Display the height map
        # Create a new figure and axis explicitly
        fig, ax = plt.subplots()

        # Plot the height map
        im = ax.imshow(height_map, cmap='viridis', interpolation='none', extent=(X.min(), X.max(), Y.min(), Y.max()))
        plt.colorbar(im, ax=ax, label='Height (m)')
        ax.set_title('Height Map (Reprojected)')

        # Display the plot using st.pyplot() with the explicitly created figure
        st.pyplot(fig)

        # Generate the rectangle image
        rectangle_fig = generate_rectangle_image(length_meters, width_meters, rotation_degrees)

        # Display the image in Streamlit
        st.pyplot(rectangle_fig)


    except ValueError as e:
        st.error(str(e))

