import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta


def fetch_historical_weather(api_key, location, start_date, end_date):
    base_url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history'
    params = {
        'aggregateHours': '24',  # Aggregate data by 24 hours
        'startDateTime': start_date,
        'endDateTime': end_date,
        'unitGroup': 'metric',  # Use 'metric' for metric units
        'contentType': 'json',  # Output format JSON
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


def calculate_average_wind_direction(data):
    if 'locations' in data and data['locations']:
        location_data = data['locations'][list(data['locations'].keys())[0]]
        if 'values' in location_data and location_data['values']:
            values = location_data['values']

            # Extract wind directions from the data
            wind_directions = [entry['wdir'] for entry in values]

            # Convert wind directions to numeric values and then to pandas Series
            wind_directions = pd.Series(pd.to_numeric(wind_directions, errors='coerce'))

            # Calculate circular mean of wind directions
            angles = wind_directions.dropna() * (2 * np.pi / 360)
            sin_sum = sum(np.sin(angles))
            cos_sum = sum(np.cos(angles))
            average_direction = np.arctan2(sin_sum, cos_sum) * (360 / (2 * np.pi))

            # Adjust negative angles to positive equivalent
            if average_direction < 0:
                average_direction += 360

            print(f"Average Wind Direction for the past 30 days: {average_direction:.2f} degrees")
        else:
            print("No 'values' found in the API response. Check the data structure.")
    else:
        print("No 'locations' found in the API response. Check the data structure.")


def main():
    api_key = 'RZVMEQKLB4H52H7TGUUZ6GGDK'
    location = 'Aachen'

    # Calculate start and end dates for the past 30 days
    end_date = date.today().strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Fetch historical weather data for the past 30 days
    data = fetch_historical_weather(api_key, location, start_date, end_date)

    if data:
        # Calculate average wind direction from the API response data
        calculate_average_wind_direction(data)


if __name__ == '__main__':
    main()

