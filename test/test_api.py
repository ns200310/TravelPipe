import requests
import time

# ICAO for London Heathrow
airport_icao = "EGLL"

# Define time window: from 2 hours ago to now
end_time = int(time.time())
begin_time = end_time - (2 * 3600) 

url = f"https://opensky-network.org/api/flights/arrival?airport={airport_icao}&begin={begin_time}&end={end_time}"

# Note: Using authentication is highly recommended to avoid strict rate limits
response = requests.get(url)

if response.status_code == 200:
    flights = response.json()
    for flight in flights:
        print(f"Flight: {flight['callsign']} | From: {flight['estDepartureAirport']} | Arrival: {time.ctime(flight['firstSeen'])}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)