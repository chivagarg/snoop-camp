from recreation_gov_client import RecreationGovClient
from datetime import datetime
from unittest.mock import MagicMock
import json
import mock
from lambda_function import lambda_handler
from lambda_function import fetch_filtered_availabilities_for_campgrounds
from email_client import EmailClient
from campground_ids import CAMPGROUND_IDS
from campground_ids import OHANAPECOSH_FRIENDLY_NAME
from campground_ids import COUGAR_ROCK_FRIENDLY_NAME


class TestRecreationClient:
    def test_get_availability_no_campsites_found(self):
        park_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
        month_date = datetime(2023, 6, 1, 0, 0) # June 1st 2023
        RecreationGovClient.send_request = MagicMock(return_value={})
        assert RecreationGovClient.get_campground_availability_for_month_range(park_id, [month_date]) == {}

    @mock.patch("recreation_gov_client.RecreationGovClient.send_request")
    def test_get_availability_for_multiple_months(self, mock_send_request):
        park_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
        from mock_response_availability_1 import MOCK_AVAILABILITY_RESPONSE_JUNE_2591_2_AVAILABLE
        from mock_response_availability_2 import MOCK_AVAILABILITY_RESPONSE_JULY_2591_1_AVAILABLE_2592_2_AVAILABLE
        mock_send_request.side_effect = [MOCK_AVAILABILITY_RESPONSE_JUNE_2591_2_AVAILABLE, MOCK_AVAILABILITY_RESPONSE_JULY_2591_1_AVAILABLE_2592_2_AVAILABLE]
        available = RecreationGovClient.get_campground_availability_for_month_range(park_id, [datetime(2023, 6, 1, 0, 0), datetime(2023, 7, 1, 0, 0)])
        assert available == {
            '2591': ['2023-06-01T00:00:00Z', '2023-06-07T00:00:00Z', '2023-07-22T00:00:00Z'],
            '2592': ['2023-07-01T00:00:00Z', '2023-07-30T00:00:00Z']}

    def test_get_availability_for_single_month(self):
        park_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
        from mock_response_availability_1 import MOCK_AVAILABILITY_RESPONSE_JUNE_2591_2_AVAILABLE
        RecreationGovClient.send_request = MagicMock(return_value=MOCK_AVAILABILITY_RESPONSE_JUNE_2591_2_AVAILABLE)
        available = RecreationGovClient.get_campground_availability_for_month_range(park_id, [datetime(2023, 6, 1, 0, 0)])
        assert available == {'2591': ['2023-06-01T00:00:00Z', '2023-06-07T00:00:00Z']}

class TestLambdaHandler:
    def test_lambda_handler_with_no_available_weekends(self, mocker):
        RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-07T00:00:00Z']})
        mocker.patch('lambda_function.get_months_to_query', return_value=[datetime(2023, 6, 1, 0, 0)])
        response = lambda_handler(MagicMock(), MagicMock())
        assert response == {
            'statusCode': 200,
            'body': json.dumps('Email not sent - no weekends available!')
        }

    def test_lambda_handler_available_weekends_single_campground_single_month(self, mocker):
        RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z']})
        mocker.patch('lambda_function.get_months_to_query', return_value=[datetime(2023, 6, 1, 0, 0)])
        mocker.patch('email_client.EmailClient.send_email')
        response = lambda_handler(MagicMock(), MagicMock())
        assert response == {
            'statusCode': 200,
            'body': json.dumps('Email sent with available dates!')
        }

    def test_lambda_handler_test_mode(self, mocker):
        RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z']})
        mocker.patch('lambda_function.get_months_to_query', return_value=[datetime(2023, 6, 1, 0, 0)])
        mocker.patch('email_client.EmailClient.send_email')
        response = lambda_handler({"is_test_mode":"True"}, MagicMock())
        assert response == {
            'statusCode': 200,
            'body': json.dumps('Email sent with available dates!')
        }

    def test_lambda_handler_available_weekends_single_campground_multiple_month(self, mocker):
        RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z', '2023-07-21T00:00:00Z', '2023-07-22T00:00:00Z', '2023-07-28T00:00:00Z', '2023-07-07T00:00:00Z']})
        mocker.patch('lambda_function.get_months_to_query', return_value=[datetime(2023, 6, 1, 0, 0), datetime(2023, 7, 1, 0, 0)])
        mocker.patch('email_client.EmailClient.send_email')
        response = lambda_handler(MagicMock(), MagicMock())
        assert response == {
            'statusCode': 200,
            'body': json.dumps('Email sent with available dates!')
        }

    def test_availability_by_camp_single_valid_campsite(self):
            ohanapecosh_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
            months = [datetime(2023, 6, 1, 0, 0)]
            RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z']})
            avail_by_campgrounds, _ = fetch_filtered_availabilities_for_campgrounds([ohanapecosh_id], months)
            # June 9 and June 10 are Friday & Saturday so function should return
            assert avail_by_campgrounds == {ohanapecosh_id: {'2591': [datetime(2023, 6, 9, 0, 0)]}}

    @mock.patch("recreation_gov_client.RecreationGovClient.get_campground_availability_for_month_range")
    def test_availability_multiple_campsite(self, mock_get_campground_availability):
            months = [datetime(2023, 6, 1, 0, 0)]
            mock_get_campground_availability.side_effect = [{'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z']},
                                                            {'6622': ['2023-06-23T00:00:00Z', '2023-06-24T00:00:00Z', '2023-06-25T00:00:00Z', '2023-06-26T00:00:00Z']}]
            avail_by_campgrounds_weekend, all_contiguous = fetch_filtered_availabilities_for_campgrounds([CAMPGROUND_IDS[OHANAPECOSH_FRIENDLY_NAME],CAMPGROUND_IDS[COUGAR_ROCK_FRIENDLY_NAME]], months)
            assert avail_by_campgrounds_weekend == {CAMPGROUND_IDS[OHANAPECOSH_FRIENDLY_NAME]: {'2591': [datetime(2023, 6, 9, 0, 0)]},
                                            CAMPGROUND_IDS[COUGAR_ROCK_FRIENDLY_NAME]: {'6622': [datetime(2023, 6, 23, 0, 0)]}}
            assert all_contiguous == {CAMPGROUND_IDS[OHANAPECOSH_FRIENDLY_NAME]: {'2591': [datetime(2023, 6, 9, 0, 0)]},
                                            CAMPGROUND_IDS[COUGAR_ROCK_FRIENDLY_NAME]: {'6622': [datetime(2023, 6, 23, 0, 0),datetime(2023, 6, 24, 0, 0), datetime(2023, 6, 25, 0, 0)]}}


    def test_availability_by_camp_non_contiguous_weekend_days(self):
            months = [datetime(2023, 6, 1, 0, 0)]
            RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-09T00:00:00Z', '2023-06-17T00:00:00Z']})
            avail_by_campgrounds, _ = fetch_filtered_availabilities_for_campgrounds([CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)], months)
            assert avail_by_campgrounds == {}

    def test_availability_by_camp_single_valid_campsite_multiple_months(self):
            ohanapecosh_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
            months = [datetime(2023, 6, 1, 0, 0)]
            RecreationGovClient.get_campground_availability_for_month_range = MagicMock(return_value={'2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z', '2023-06-07T00:00:00Z', '2023-07-21T00:00:00Z', '2023-07-22T00:00:00Z', '2023-07-28T00:00:00Z', '2023-07-07T00:00:00Z']})
            avail_by_campgrounds, _ = fetch_filtered_availabilities_for_campgrounds([ohanapecosh_id], months)
            assert avail_by_campgrounds == {ohanapecosh_id: {'2591': [datetime(2023, 6, 9, 0, 0), datetime(2023, 7, 21, 0, 0)]}}

    def test_availability_by_camp_multiple_valid_campsite_multiple_months(self):
            ohanapecosh_id = CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME)
            months = [datetime(2023, 6, 1, 0, 0), datetime(2023, 7, 1, 0, 0), datetime(2023, 7, 1, 0, 0)]
            RecreationGovClient.get_campground_availability_for_month_range = \
                MagicMock(return_value=
                    {
                        '2591': ['2023-06-01T00:00:00Z', '2023-06-09T00:00:00Z', '2023-06-10T00:00:00Z',
                                 '2023-06-07T00:00:00Z', '2023-07-21T00:00:00Z', '2023-07-22T00:00:00Z',
                                 '2023-07-28T00:00:00Z', '2023-07-07T00:00:00Z'],
                        '2592': ['2023-07-23T00:00:00Z', '2023-07-28T00:00:00Z', '2023-07-29T00:00:00Z',
                                 '2023-08-25T00:00:00Z', '2023-08-26T00:00:00Z','2023-09-25T00:00:00Z']
                     })
            avail_by_campgrounds, _ = fetch_filtered_availabilities_for_campgrounds([ohanapecosh_id], months)
            assert avail_by_campgrounds == {ohanapecosh_id: {'2591': [datetime(2023, 6, 9, 0, 0), datetime(2023, 7, 21, 0, 0)],
                                                       '2592': [datetime(2023, 7, 28, 0, 0), datetime(2023, 8, 25, 0, 0)]}}


class TestEmailClient:
    def test_build_html_body_chronological_multiple_camps(self):
        availability = {
            CAMPGROUND_IDS.get(OHANAPECOSH_FRIENDLY_NAME): {'2591': [datetime(2023, 6, 9, 0, 0),  # June 9th
                                                                     datetime(2023, 7, 21, 0, 0)],  # July 21
                                                            '2592': [datetime(2023, 7, 7, 0, 0),  # July 7
                                                                     datetime(2023, 8, 25, 0, 0)]},  # Aug 25
            CAMPGROUND_IDS.get(COUGAR_ROCK_FRIENDLY_NAME): {'6611': [datetime(2023, 6, 9, 0, 0),  # June 9
                                                                     datetime(2023, 7, 21, 0, 0),  # July 21
                                                                     datetime(2023, 8, 31, 0, 0)],  # Aug 31
                                                            '8877': [datetime(2023, 7, 28, 0, 0),  # July 28
                                                                     datetime(2023, 8, 31, 0, 0)]}  # Aug 31
        }

        expected_html = "<html><body><h1>Do you smell the pine cones yet?</h1>" \
                        "<p>Here are some available campsites. Book now!</p>" \
                        "<ul>" \
                            "<li><h3>Fri, Jun 09 2023 - Sun, Jun 11 2023</h3>" \
                                 "<ul>" \
                                    "<li>" + COUGAR_ROCK_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/6611'>6611</a>" + "</li>" \
                                    "<li>" + OHANAPECOSH_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/2591'>2591</a>" + "</li>" \
                                 "</ul>" \
                            "</li>" \
                            "<li><h3>Fri, Jul 07 2023 - Sun, Jul 09 2023</h3>" \
                                 "<ul>" \
                                     "<li>" + OHANAPECOSH_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/2592'>2592</a>" + "</li>" \
                                  "</ul>" \
                            "</li>" \
                            "<li><h3>Fri, Jul 21 2023 - Sun, Jul 23 2023</h3>" \
                                "<ul>" \
                                    "<li>" + COUGAR_ROCK_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/6611'>6611</a>" + "</li>" \
                                    "<li>" + OHANAPECOSH_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/2591'>2591</a>" + "</li>" \
                                "</ul>" \
                            "</li>" \
                            "<li><h3>Fri, Jul 28 2023 - Sun, Jul 30 2023</h3>" \
                                "<ul>" \
                                    "<li>" + COUGAR_ROCK_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/8877'>8877</a>" + "</li>" \
                                "</ul>" \
                            "</li>" \
                            "<li><h3>Fri, Aug 25 2023 - Sun, Aug 27 2023</h3>" \
                                "<ul>" \
                                    "<li>" + OHANAPECOSH_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/2592'>2592</a>" + "</li>" \
                                "</ul>" \
                            "</li>" \
                            "<li><h3>Thu, Aug 31 2023 - Sat, Sep 02 2023</h3>" \
                                  "<ul>" \
                                     "<li>" + COUGAR_ROCK_FRIENDLY_NAME + " : " + "<a href='https://www.recreation.gov/camping/campsites/6611'>6611</a>" + ", " + "<a href='https://www.recreation.gov/camping/campsites/8877'>8877</a>" + "</li>" \
                                  "</ul>" \
                            "</li>" \
                         "</ul></body></html>"


        assert EmailClient(is_test_mode=False).build_html_body(availability) == expected_html



