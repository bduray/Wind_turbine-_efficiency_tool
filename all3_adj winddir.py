import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta
from owslib.wms import WebMapService
from io import BytesIO
from PIL import Image
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
from pyproj import Geod, Transformer

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
        print(f"Error fetching data: {response.status_code}")
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
            print("No 'values' found in the API response. Check the data structure.")
            return None
    else:
        print("No 'locations' found in the API response. Check the data structure.")
        return None

# Define the WMS URL
wms_url = 'https://www.wms.nrw.de/geobasis/wms_nw_ndom'

# Connect to the WMS service
wms = WebMapService(wms_url)

# Specify the layer containing building height information
building_height_layer = 'nw_ndom'

# Initialize a geocoder
geolocator = Nominatim(user_agent="wms_height_checker")

# Ask the user for a location (address or name of a place)
location_name = input("Enter a location (e.g., address or name of a place): ")

# Geocode the location to get its coordinates (latitude and longitude)
location = geolocator.geocode(location_name)

if location:
    # Extract latitude and longitude coordinates
    latitude = location.latitude
    longitude = location.longitude

    # Define the bounding box (extent) for the area around the specified location
    bbox_size = 0.001
    bbox = (longitude - bbox_size, latitude - bbox_size,
            longitude + bbox_size, latitude + bbox_size)

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

    # Display the image
    image.show()

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
                    height_map[y-1, x], height_map[y+1, x],
                    height_map[y, x-1], height_map[y, x+1]
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

    # Fetch the wind direction
    api_key = 'RZVMEQKLB4H52H7TGUUZ6GGDK'
    location = location_name
    end_date = date.today().strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    data = fetch_historical_weather(api_key, location, start_date, end_date)
    if data:
        average_wind_direction = calculate_average_wind_direction(data)
        if average_wind_direction is not None:
            print(f"Average Wind Direction: {average_wind_direction:.2f} degrees")

            # Initialize distance and find height data
            distance_meters = 5
            max_distance = 100  # Set a maximum search distance to avoid infinite loops
            height_at_new_location = np.nan
            lon2, lat2 = longitude, latitude  # Initialize to the starting coordinates

            geod = Geod(ellps='WGS84')

            while np.isnan(height_at_new_location) and distance_meters <= max_distance:
                lon2, lat2, _ = geod.fwd(longitude, latitude, average_wind_direction, distance_meters)
                lon2_idx = np.argmin(np.abs(x_coords - lon2))
                lat2_idx = np.argmin(np.abs(y_coords - lat2))
                height_at_new_location = height_map[lat2_idx, lon2_idx]
                distance_meters += 3  # Increment the distance in 10 meter steps

            # Calculate the actual distance to the found height data
            if distance_meters <= max_distance:
                actual_distance = geod.inv(longitude, latitude, lon2, lat2)[2]
                print(f"Distance to the found height data: {actual_distance:.2f} meters")
            else:
                print("No building height data found within the maximum search distance.")

            print(f"Endpoint Coordinates: Longitude={lon2}, Latitude={lat2}")
            print(f"Height at the new location (after {distance_meters - 5} meters): {height_at_new_location:.2f} meters")

            # Display the height map and the red dot
            plt.figure()
            plt.imshow(height_map, cmap='viridis', interpolation='none', extent=(X.min(), X.max(), Y.min(), Y.max()))
            plt.colorbar(label='Height (m)')
            plt.title('Height Map (Reprojected)')

            # Add a red dot at the calculated endpoint
            plt.scatter(lon2, lat2, color='red', marker='o', s=100, label='Endpoint')

            plt.xlim(X.min(), X.max())
            plt.ylim(Y.min(), Y.max())
            plt.legend()
            plt.show()

else:
    print("Location not found. Please enter a valid location.")
