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

def is_valid(item, filters):
    for filter_name, allowed_values in filters.items():
        if not item.get(filter_name, None) in allowed_values:
            return False
    return True

def find_restaurant(slug, filters, force_exact_match=False):
    if force_exact_match:
        response = requests.get(INFO_API.format(slug=slug))
    else:
        response = requests.get(SEARCH_API.format(slug=slug))
    response.raise_for_status()

    results = response.json()['results']
    found_restauratns = []

    for result in results[:10]:
        if force_exact_match and result['slug'] != slug:
            continue
        if not force_exact_match:
            result = result['value']

        if not is_valid(result, filters):
            continue

        found_restauratns.append(
            {
                'online' : result['online'],
                'slug' : result['slug'],
                'address' : result['address'],
                'name' : result['name'][0]['value'],
                'url' : result['public_url']
            }
        )

    return found_restauratns
