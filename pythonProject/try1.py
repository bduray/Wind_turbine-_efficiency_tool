import tkinter as tk
from PIL import Image, ImageTk
import rasterio
from pyproj import Transformer

# Path to the GeoTIFF file
geotiff_path = 'C:/BORO/suli/aachen/6.Semester/BIM_LCA/programming/TIFF/en_100m_klas.tif'


# Function to handle mouse click events
def on_map_click(event):
    # Get the clicked coordinates
    x, y = event.x, event.y

    # Check if the clicked coordinates are within the image bounds
    if x < 0 or x >= map_width or y < 0 or y >= map_height:
        print("Clicked coordinates are outside the image bounds.")
        return

    # Convert pixel coordinates to geographic coordinates
    lat, lon = transformer.transform(x, y)

    # Get the value at the specified location
    try:
        v = get_value_at_location(lat, lon)
        print(f"The value at location ({lat}, {lon}) is {v}")
    except ValueError as e:
        print(e)


# Function to get the value at a specific latitude and longitude
def get_value_at_location(lat, lon):
    with rasterio.open(geotiff_path) as src:
        transformer = Transformer.from_crs("EPSG:4326", src.crs)
        x, y = transformer.transform(lat, lon)

        row, col = src.index(x, y)

        # Check if the calculated row and col are within bounds
        if (row < 0 or row >= src.height) or (col < 0 or col >= src.width):
            raise ValueError("Latitude and longitude are out of raster bounds.")

        if not (0 <= row < src.height and 0 <= col < src.width):
            raise ValueError("Invalid row or column index.")

        # Read the value at the specified location
        v1 = src.read(1)[row, col]  # Reading the first band

        # Additional processing if needed...

        return v1
