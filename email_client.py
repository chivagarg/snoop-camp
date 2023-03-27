from collections import defaultdict

import boto3
from botocore.exceptions import ClientError
from recreation_gov_client import RecreationGovClient
from dateutil.relativedelta import relativedelta
from date_time_utils import to_human_readable_dt_format

from campground_ids import CAMPSITE_ID_TO_PARK_DISPLAY_NAME
from test_campgrounds_ids import TEST_CAMPSITE_ID_TO_PARK_DISPLAY_NAME
from typing import Dict, List
from datetime import datetime


class EmailClient:

    def __init__(cls, is_test_mode):
        cls.is_test_mode = is_test_mode

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "snoop-campers@googlegroups.com"

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "snoop-campers@googlegroups.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"

    # The character encoding for the email.
    CHARSET = "UTF-8"

    @classmethod
    def get_reservation_link(cls, campsite_id):
        return "<a href='" + RecreationGovClient.CAMPSITE_RESERVATION_URL.format(campsite_id=campsite_id) + "'>" + campsite_id + "</a>"

    @classmethod
    def build_headline(cls):
        subject = "<html><body><h1>Do you smell the pine cones yet?</h1>" \
                  "<p>Here are some available campsites. Book now!</p>"
        return subject

    def build_html_body(cls, availability: Dict[str, Dict[str, List[datetime]]]) -> str:
        body_html = "<html><body><h1>Do you smell the pine cones yet?</h1><p>Here are some available campsites. Book now!</p><ul>"

        # Keep track of available sites for each campground on each date
        # The available_sites defaultdict tracks the availability of campsites for each campground on each date.
        # The keys of the outer defaultdict correspond to the dates on which the campsites are available, and the
        # values are inner defaultdicts.The keys of the inner defaultdict correspond to the campground IDs, and the
        # values are lists of site IDs that are available on that date.
        # {
        #     datetime.datetime(2023, 8, 31, 0, 0): {
        #         'COUGAR_ROCK': ['6611', '8877'],
        #         'HUCKLEBERRY_MOUNTAIN': ['1234']
        #     },
        #     datetime.datetime(2023, 9, 1, 0, 0): {
        #         'COUGAR_ROCK': ['6611'],
        #         'WHITEWATER_FALLS': ['5555', '6666']
        #     },
        #     datetime.datetime(2023, 9, 2, 0, 0): {
        #         'COUGAR_ROCK': ['6611', '8877']
        #     }
        # }

        available_sites = defaultdict(lambda: defaultdict(list))
        for campground_id, site_id_with_dates in availability.items():
            for site_id, dates in site_id_with_dates.items():
                for date in dates:
                    available_sites[date][campground_id].append(site_id)

        # Append available sites to the HTML in a grouped format
        for day in sorted(available_sites.keys()):
            body_html += f"<li>{to_human_readable_dt_format(day)} - {to_human_readable_dt_format(day + relativedelta(days=2))}<ul>"
            for campground_id, sites in sorted(available_sites[day].items(),
                                               key=lambda item: CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(item[0])): # sorted by name
                sites_str = ", ".join(
                    f"<a href='https://www.recreation.gov/camping/campsites/{site_id}'>{site_id}</a>" for site_id in
                    sorted(sites))
                if cls.is_test_mode:
                    body_html += f"<li>{TEST_CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(campground_id)} : {sites_str[:5]}</li>"
                else:
                    body_html += f"<li>{CAMPSITE_ID_TO_PARK_DISPLAY_NAME.get(campground_id)} : {sites_str}</li>"
            body_html += "</ul></li>"

        body_html += "</ul></body></html>"
        return body_html

    def send_email(cls, weekend_availability, contiguous_availability):
        subject = "[TEST] " if cls.is_test_mode else ""
        if weekend_availability:
            print("Got weekend availability {}", weekend_availability)
            subject += "Snoop camp smells some available campsites (weekends)"
            body_html = cls.build_html_body(weekend_availability)
        elif contiguous_availability:
            print("Got contiguous availability {}", contiguous_availability)
            subject += "Snoop camp smells some available campsites (non weekend)"
            # The HTML body of the email.
            body_html = cls.build_html_body(contiguous_availability)
        else:
            raise Exception('We should not even be here!')

        # The email body for recipients with non-HTML email clients.
        body_text = ("Hello from snoop camp\r\n"
                     "I found some campsites of interest for you!")

        # Create a new SES resource and specify a region.
        client = boto3.client('ses', region_name=cls.AWS_REGION)

        # Try to send the email.
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        "shgar.gir@gmail.com" if cls.is_test_mode else cls.RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': cls.CHARSET,
                            'Data': body_html,
                        },
                        'Text': {
                            'Charset': cls.CHARSET,
                            'Data': body_text,
                        },
                    },
                    'Subject': {
                        'Charset': cls.CHARSET,
                        'Data': subject,
                    },
                },
                Source="shgar.gir@gmail.com" if cls.is_test_mode else cls.SENDER
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
            return False
        else:
            print("Email sent successfully! Message ID:"),
            print(response['MessageId'])
            return True