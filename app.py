from flask import Flask, jsonify, request
from w3lib.html import get_base_url
import extruct
import requests

app = Flask(__name__)


def extract_osm_tags(data):
    tags = {}

    schema_org_type = data.get('@type')

    if schema_org_type == 'Restaurant':
        tags['amenity'] = 'restaurant'

        serves_cuisine = tags.get('servesCuisine')
        if serves_cuisine:
            cuisine = []

            if 'Burgers' in serves_cuisine:
                cuisine.append('burger')
            if 'Fast Casual' in serves_cuisine:
                tags['amenity'] = 'fast_food'
    elif schema_org_type == 'Hotel':
        tags['tourism'] = 'hotel'
    elif schema_org_type == 'ExerciseGym':
        tags['leisure'] = 'fitness_centre'
    elif schema_org_type == 'BankOrCreditUnion':
        tags['amenity'] = 'bank'
    else:
        return {}

    address = data.get('address', {}).get('streetAddress')
    if address:
        tags['addr:full'] = address
    address = data.get('address', {}).get('addressLocality')
    if address:
        tags['addr:city'] = address
    address = data.get('address', {}).get('addressRegion')
    if address:
        tags['addr:state'] = address
    address = data.get('address', {}).get('streetAddress')
    if address:
        tags['postcode'] = address
    address = data.get('address', {}).get('addressCountry')
    if address:
        tags['addr:country'] = address

    brand = data.get('brand')
    if brand:
        tags['brand'] = brand

    name = data.get('name')
    if name:
        tags['name'] = name

    telephone = data.get('telephone')
    if telephone:
        tags['phone'] = telephone
    faxNumber = data.get('faxNumber')
    if faxNumber:
        tags['fax'] = faxNumber

    url = data.get('url')
    if url:
        tags['website'] = url

    return tags

@app.route("/extract")
def extract():
    url = request.args.get('url')

    if not url:
        return jsonify(error="Must specify url parameter"), 400

    app.logger.info("Extracting json-ld from %s", url)

    r = requests.get(url)

    if r.status_code != 200:
        app.logger.info("HTTP %s from %s", r.status_code, url)
        return jsonify(error="Error fetching url"), 502

    base_url = get_base_url(r.text, r.url)
    data = extruct.extract(r.text, base_url=base_url, syntaxes=["json-ld"])
    data = data.get('json-ld')

    output = {}
    suggested_tags = {}
    for entry in data:
        suggested_tags.update(extract_osm_tags(entry))

    output = {
        'status': {
            'url': url,
            'success': len(suggested_tags) > 0,
        },
        'suggested_tags': suggested_tags,
    }

    if request.args.get('include_extracted', type=bool):
        output['extracted'] = data

    return jsonify(output)
