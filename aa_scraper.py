import asyncio, json
from datetime import datetime
from playwright.async_api import async_playwright
from curl_cffi import AsyncSession

async def api_caller(session, url, headers, payload, cookies, method):
    max_retries = 5
    retries = 0
    while retries<max_retries:
        try:
            if method == "GET":
                response = await session.get(url, headers=headers, cookies=cookies, impersonate="chrome")
                if response.status_code != 200:
                    retries+=1
                    if retries>=max_retries:
                        print(f"Failed to fetch {url}, status:{response.status_code}")
                        return None
                else:
                    return response.json()
            else:
                response = await session.post(url, headers=headers,json=payload, cookies=cookies, impersonate="chrome")
                if response.status_code != 200:
                    retries+=1
                    if retries>=max_retries:
                        print(f"Failed to fetch {url}, status:{response.status_code}")
                        return None
                else:
                    return response.json()
        except Exception as e:
            retries+=1
            if retries>=max_retries:
                print(f"Failed to fetch {url}, error:{e}")
                return None

async def extract_time(input_time):
    dt = datetime.fromisoformat(input_time)
    return dt.strftime("%H:%M")

async def convert_duration(duration_in_minutes):
    hours = duration_in_minutes // 60  
    minutes = duration_in_minutes % 60 
    return f"{hours}h {minutes}m"

async def parse_award_pricing_json(json_data):
    award_price_details = {}
    for slice in json_data.get("slices", []):
        award_price_details[slice.get("hash")] = {}
        for pricingDetail in slice.get("pricingDetail", []):
            if pricingDetail.get("benefitKey") == "COACH":
                award_price_details[slice.get("hash")]['points_required'] = pricingDetail.get("perPassengerAwardPoints")
                award_price_details[slice.get("hash")]['taxes_fees_usd'] = pricingDetail.get("perPassengerTaxesAndFees", {}).get("amount")  
    return award_price_details

async def award_pricing_api(session, headers, adults, origin, destination, date, cookies):
    payload = {
        'metadata': {
            'selectedProducts': [],
            'tripType': 'OneWay',
            'udo': {},
        },
        'passengers': [
            {
                'type': 'adult',
                'count': adults,
            },
        ],
        'requestHeader': {
            'clientId': 'AAcom',
        },
        'slices': [
            {
                'allCarriers': True,
                'cabin': '',
                'departureDate':f'{date}',
                'destination': f'{destination}',
                'destinationNearbyAirports': False,
                'maxStops': None,
                'origin': f'{origin}',
                'originNearbyAirports': False,
            },
        ],
        'tripOptions': {
            'corporateBooking': False,
            'fareType': 'Lowest',
            'locale': 'en_US',
            'pointOfSale': None,
            'searchType': 'Award',
        },
        'loyaltyInfo': None,
        'version': '',
        'queryParams': {
            'sliceIndex': 0,
            'sessionId': '',
            'solutionSet': '',
            'solutionId': '',
            'sort': 'CARRIER',
        },
    }
    url = 'https://www.aa.com/booking/api/search/itinerary'
    json_data = await api_caller(session, url, headers, payload, cookies, "POST")
    return json_data
    
async def parse_cash_pricing_json(json_data):
    cash_price_details = {}
    for slice in json_data.get("slices", []):
        cash_price_details[slice.get("hash")] = {}
        cash_price_details[slice.get("hash")]['is_nonstop'] = True if slice.get("stops") == 0 else False
        cash_price_details[slice.get("hash")]['segments'] = []
        for segment in slice.get("segments", []):
            cash_price_details[slice.get("hash")]['segments'].append({
                "flight_number": f'{segment.get("flight",{}).get("carrierCode")}{segment.get("flight",{}).get("flightNumber")}',
                "departure_time": await extract_time(segment.get("departureDateTime")),
                "arrival_time": await extract_time(segment.get("arrivalDateTime"))
            })
        cash_price_details[slice.get("hash")]['total_duration'] = await convert_duration(slice.get("durationInMinutes"))
        cash_price_details[slice.get("hash")]['points_required'] = None
        for pricingDetail in slice.get("pricingDetail", []):
            if pricingDetail.get("productGroup") == "MAIN" and pricingDetail.get("productType") == "COACH":
                cash_price_details[slice.get("hash")]['cash_price_usd'] = pricingDetail.get("allPassengerDisplayTotal", {}).get("amount")
    return cash_price_details  

async def cash_pricing_api(session, headers, adults, origin, destination, date, cookies):
    payload = {
        'metadata': {
            'selectedProducts': [],
            'tripType': 'OneWay',
            'udo': {
                'search_method': 'Lowest',
            },
        },
        'passengers': [
            {
                'type': 'adult',
                'count': adults,
            },
        ],
        'requestHeader': {
            'clientId': 'AAcom',
        },
        'slices': [
            {
                'allCarriers': True,
                'cabin': '',
                'departureDate':f'{date}',
                'destination': f'{destination}',
                'destinationNearbyAirports': False,
                'maxStops': None,
                'origin': f'{origin}',
                'originNearbyAirports': False,
            },
        ],
        'tripOptions': {
            'corporateBooking': False,
            'fareType': 'Lowest',
            'locale': 'en_US',
            'pointOfSale': None,
            'searchType': 'Revenue',
        },
        'loyaltyInfo': None,
        'version': 'cfr',
        'queryParams': {
            'sliceIndex': 0,
            'sessionId': '',
            'solutionSet': '',
            'solutionId': '',
            'sort': 'CARRIER',
        },
    }
    url = 'https://www.aa.com/booking/api/search/itinerary'
    json_data = await api_caller(session, url, headers, payload, cookies, "POST")
    return json_data

async def get_output_json(cash_pricing_json, award_pricing_json):
    output_json = {}
    output_json['search_metadata'] = {}
    output_json['search_metadata']['origin'] = cash_pricing_json['utag']['search_origin_city']
    output_json['search_metadata']['destination'] = cash_pricing_json['utag']['search_destination_city']
    output_json['search_metadata']['date'] = cash_pricing_json['responseMetadata']['departureDate']
    output_json['search_metadata']['passengers'] = cash_pricing_json['utag']['adult_passengers']
    output_json['search_metadata']['cabin_class'] = "economy"
    cash_price_details = await parse_cash_pricing_json(cash_pricing_json)
    award_price_details = await parse_award_pricing_json(award_pricing_json)
    output_json['flights'] = []
    for key in cash_price_details:
        if key not in award_price_details:
            continue
        output_json['flights'].append({
            "is_nonstop":cash_price_details[key]['is_nonstop'],
            "segments":cash_price_details[key]['segments'],
            "total_duration":cash_price_details[key]['total_duration'],
            "points_required":award_price_details.get(key,{}).get("points_required"),
            "cash_price_usd":cash_price_details[key]['cash_price_usd'],
            "taxes_fees_usd":award_price_details.get(key,{}).get("taxes_fees_usd",0),
            "cpp":round(((cash_price_details[key]['cash_price_usd'] - award_price_details.get(key,{}).get("taxes_fees_usd"))/award_price_details.get(key,{}).get("points_required"))*100, 2)
        })
    output_json['total_results'] = len(output_json['flights'])
    return output_json

async def get_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--no-first-run", "--no-default-browser-check"]
        )
        context = await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.aa.com/homePage.do", wait_until="domcontentloaded")
        cookies = await context.cookies()
        cookies = {c['name']: c['value'] for c in cookies}
        await browser.close()
        return cookies

async def main(headers):
    async with AsyncSession() as session:
        cookies = await get_cookies()

        adults = 1
        origin = "LAX"
        destination = "JFK"
        date = "2025-12-15"

        cash_pricing_json = await cash_pricing_api(session, headers, adults, origin, destination, date, cookies)
        award_pricing_json = await award_pricing_api(session, headers, adults, origin, destination, date, cookies)
        return await get_output_json(cash_pricing_json, award_pricing_json)

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US',
    'content-type': 'application/json',
    'origin': 'https://www.aa.com',
    'priority': 'u=1, i',
    'referer': 'https://www.aa.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

final_json = asyncio.run(main(headers))

with open("result.json", "w", encoding="utf-8") as fp:
    json.dump(final_json, fp, indent=4)