import logging
import requests

SEARCH_API = 'https://restaurant-api.wolt.com/v1/search?sort=releveancy&q={slug}'
INFO_API = 'https://restaurant-api.wolt.com/v3/venues/slug/{slug}'

def get_restaurant_status(slug: str):
    response = requests.get(INFO_API.format(slug=slug))
    response.raise_for_status()

    result = response.json()['results'][0]
    restaurant_name = result['name'][0]['value']

    return (result['online'], restaurant_name, result['public_url'])

def find_restaurant(slug, force_exact_match=False):
    response = requests.get(INFO_API.format(slug=slug))
    response.raise_for_status()

    results = response.json()['results']
    found_restauratns = []

    for result in results[:10]:
        if force_exact_match and result['slug'] != slug:
            continue
        found_restauratns.append(
            {
                'slug' : result['slug'],
                'address' : result['address'],
                'name' : result['name'][0]['value'],
                'url' : result['public_url']
            }
        )

    return found_restauratns
