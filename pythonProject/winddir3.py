import requests

def fetch_historical_weather(api_key, location, start_datetime, end_datetime):
    base_url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/history'
    params = {
        'aggregateHours': '24',  # Aggregate data by 24 hours
        'startDateTime': start_datetime,
        'endDateTime': end_datetime,
        'unitGroup': 'uk',  # Use 'us' for Imperial units
        'contentType': 'csv',  # Output format CSV
        'dayStartTime': '0:0:00',
        'dayEndTime': '0:0:00',
        'location': location,
        'key': api_key,
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        filename = f"{location.replace(',', '_')}_{start_datetime}_{end_datetime}.csv"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded historical weather data to {filename}")
    else:
        print(f"Error fetching data: {response.status_code}")

def main():
    api_key = 'RZVMEQKLB4H52H7TGUUZ6GGDK'
    location = 'Aachen'
    start_datetime = '2019-06-13'
    end_datetime = '2019-06-20'

    fetch_historical_weather(api_key, location, start_datetime, end_datetime)

if __name__ == '__main__':
    main()

