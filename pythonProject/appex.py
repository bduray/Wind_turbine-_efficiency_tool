import streamlit as st
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="my_python_geocoder_app")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address
    except GeocoderTimedOut:
        return "Timeout: Unable to get the place name"


st.title("Interactive Map for Wind Turbine Placement")
st.write("Click on the map to get the location coordinates and address.")

m = folium.Map(location=[50.7753, 6.0839], zoom_start=12)
click_handler = folium.LatLngPopup()
m.add_child(click_handler)
map_data = st_folium(m, width=700, height=500)

if map_data['last_clicked'] is not None:
    lat, lon = map_data['last_clicked']['lat'], map_data['last_clicked']['lng']
    st.write(f"Latitude: {lat}, Longitude: {lon}")

    place_name = reverse_geocode(lat, lon)
    st.write(f"Place Name: {place_name}")

# Add additional inputs and calculations here
A = st.number_input("Windturbine Fläche (m²)", min_value=0.0, value=200.0)
h2 = st.number_input("Höhe (in Metern) für die Anpassung", min_value=0.0, value=6.0)
years = st.number_input("Anzahl der Jahre für die Nutzung der Turbine", min_value=1, value=20)

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

