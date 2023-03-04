OHANAPECOSH_FRIENDLY_NAME = 'Rainier area - Ohanapecosh'
COUGAR_ROCK_FRIENDLY_NAME = 'Rainier area - Cougar Rock'

CAMPGROUND_IDS = {
    # Olympic national park area
    'Olympic area - Hoh Rainforest': '247592',
    'Olympic area - Sol Duc': '251906',
    'Olympic area - Fairholme': '259084',
    'Olympic area - Kalaloch': '232464',
    'Olympic area - Coho': '233384',
    'Olympic area - Willaby': '119290',
    'Olympic area - Falls Creek': '251365',
    # Mt Rainier area (within 2.5 hours of seattle)
    OHANAPECOSH_FRIENDLY_NAME: '232465',
    COUGAR_ROCK_FRIENDLY_NAME: '232466',
    'Rainier area - Big Creek' : '234086',
    'Rainier area - Silver Springs': '232298',
    # North cascades
    'Cascades area - Colonial Creek North': '246855',
    'Cascades area - Colonial Creek South': '255201',
    'Cascades area - Gorge Lake': '10004932',
    'Cascades area - Harlequin': '10101324',
    'Cascades area - Newhalem Creek': '234060',
    # Mt. Baker
    'Baker area - Beckler River': '232018',
    'Baker area - Turlo': '232118',

}

CAMPSITE_ID_TO_PARK_DISPLAY_NAME = {v: k for k, v in CAMPGROUND_IDS.items()}