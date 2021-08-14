import requests

SEARCH_API = 'https://restaurant-api.wolt.com/v1/search?sort=releveancy&q={slug}'
INFO_API = 'https://restaurant-api.wolt.com/v3/venues/slug/{slug}'

def get_restaurant_status(slug: str):
    response = requests.get(INFO_API.format(slug=slug))
    response.raise_for_status()

    result = response.json()['results'][0]
    restaurant_name = result['name'][0]['value']

    return (result['online'], restaurant_name, result['public_url'])

def find_restaurant(query):
    response = requests.get(SEARCH_API.format(slug=query))
    response.raise_for_status()

    results = response.json()['results']
    found_restauratns = []

    for result in results[:10]:
        found_restauratns.append(result['value']['name'][0]['value'])

    return found_restauratns
