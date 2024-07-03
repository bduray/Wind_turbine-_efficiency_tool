from owslib.wms import WebMapService
from io import BytesIO
from PIL import Image
from geopy.geocoders import Nominatim
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

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
    bbox_size = 0.001  # Adjust this value as needed
    bbox = (longitude - bbox_size, latitude - bbox_size,
            longitude + bbox_size, latitude + bbox_size)

    # Define the desired image size
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

    # Iterate through each pixel and map the color to height
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

    # Display the height map using Matplotlib
    plt.imshow(height_map, cmap='viridis', interpolation='none')
    plt.colorbar(label='Height (m)')
    plt.title('Height Map')
    plt.show()

    # Create a 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    X, Y = np.meshgrid(range(width), range(height))
    ax.plot_surface(X, Y, height_map, cmap='viridis')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Height (m)')
    plt.title('3D Height Map')
    plt.show()

    # Save the height map to a CSV file
    df = pd.DataFrame(height_map)
    df.to_csv('height_map.csv', index=False)

else:
    print("Location not found. Please enter a valid location.")
