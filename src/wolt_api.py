import logging
import requests

SEARCH_API = 'https://restaurant-api.wolt.com/v1/pages/search?q={slug}&lat=32.087236876497585&lon=34.78698525756491'
INFO_API = 'https://restaurant-api.wolt.com/v3/venues/slug/{slug}'

def get_restaurant_status(slug: str):
    response = requests.get(INFO_API.format(slug=slug))
    response.raise_for_status()

    result = response.json()['results'][0]
    restaurant_name = result['name'][0]['value']

    return (result['online'], restaurant_name, result['public_url'])

def is_valid(item, filters):
    for filter_name, allowed_values in filters.items():
        logging.debug(f'Checking {filter_name}')
        if not item.get(filter_name, None) in allowed_values:
            return False
    return True

def find_restaurant(slug, filters, force_exact_match=False):
    if force_exact_match:
        url = INFO_API.format(slug=slug)
        logging.info(f'Searching for exact match: {slug} - {url}')
        response = requests.get(url)
        if response.json().get('results', None) is None:
            logging.debug(f'No match for slug: {slug}')
            return []
        
        result = response.json()['results'][0]
        restaurant_name = result['name'][0]['value']
        return [{
            'online' : result['online'],
            'slug' : result['slug'],
            'address' : result['address'],
            'name' : restaurant_name,
            'url' : result['public_url']
        }]

    
    response = requests.get(SEARCH_API.format(slug=slug))
    response.raise_for_status()

    results = response.json()['sections'][0]['items']
    found_restauratns = []

    for result in results[:10]:
        venue = result['venue']
        if force_exact_match and venue['slug'] != slug:
            continue
        if not force_exact_match:
            result = venue['name']

        if not is_valid(venue, filters):
            continue

        info = get_restaurant_status(venue['slug'])
        found_restauratns.append(
            {
                'online' : info[0],
                'slug' : venue['slug'],
                'address' : venue['address'],
                'name' : venue['name'],
                'url' : info[2]
            }
        )

    return found_restauratns
