from owslib.wms import WebMapService
from io import BytesIO
from PIL import Image
from geopy.geocoders import Nominatim

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

    # Display the image
    image.show()

else:
    print("Location not found. Please enter a valid location.")
