# TomTom_EVSE

This package will allow for systematic queuing of the TomTom ChargingAvailability API for a set of chargers once or at intervals using one or more API keys.

There are two APIs which are neede here - the first is the Point of Interest (POI) API which will be used to find TomTom charger ID's (https://developer.tomtom.com/search-api/api-explorer). The second will be the ChargingAvailability API which will be used to monitor the chargers by ID (doc https://developer.tomtom.com/ev-charging-stations-availability-api/documentation/ev-charging-stations-availability-api/ev-charging-stations-availability).

The POI API is as follows:

(Make an API key - 2500 free calls per day)

Example call for EV charger POI with output as JSON centered on a lon/lat point:

https://api.tomtom.com/search/2/nearbySearch/.json?key={Your_API_Key}&lon=-122.427&lat=37.772&radius=50000&categorySet=7309&countrySet=US


The ChargerAvailability API is as follows:

Example call for status of charger 5551f3a1-4f18-41dd-8097-41c7fd129015 but only the DC L1 plug:

https://api.tomtom.com/search/2/chargingAvailability.json?key={Your_API_Key}&chargingAvailability=5551f3a1-4f18-41dd-8097-41c7fd129015&connectorSet=IEC62196Type2CableAttached&minPowerKW=22.2&maxPowerKW=43.2

Please consult the doc for all fields for both APIs

The desired features are:

1: Return up to N closest chargers to a given Lon/Lat which meet field criteria

2: Return status of all chargers in an iterable of IDs while taking other fields as inputs and alternating amongst an interable of API keys for each call

3: Same as 2 but scheduled to run in backgound at given time intervals (this should be a single call from bash/terminal but does not neet to return the terminal called from)

Exploration code is provided in Dev.ipynb