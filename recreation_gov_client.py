
import requests
import user_agent 

class RecreationGovClient:
    REC_GOV_BASE_URL = "https://www.recreation.gov"
    CAMPSITE_RESERVATION_URL = REC_GOV_BASE_URL + '/camping/campsites/{campsite_id}'
    PARK_AVAILABILITY_ENDPOINT = (
            REC_GOV_BASE_URL + "/api/camps/availability/campground/{park_id}/month"
    )
    ALLOWED_CAMPSITE_TYPES = ['STANDARD NONELECTRIC', 'TENT ONLY NONELECTRIC']

    headers = {"User-Agent": user_agent.generate_user_agent() }
    
    @classmethod
    def get_campground_availability_for_month_range(cls, park_id, months):
        # API expects format like 2023-06-01T00:00:00.000Z
        formatted_months = [m.strftime('%Y-%m-%dT00:00:00.000Z') for m in months]
        campsite_to_available_dates = {}
        for formatted_month in formatted_months:
            params = {"start_date": formatted_month}
            print("Querying for {} with these params: {}".format(park_id, params))
            url = cls.PARK_AVAILABILITY_ENDPOINT.format(park_id=park_id)
            resp = cls.send_request(url, params)

            campsites = resp.get('campsites')

            if not campsites:
                print("No campsites in response! Skipping")
                return {}

            for campsite_id in campsites: # campsite is really campsite_id
                campsite_details = campsites.get(campsite_id)

                if campsite_details.get('campsite_type') not in cls.ALLOWED_CAMPSITE_TYPES:
                    continue

                camp_availabilities = campsite_details.get('availabilities')

                if not camp_availabilities:
                    continue

                for daily_availability in camp_availabilities:
                    if camp_availabilities[daily_availability] == "Available":
                        campsite_to_available_dates.setdefault(campsite_id, []).append(daily_availability)

        return campsite_to_available_dates

    @classmethod
    def send_request(cls, url, params):
        resp = requests.get(url, params=params, headers=cls.headers)
        if resp.status_code != 200:
            raise RuntimeError(
                "failedRequest",
                "ERROR, {status_code} code received from {url}: {resp_text}".format(
                    status_code=resp.status_code, url=url, resp_text=resp.text
                ),
            )
        return resp.json()