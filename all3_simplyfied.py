import rasterio
from pyproj import Transformer
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import numpy as np


# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")  # Replace with a unique user agent string
    location = geolocator.geocode(place_name, timeout=30)  # Adjust the timeout value as needed

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")


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
    """
    Calculate the reduction in wind speed due to nearby buildings.

    Parameters:
    Cd (float): Drag coefficient (e.g., 0.8 for now).
    h (float): Height of the building in the direction where wind comes from.
    r (float): Distance between the location and the building.

    Returns:
    float: Reduction in wind speed (ΔV).
    """
    delta_V = Cd * h / r
    return delta_V


# Example usage
if __name__ == "__main__":
    # Path to your geotiff file
    geotiff_path = 'C:\\BORO\\suli\\aachen\\6.Semester\\BIM_LCA\\programming\\TIFF\\en_100m_klas.tif'

    # Get location input from user
    location_text_input = input("Enter a location (e.g., city, address): ")
    h2 = float(input("Enter the height (in meters) for wind speed adjustment: "))

    try:
        # Get coordinates from the location input using Nominatim
        lat, lon = get_coordinates_from_place(location_text_input)

        # Calculate original wind speed at the specified location and height
        original_wind_speed = get_wind_speed_at_height(geotiff_path, lat, lon, h2)

        # Example values for building height and distance
        h_building = 10.0  # Height of the nearby building
        r_building = 50.0  # Distance to the nearby building

        # Calculate wind speed reduction due to nearby building
        Cd = 0.8  # Drag coefficient
        wind_speed_reduction = calculate_wind_speed_reduction(Cd, h_building, r_building)

        # Adjust the original wind speed considering the reduction
        final_wind_speed = original_wind_speed - wind_speed_reduction

        print(f"Original Wind Speed at ({lat:.2f}, {lon:.2f}) at {h2} meters height: {original_wind_speed:.2f} m/s")
        print(f"Wind Speed Reduction due to nearby building: {wind_speed_reduction:.2f} m/s")
        print(f"Final Wind Speed after reduction: {final_wind_speed:.2f} m/s")

    except ValueError as e:
        print(f"Error: {e}")

    except GeocoderTimedOut:
        print("Geocoding service timed out. Please try again later.")
