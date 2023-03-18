import json
from dateutil import rrule
from datetime import datetime
from recreation_gov_client import RecreationGovClient
from email_client import EmailClient

from dateutil.relativedelta import relativedelta
from campground_ids import CAMPGROUND_IDS
from test_campgrounds_ids import TEST_CAMPGROUND_IDS
from date_time_utils import get_today

def get_months_to_query(additional_months_to_query_for = 7):
    from_date = get_today()
    # API restriction - we need to query by first of each month we care about
    start = datetime(from_date.year, from_date.month, 1)
    query_until = start + relativedelta(months=additional_months_to_query_for)
    months = list(
        rrule.rrule(rrule.MONTHLY, dtstart=start, until=query_until)
    )
    return months

def get_available_weekend_days(days_available_for_campsite):
    days_in_datetime = [datetime.strptime(d, '%Y-%m-%dT00:00:00Z') for d in days_available_for_campsite]
    days_in_datetime.sort()
    days_with_available_weekend = []
    for i in range(0, len(days_in_datetime)):
        if not days_in_datetime[i].weekday() == 4:
            continue
        if i + 1 < len(days_in_datetime) and days_in_datetime[i] + relativedelta(days=1) == days_in_datetime[i + 1]:
            days_with_available_weekend.append(days_in_datetime[i])

    return days_with_available_weekend

def get_two_contiguously_available_days(days_available_for_campsite):
    days_in_datetime = [datetime.strptime(d, '%Y-%m-%dT00:00:00Z') for d in days_available_for_campsite]
    days_in_datetime.sort()
    days_with_contiguous_availability = []
    for i in range(0, len(days_in_datetime)):
        if i + 1 < len(days_in_datetime) and days_in_datetime[i] + relativedelta(days=1) == days_in_datetime[i + 1]:
            days_with_contiguous_availability.append(days_in_datetime[i])

    return days_with_contiguous_availability

def fetch_filtered_availabilities_for_campgrounds(campgrounds, months):
    weekend_availability_by_campsites = {}
    contiguous_availability_by_campsites = {}

    for campground_id in campgrounds:
        try:
            availabilities = RecreationGovClient.get_campground_availability_for_month_range(campground_id, months)
        except Exception as e:
            print(e)

        if availabilities:
            for campsite_id in availabilities:
                available_weekend_days = get_available_weekend_days(availabilities.get(campsite_id))
                print("Got weekend days {}", available_weekend_days)
                if available_weekend_days:
                    weekend_availability_by_campsites.setdefault(campground_id, {}).update({campsite_id: available_weekend_days})

                available_contiguous_days = get_two_contiguously_available_days(availabilities.get(campsite_id))
                print("Got contiguous availability {}", available_contiguous_days)
                if available_contiguous_days:
                    contiguous_availability_by_campsites.setdefault(campground_id, {}).update({campsite_id: available_contiguous_days})

    return weekend_availability_by_campsites, contiguous_availability_by_campsites


def lambda_handler(event, context):
    is_test_mode = False
    if event and event.get('is_test_mode') == 'True':
        print("This is test mode!")
        is_test_mode = True

    months = get_months_to_query(2 if is_test_mode else 7)

    camground_ids_to_fetch = [TEST_CAMPGROUND_IDS.get(c) for c in TEST_CAMPGROUND_IDS.keys()] if is_test_mode else [CAMPGROUND_IDS.get(c) for c in CAMPGROUND_IDS.keys()]
    
    weekend_availability, contiguous_availability = fetch_filtered_availabilities_for_campgrounds(camground_ids_to_fetch, months)
    print("!!!This is the availability we got!!!")
    print(weekend_availability)

    if not weekend_availability and not contiguous_availability:
        return {
            'statusCode': 200,
            'body': json.dumps('Email not sent - no weekends available!')
        }
    else:
        EmailClient(is_test_mode).send_email(weekend_availability, contiguous_availability, is_test_mode)
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent with available dates!')
        }
