from owslib.wms import WebMapService
from io import BytesIO
from PIL import Image
from geopy.geocoders import Nominatim
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer, Geod

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

    # Define the desired direction (in degrees from north)
    direction_degrees = float(input("Enter the direction in degrees (0-360): "))
    distance_meters = 40 # Distance to check in meters

    # Calculate the destination point coordinates
    geod = Geod(ellps='WGS84')
    lon2, lat2, _ = geod.fwd(longitude, latitude, direction_degrees, distance_meters)

    # Define the bounding box around the calculated point
    bbox_size = 0.001  # Adjust this value as needed
    bbox = (lon2 - bbox_size, lat2 - bbox_size,
            lon2 + bbox_size, lat2 + bbox_size)

    # Define the image size
    width = 400  # Width of the image
    height = 300  # Height of the image

    # Get the image from the WMS service
    img = wms.getmap(layers=[building_height_layer],
                     srs='EPSG:4326',  # Projection: EPSG:4326 (same as WMS service)
                     bbox=bbox,
                     size=(width, height),
                     format='image/png',
                     transparent=True)

    # Convert the image content to PIL Image
    image_bytes = BytesIO(img.read())
    image = Image.open(image_bytes)
    image = image.convert('RGBA')

    # Color to height mapping (same as before)
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
                height_map[y, x] = np.nan  # or some default value

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

    # Display the height map using Matplotlib (same as before)
    plt.imshow(height_map, cmap='viridis', interpolation='none', extent=(X.min(), X.max(), Y.min(), Y.max()))
    plt.colorbar(label='Height (m)')
    plt.title('Height Map (Reprojected)')
    plt.show()

    # Find the first height after 10 meters in the specified direction
    # Convert distance to pixels for indexing
    distance_pixels = int(distance_meters / (X.max() - X.min()) * width)

    # Extract the heights in the direction
    if direction_degrees >= 0 and direction_degrees < 90:
        heights_in_direction = height_map[:, :distance_pixels].flatten()
    elif direction_degrees >= 90 and direction_degrees < 180:
        heights_in_direction = height_map[:distance_pixels, :].flatten()
    elif direction_degrees >= 180 and direction_degrees < 270:
        heights_in_direction = height_map[::-1, :distance_pixels].flatten()
    else:
        heights_in_direction = height_map[:, ::-1][:, :distance_pixels].flatten()

    # Find the first non-NaN height
    first_valid_height = next((h for h in heights_in_direction if not np.isnan(h)), None)

    if first_valid_height is not None:
        print(f"The first height after 10 meters in direction {direction_degrees}° is: {first_valid_height} meters.")
    else:
        print("No valid height found after 10 meters in the specified direction.")

else:
    print("Location not found. Please enter a valid location.")

import matplotlib.pyplot as plt

# Display the height map using Matplotlib
plt.figure()

# Plot the height map
plt.imshow(height_map, cmap='viridis', interpolation='none', extent=(X.min(), X.max(), Y.min(), Y.max()))
plt.colorbar(label='Height (m)')
plt.title('Height Map (Reprojected)')

# Calculate the position of the red dot (or marker)
plt.scatter(lon2, lat2, color='red', marker='o', s=100, label='Endpoint')  # Increase marker size to 100

# Adjust plot limits to include the red dot
plt.xlim(X.min(), X.max())
plt.ylim(Y.min(), Y.max())

# Add legend
plt.legend()

# Print the coordinates of the endpoint
print(f"Endpoint Coordinates: Longitude={lon2}, Latitude={lat2}")

# Show the plot
plt.show()


