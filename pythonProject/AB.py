from rasterio.plot import show
import numpy as np
from geopy.geocoders import Nominatim
from pyproj import Transformer


# Function to get coordinates from a place name using Nominatim
def get_coordinates_from_place(place_name):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")  # Replace with a unique user agent string
    location = geolocator.geocode(place_name)

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for place: {place_name}")



# Beispielwerte
A = float(input("Geben Sie die Fläche der Turbine in Quadratmetern (m²) ein: "))
place_name = input("Bitte geben Sie den Ort ein (z.B. 'Kölner Dom, Köln'): ")
height = float(input("Bitte geben Sie die gewünschte Höhe in Metern ein: "))

# Get the coordinates for the place
try:
    lat, lon = get_coordinates_from_place(place_name)

    # Get the value at the specified location and adjust it to the specified height
    v = get_value_at_location_and_height(geotiff_path, lat, lon, height)
    print(f'The value at location ({lat}, {lon}) adjusted to {height} meters height is {v}')
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
