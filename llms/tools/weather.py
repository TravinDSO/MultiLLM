import requests

class WeatherChecker:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/"
        self.geocode_url = "http://api.openweathermap.org/geo/1.0/direct"

    def get_weather(self, lat, lon):
        weather_url = f"{self.base_url}weather?lat={lat}&lon={lon}&appid={self.api_key}&units=imperial"
        response = requests.get(weather_url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Unable to get weather data"}

    def get_forecast(self, lat, lon):
        forecast_url = f"{self.base_url}forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=imperial"
        response = requests.get(forecast_url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Unable to get forecast data"}

# Test Cell
# Please do not modify
if __name__ == "__main__":
    # Load the env file
    import os
    from dotenv import load_dotenv
    load_dotenv('environment.env', override=True)

    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    weather_checker = WeatherChecker(api_key)

    current_weather = weather_checker.get_weather(78.5097,35.9799)
    forecast = weather_checker.get_forecast(78.5097,35.9799)

    print("Current Weather:")
    print(current_weather)

    print("\nForecast:")
    print(forecast)
