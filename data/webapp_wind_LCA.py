import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MousePosition
import rasterio
from pyproj import Transformer, Geod
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import numpy as np
import requests
import pandas as pd
from datetime import date, timedelta
from owslib.wms import WebMapService
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import math

# Path to your geotiff file
geotiff_path = (''
                './data/en_100m_klas.tif')

# Function to fetch historical weather data
def fetch_historical_weather(api_key, location, start_date, end_date):
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
        st.error(f"Error fetching data: {response.status_code}")
        return None

# Function to calculate the average wind direction
def calculate_average_wind_direction(data):
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
            st.error("No 'values' found in the API response. Check the data structure.")
            return None
    else:
        st.error("No 'locations' found in the API response. Check the data structure.")
        return None

# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")  # Replace with a unique user agent string
    location = geolocator.geocode(place_name, timeout=30)  # Adjust the timeout value as needed

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")

# Function to retrieve place name from coordinates
def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address
    except GeocoderTimedOut:
        return "Timeout: Unable to get the place name"

# Function to get the wind speed at a 100 meters height
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
        h1 = 100  # Standard height ( 100 meters)
        a = 1 / 7  # Power law exponent
        v2 = v1 * ((h2 / h1) ** a)

        return v2

# Function to calculate wind speed reduction due to nearby buildings
def calculate_wind_speed_reduction(Cd, h, r):
    delta_V = Cd * h / r
    return delta_V

# Function to calculate the annual energy output
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
    'coal': 0.87,
    'natural_gas': 0.49,
    'oil': 0.6
}

# Header section
st.title("Efficient Positioning of Wind Turbines")
st.write(
    "Welcome to the Wind Turbine Efficiency Evaluation Tool! Enter turbine details, then select a location on the map,  and click 'Calculate' to assess potential energy output and CO2 savings. Use the resulting height map to refine your location for optimal results.")


# Streamlit App
st.title("Wind Speed Adjustment and Building Height Analysis")


# Input Data
st.write("### Input Data")
h2 = st.number_input("Enter the height (in meters) for wind speed adjustment:", min_value=1.0, value=6.0)
years = st.number_input("Enter the number of years for turbine usage:", min_value=1, value=20)

# Select the type of turbine
turbine_type = st.selectbox("Select the type of wind turbine:", ["Horizontal-Axis Wind Turbine (HAWT)", "Vertical-Axis Wind Turbine (VAWT)"])

# Inputs based on turbine type
if turbine_type == "Horizontal-Axis Wind Turbine (HAWT)":
    radius = st.number_input("Radius of the wind turbine (in meters):", min_value=0.0, value=1.0, step=0.1)
    A = math.pi * radius ** 2
elif turbine_type == "Vertical-Axis Wind Turbine (VAWT)":
    rotor_height = st.number_input("Rotor height (in meters):", min_value=0.0, value=1.0, step=0.1)
    diameter = st.number_input("Rotor diameter (in meters):", min_value=0.0, value=1.5, step=0.1)
    A = rotor_height * diameter  # A simple approximation

# Display the calculated swept area
st.write(f"Calculated swept area of the wind turbine (in square meters): **{A:.2f}**")
#Folium map
st.write("### Select a location on the map ")

map_center = [51.1657, 10.4515]
m = folium.Map(location=map_center, zoom_start=6)
marker = folium.Marker(map_center, popup="Default Location")
m.add_child(marker)
m = folium.Map(location=[50.775346, 6.083887], zoom_start=13)
# Add a mouse position plugin to display latitude and longitude
MousePosition().add_to(m)
# Display the map in Streamlit
output_clicked_coords = st_folium(m, width=700, height=500)


# If user has clicked on the map
if output_clicked_coords['last_clicked']:
    if 'lat' in output_clicked_coords['last_clicked']:
        lat = output_clicked_coords['last_clicked']['lat']
        lon = output_clicked_coords['last_clicked']['lng']
        st.write(f"Selected Coordinates: Latitude = {lat:.2f}, Longitude = {lon:.2f}")
        try:
            place_name = reverse_geocode(lat, lon)
            st.write(f"The chosen location is: **{place_name}**")
        except ValueError as e:
            st.error(str(e))

# Button that triggers the calculations
    if st.button("Calculate"):
        try:
            # Calculate original wind speed at the specified location and height
            original_wind_speed = get_wind_speed_at_height(geotiff_path, lat, lon, h2)

            # Fetch the wind direction and calculate average
            api_key = 'RZVMEQKLB4H52H7TGUUZ6GGDK'
            location = f"{lat},{lon}"
            end_date = date.today().strftime('%Y-%m-%d')
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
            weather_data = fetch_historical_weather(api_key, location, start_date, end_date)
            if weather_data:
                average_wind_direction = calculate_average_wind_direction(weather_data)
                if average_wind_direction is not None:
                    st.write(f"Average Wind Direction: {average_wind_direction:.2f} degrees")

                    # Defined the WMS URL
                    wms_url = 'https://www.wms.nrw.de/geobasis/wms_nw_ndom'

                    # Connection to the WMS service
                    wms = WebMapService(wms_url)
                    # Specify the layer containing building height information
                    building_height_layer = 'nw_ndom'

                    # Define the bounding box (extent) for the area around the specified location
                    bbox_size = 0.001
                    bbox = (lon - bbox_size, lat - bbox_size,
                            lon + bbox_size, lat + bbox_size)

                    # Define the desired image size
                    width = 400
                    height = 300

                    # Get the image from the WMS service
                    img = wms.getmap(layers=[building_height_layer],
                                     srs='EPSG:4326',
                                     bbox=bbox,
                                     size=(width, height),
                                     format='image/png',
                                     transparent=True)

                    # Convert the image content to PIL Image
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

                    # Get image dimensions
                    width, height = image.size

                    # Create an array to hold the height values
                    height_map = np.zeros((height, width))

                    # Load the pixel data
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

                    # Initialize distance and find height data
                    distance_meters = 1
                    max_distance = 100  # Set a maximum search distance to avoid infinite loops
                    height_at_new_location = np.nan
                    lon2, lat2 = lon, lat  # Initialize to the starting coordinates

                    geod = Geod(ellps='WGS84')

                    # Calculate the wind direction range to search (from average_wind_direction - 10° to average_wind_direction + 10°)
                    search_start_direction = int(average_wind_direction - 10)
                    search_end_direction = int(average_wind_direction + 10)

                    # Find the first location with no height data or height data in range 0 to 1.5 meters
                    found_empty_location = False
                    while (not found_empty_location) and distance_meters <= max_distance:
                        # Iterate over the search range
                        for direction in range(search_start_direction, search_end_direction + 1):
                            lon2, lat2, _ = geod.fwd(lon, lat, direction, distance_meters)
                            lon2_idx = np.argmin(np.abs(x_coords - lon2))
                            lat2_idx = np.argmin(np.abs(y_coords - lat2))
                            height_at_new_location = height_map[lat2_idx, lon2_idx]
                            if np.isnan(height_at_new_location) or 0 <= height_at_new_location <= 1.5:
                                found_empty_location = True
                                # First no height data or height in range 0-1.5 meters found at: ({lat2:.2f}, {lon2:.2f})

                                break  # Exit the loop once a suitable location is found
                        if not found_empty_location:
                            distance_meters += 1

                    # If we found a location with no height data or height in range 0-1.5 meters, look for the next height data higher than h2
                    if found_empty_location:
                        # Reset height_at_new_location for the next search
                        height_at_new_location = np.nan
                        while (np.isnan(
                                height_at_new_location) or height_at_new_location <= h2) and distance_meters <= max_distance:
                            # Iterate over the search range
                            for direction in range(search_start_direction, search_end_direction + 1):
                                lon2, lat2, _ = geod.fwd(lon, lat, direction, distance_meters)
                                lon2_idx = np.argmin(np.abs(x_coords - lon2))
                                lat2_idx = np.argmin(np.abs(y_coords - lat2))
                                height_at_new_location = height_map[lat2_idx, lon2_idx]
                                if not np.isnan(height_at_new_location) and height_at_new_location > h2:
                                    actual_distance = geod.inv(lon, lat, lon2, lat2)[2]
                                    st.write(
                                        f"Distance to the first height data higher than {h2} meters: {actual_distance:.2f} meters")
                                    st.write(f"Height at the found location: {height_at_new_location:.2f} meters")
                                    break
                                    # Exit the loop once a suitable location is found
                            if not np.isnan(height_at_new_location) and height_at_new_location > h2:
                                break
                                # Exit the outer while loop as well

                            distance_meters += 1
                            # Increment the distance in 1 meter step

                    # Calculate wind speed reduction due to the building at the new location
                    if np.isnan(height_at_new_location) or height_at_new_location <= h2:
                        wind_speed_reduction = 0

                        #No valid height data found higher than {h2} meters within the maximum search distance.
                        st.write(f"Wind Speed Reduction due to nearby building: {wind_speed_reduction:.2f} m/s")
                    else:
                        # Calculate wind speed reduction due to the building at the new location
                        Cd = 0.8  # Drag coefficient
                        wind_speed_reduction = calculate_wind_speed_reduction(Cd, height_at_new_location,
                                                                              actual_distance)
                        st.write(f"Wind Speed Reduction due to nearby building: {wind_speed_reduction:.2f} m/s")

                    # Adjust the original wind speed considering the reduction
                    final_wind_speed = original_wind_speed - wind_speed_reduction

                    # Check if final wind speed is negative, if so, set it to zero
                    if final_wind_speed < 0:
                        final_wind_speed = 0
                        st.write(
                            "Final Wind Speed after reduction: 0.00 m/s.")
                    else:
                        st.write(
                            f"Original Wind Speed at ({lat:.2f}, {lon:.2f}) at {h2} meters height: {original_wind_speed:.2f} m/s")

                        st.write(f"Final Wind Speed after reduction: {final_wind_speed:.2f} m/s")



                    # Function to calculate wind power
                    def calculate_wind_power(A, final_wind_speed):
                        rho = 1.2255
                        efficiency = 0.4
                        PWind = (rho / 2) * A * final_wind_speed ** 3
                        PEffective = PWind * efficiency
                        return PEffective


                    wind_power = calculate_wind_power(A, final_wind_speed)
                    st.write(f"The effective power of the wind turbine is: **{wind_power:.2f} W**")

                    annual_energy_output = calculate_annual_energy_output(wind_power)
                    st.write(f"The annual energy production is: **{annual_energy_output:.2f} kWh**")

                    annual_co2_savings_coal = calculate_co2_savings(annual_energy_output, emission_factors['coal'])
                    annual_co2_savings_gas = calculate_co2_savings(annual_energy_output,
                                                                   emission_factors['natural_gas'])
                    annual_co2_savings_oil = calculate_co2_savings(annual_energy_output, emission_factors['oil'])

                    total_co2_savings_coal = calculate_total_co2_savings(annual_co2_savings_coal, years)
                    total_co2_savings_gas = calculate_total_co2_savings(annual_co2_savings_gas, years)
                    total_co2_savings_oil = calculate_total_co2_savings(annual_co2_savings_oil, years)

                    st.success(
                        f"The annual CO2 savings compared to natural gas are: **{annual_co2_savings_gas:.2f} kg CO2**")

                    # Plotting the results with custom colors
                    fossil_fuel_types = ['Coal', 'Natural Gas', 'Oil', 'Wind Turbine']
                    total_savings = [annual_co2_savings_coal, annual_co2_savings_gas, annual_co2_savings_oil, 0]

                    # Define colors using hex color codes
                    colors = ['#2d2d96', '#5858cc', '#7e7ed8', '#a4a4e3']

                    fig, ax = plt.subplots()
                    ax.bar(fossil_fuel_types, total_savings, color=colors)
                    ax.set_xlabel('Fossil Fuel Type')
                    ax.set_ylabel('Total CO2  (kg)')
                    ax.set_title(f'Total CO2 for energy over a year')

                    st.pyplot(fig)

                    st.write(f"If the resulting value is not as expected, the following height map can assist. It displays the heights of the surrounding buildings that could affect wind speed, with the chosen location at the center. This visualization can help in determining an alternative location for optimal wind turbine placement.")

                    # Display the height map
                    fig, ax = plt.subplots()

                    # Plot the height map
                    im = ax.imshow(height_map, cmap='viridis', interpolation='none',
                                   extent=(X.min(), X.max(), Y.min(), Y.max()))

                    # Customize color bar
                    plt.colorbar(im, ax=ax, label='Height (m)')

                    # Remove axis labels and ticks
                    ax.set_xticks([])
                    ax.set_yticks([])

                    # Hide the coordinate values displayed on the corners
                    ax.set_xlim(left=X.min(), right=X.max())
                    ax.set_ylim(bottom=Y.min(), top=Y.max())

                    # Add title
                    ax.set_title('Height Map')

                    # Display the plot using st.pyplot() with the explicitly created figure
                    st.pyplot(fig)
        except ValueError as e:
            st.error(f"Error: {e}")
