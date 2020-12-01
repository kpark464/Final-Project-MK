import urllib.request
import urllib.parse
import json
from pprint import pprint
import dateutil.parser

# Useful URLs (you need to add the appropriate parameters for your requests)
MAPQUEST_BASE_URL = "http://www.mapquestapi.com/geocoding/v1/address"
MBTA_BASE_URL = "https://api-v3.mbta.com/stops"
MBTA_PREDICTION_BASE_URL = "https://api-v3.mbta.com/predictions"
MBTA_ROOT_URL = "https://api-v3.mbta.com/"

# Your API KEYS (you need to use your own keys - very long random characters)
MAPQUEST_API_KEY = "o9zmlFPBkUTrYdgeYOLGGMwI2N22hhzw"
MBTA_API_KEY = "15205bbf7f744225b638708280d528f9"


# A little bit of scaffolding if you want to use it

def get_json(url):
    """
    Given a properly formatted URL for a JSON web API request, return
    a Python JSON object containing the response to that request.
    """
    f = urllib.request.urlopen(url)
    response_text = f.read().decode('utf-8')
    response_data = json.loads(response_text)
    return response_data


def get_lat_long(place_name):
    """
    Given a place name or address, return a (latitude, longitude) tuple
    with the coordinates of the given place.
    See https://developer.mapquest.com/documentation/geocoding-api/address/get/
    for Mapquest Geocoding  API URL formatting requirements.
    """

    request_url = map_quest_request_url(place_name)
    try:
        json_data = get_json(request_url)
        lat = json_data["results"][0]["locations"][0]["latLng"]["lat"]
        lng = json_data["results"][0]["locations"][0]["latLng"]["lng"]
        lat_lng = (lat, lng)
        return lat_lng

    except():
        print("Error when fetching lat lng information")
        raise Exception


def map_quest_request_url(place_name):
    params = urllib.parse.urlencode({'key': MAPQUEST_API_KEY, 'location': place_name})
    request_url = MAPQUEST_BASE_URL + "?" + params
    return request_url


def get_nearest_station(latitude, longitude):
    """
    Given latitude and longitude strings, return a (station_name, wheelchair_accessible)
    tuple for the nearest MBTA station to the given coordinates.
    See https://api-v3.mbta.com/docs/swagger/index.html#/Stop/ApiWeb_StopController_index for URL
    formatting requirements for the 'GET /stops' API.
    """
    request_url = mbtq_request_url(latitude, longitude)

    # Add api key to request header
    req = urllib.request.Request(
        request_url,
        headers={"x-api-key": MBTA_API_KEY}
    )

    f = urllib.request.urlopen(req)
    response_text = f.read().decode('utf-8')
    response_data = json.loads(response_text)
    if len(response_data["data"]) > 0:
        nearest_stop = response_data["data"][0]
        attributes = nearest_stop["attributes"]

        wheelchair_info = {
            0: "No information",
            1: "Accessible",
            2: "Inaccessible"
        }

        result_dict = {
            "stop_id": nearest_stop["id"],
            "stop_links": nearest_stop["links"],
            "links": nearest_stop["links"],
            "address": attributes["address"],
            "name": attributes["name"],
            "description": attributes["description"],
            "wheelchair_info": wheelchair_info[attributes["wheelchair_boarding"]],
            "geo_info": {
                "lat": attributes["latitude"],
                "lng": attributes["longitude"]
            },
        }

        bus_arrivals = bus_arrival_prediction(result_dict["stop_id"], 5)
        result_dict['bus_arrivals'] = bus_arrivals

        return result_dict

    return "No nearest MBTA stop found", "No information"


def mbtq_request_url(latitude, longitude):
    params = urllib.parse.urlencode({
        'sort': 'distance',
        'filter[latitude]': latitude,
        'filter[longitude]': longitude,
    })
    request_url = MBTA_BASE_URL + "?" + params
    return request_url


def find_stop_near(place_name):
    """
    Given a place name or address, return the nearest MBTA stop and whether it is wheelchair accessible.
    """
    try:
        lat_lng = get_lat_long(place_name)
        nearest_stop = get_nearest_station(lat_lng[0], lat_lng[1])
        return nearest_stop
    except():
        print("Error when fetching nearest stops")
        raise Exception


def bus_arrival_prediction(stop_id, limit):
    """
    Find the bus arrival time of a specific stop
    """
    params = urllib.parse.urlencode({
        'sort': 'arrival_time',
        'filter[stop]': stop_id,
        'page[limit]': limit
    })
    request_url = MBTA_PREDICTION_BASE_URL + "?" + params

    req = urllib.request.Request(
        request_url,
        headers={"x-api-key": MBTA_API_KEY}
    )

    f = urllib.request.urlopen(req)
    response_text = f.read().decode('utf-8')
    response_data = json.loads(response_text)
    print(response_data['data'])

    result = []
    for arrival in response_data['data']:
        result_dict = {}
        attributes = arrival["attributes"]
        relationships = arrival["relationships"]
        result_dict['direction_id'] = attributes['direction_id']
        result_dict['prediction_id'] = arrival['id']
        result_dict['stop_id'] = relationships['stop']['data']['id']

        arrival_time = attributes['arrival_time']
        if arrival_time is not None:
            arrival_time = dateutil.parser.parse(arrival_time)

        result_dict['arrival_time'] = arrival_time

        vehicle_info = None
        if relationships['vehicle']['data']:
            vehicle_info = get_vehicle_info(relationships['vehicle']['data']['id'])
        result_dict['vehicle_info'] = vehicle_info

        direction_info = get_direction_info(result_dict['direction_id'],
                                            relationships['route']['data']['id'])
        result_dict['direction_info'] = direction_info
        result.append(result_dict)

    return result


def get_vehicle_info(vehicle_id):
    """
        Get vehicle info by vehicle id
    """
    request_url = MBTA_ROOT_URL + "vehicles/" + vehicle_id
    req = urllib.request.Request(
        request_url,
        headers={"x-api-key": MBTA_API_KEY}
    )

    f = urllib.request.urlopen(req)
    response_text = f.read().decode('utf-8')
    response_data = json.loads(response_text)

    attributes = response_data['data']['attributes']
    result_dict = {
        "vehicle_id": vehicle_id,
        "current_status": attributes['current_status'],
        "current_lat": attributes['latitude'],
        "current_lng": attributes['longitude']
    }
    return result_dict


def get_direction_info(direction_id, route_id):
    """
            Get vehicle info by vehicle id
        """
    request_url = MBTA_ROOT_URL + "routes/" + route_id
    # print("route id: {}, direction id: {}".format(route_id, direction_id))
    req = urllib.request.Request(
        request_url,
        headers={"x-api-key": MBTA_API_KEY}
    )

    f = urllib.request.urlopen(req)
    response_text = f.read().decode('utf-8')
    response_data = json.loads(response_text)

    route_data = response_data["data"]
    attributes = route_data["attributes"]
    result_dict = {
        "route_id": route_data["id"],
        "route_color": attributes['color'],
        "destination": attributes['direction_destinations'][direction_id],
        "direction": attributes['direction_names'][direction_id],
    }
    return result_dict

def main():
    """
    You can test all the functions here
    """
    place_name = "30 Leggs Hill Road, Marblehead, MA 01945 Marblehead Massachusetts United States"
    place_name = "150 Humphrey Street, Marblehead, MA 01945 Marblehead Massachusetts United States"
    place_name = "fan pier park"
    lat_lng = get_lat_long(place_name)
    # get_nearest_station(42.489729, -70.892)
    get_nearest_station(lat_lng[0], lat_lng[1])


if __name__ == '__main__':
    main()
