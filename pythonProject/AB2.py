import rasterio
from rasterio.plot import show
import numpy as np
from geopy.geocoders import Nominatim
from pyproj import Transformer


# Function to get the value at a specific latitude and longitude
def get_value_at_location(geotiff_path, lat, lon):
    with rasterio.open(geotiff_path) as src:
        # Print raster bounds

        # Transform geographic coordinates to the raster's coordinate system
        transformer = Transformer.from_crs("EPSG:4326", src.crs)
        x, y = transformer.transform(lat, lon)

        row, col = src.index(x, y)

        # Check if the calculated row and col are within bounds
        if (row < 0 or row >= src.height) or (col < 0 or col >= src.width):
            raise ValueError("Latitude and longitude are out of raster bounds.")

        # Read the value at the specified location
        value = src.read(1)[row, col]  # Reading the first band

        return value * 0.84  # Adjust the value to 6 meters height


# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")  # Replace with a unique user agent string
    location = geolocator.geocode(place_name, timeout=30)

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")


def calculate_wind_power(A, v):
    # Definieren Sie die Konstanten
    rho = 1.2255  # Luftdichte in kg/m³
    efficiency = 0.4  # Angenommene Effizienz der Turbine (40%)

    # Berechnung der theoretischen Leistung
    PWind = (rho / 2) * A * v ** 3

    # Berechnung der tatsächlichen Leistung unter Berücksichtigung der Effizienz
    PEffective = PWind * efficiency

    return PEffective


def calculate_annual_energy_output(power):
    # Berechnung der jährlichen Energieproduktion in kWh
    hours_per_year = 24 * 365
    annual_energy_output = power * hours_per_year / 1000  # Umrechnung von Watt in kW
    return annual_energy_output


def calculate_co2_savings(annual_energy_output, co2_per_kwh=0.5):
    # Berechnung der CO2-Einsparung in kg
    co2_savings = annual_energy_output * co2_per_kwh
    return co2_savings


def calculate_total_co2_savings(annual_co2_savings, years):
    # Berechnung der Gesamteinsparung in kg CO2 über die angegebene Anzahl von Jahren
    total_co2_savings = annual_co2_savings * years
    return total_co2_savings


# Path to the GeoTIFF file
geotiff_path = 'C:\\BORO\\suli\\aachen\\6.Semester\\BIM_LCA\\programming\\TIFF\\en_100m_klas.tif'

# Beispielwerte
A = float(input("Geben Sie die Fläche der Turbine in Quadratmetern (m²) ein: "))
place_name = input("Bitte geben Sie den Ort ein (z.B. 'Kölner Dom, Köln'): ")

# Get the coordinates for the place
try:
    lat, lon = get_coordinates_from_place(place_name)

    # Get the value at the specified location and adjust it to 6 meters height
    v = get_value_at_location(geotiff_path, lat, lon)
    print(f'The value at location ({lat}, {lon}) adjusted to 6 meters height is {v}')
except ValueError as e:
    print(e)
    exit(1)

years = int(input("Geben Sie die Anzahl der Jahre ein, für die die Turbine genutzt werden soll: "))

# Berechnung der tatsächlichen Leistung unter Berücksichtigung der Effizienz
wind_power = calculate_wind_power(A, v)
print(f"Die effektive Leistung der Windturbine beträgt: {round(wind_power, 2)} W")

# Berechnung der jährlichen Energieproduktion
annual_energy_output = calculate_annual_energy_output(wind_power)
print(f"Die jährliche Energieproduktion beträgt: {round(annual_energy_output, 2)} kWh")

# Berechnung der jährlichen CO2-Einsparung
annual_co2_savings = calculate_co2_savings(annual_energy_output)
print(f"Die jährliche CO2-Einsparung beträgt: {round(annual_co2_savings, 2)} kg CO2")

# Berechnung der Gesamteinsparung über die angegebene Anzahl von Jahren
total_co2_savings = calculate_total_co2_savings(annual_co2_savings, years)
print(f"Die Gesamteinsparung über {years} Jahre beträgt: {round(total_co2_savings, 2)} kg CO2")
