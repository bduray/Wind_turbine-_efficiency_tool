import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np


def get_daily_forecast(api_key, city):
    url = "https://api.weatherbit.io/v2.0/forecast/daily"
    params = {
        'city': city,
        'key': api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad response status

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def calculate_average_wind_direction(forecast_data):
    wind_directions = []
    for day in forecast_data['data']:
        wind_direction = day['wind_dir']
        wind_directions.append(wind_direction)

    average_wind_direction = np.mean(wind_directions)
    return average_wind_direction


def plot_wind_rose(average_wind_direction):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, polar=True)

    theta = np.deg2rad(np.linspace(0, 360, 16, endpoint=False))
    radii = np.zeros_like(theta) + 10  # Dummy radii, can be adjusted based on wind speed

    ax.plot(theta, radii, color='r', linewidth=1)  # Example plot line

    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('N')
    ax.set_title('Wind Rose')
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

    ax.grid(True)
    plt.show()


def main():
    # Replace with your Weatherbit API key
    api_key = '09a3a1dc997f45e49e62a59d5ac4240b'
    city = 'Aachen'

    # Fetch daily forecast data
    forecast_data = get_daily_forecast(api_key, city)

    if forecast_data:
        print(f"Successfully fetched daily forecast for {city}:")
        for day in forecast_data['data']:
            date = day['datetime']
            wind_direction = day['wind_dir']
            print(f"On {date}, wind direction: {wind_direction} degrees")

        # Calculate average wind direction
        average_wind_direction = calculate_average_wind_direction(forecast_data)
        print(f"Average wind direction over 7 days: {average_wind_direction} degrees")

        # Plot wind rose
        plot_wind_rose(average_wind_direction)

    else:
        print("Failed to fetch daily forecast data.")


if __name__ == "__main__":
    main()

