"""
Track catalog. Keys are URL-safe slugs used as track_key in the DB.
"""

TRACKS = {
    'barber':           {'name': 'Barber Motorsports Park'},
    'bathurst':         {'name': 'Mount Panorama Circuit'},
    'brands_hatch':     {'name': 'Brands Hatch'},
    'catalunya':        {'name': 'Circuit de Barcelona-Catalunya'},
    'charlotte_roval':  {'name': 'Charlotte Motor Speedway Roval'},
    'cota':             {'name': 'Circuit of the Americas'},
    'ctmp':             {'name': 'Canadian Tire Motorsport Park'},
    'daytona_road':     {'name': 'Daytona International Speedway (Road)'},
    'donington':        {'name': 'Donington Park'},
    'fuji':             {'name': 'Fuji International Speedway'},
    'hockenheim':       {'name': 'Hockenheimring'},
    'hungaroring':      {'name': 'Hungaroring'},
    'imola':            {'name': 'Autodromo Enzo e Dino Ferrari (Imola)'},
    'indianapolis_road':{'name': 'Indianapolis Motor Speedway (Road)'},
    'interlagos':       {'name': 'Autodromo Jose Carlos Pace (Interlagos)'},
    'jerez':            {'name': 'Circuito de Jerez'},
    'laguna_seca':      {'name': 'WeatherTech Raceway Laguna Seca'},
    'le_mans':          {'name': 'Circuit des 24 Heures du Mans'},
    'lime_rock':        {'name': 'Lime Rock Park'},
    'long_beach':       {'name': 'Long Beach Street Circuit'},
    'mid_ohio':         {'name': 'Mid-Ohio Sports Car Course'},
    'monza':            {'name': 'Autodromo Nazionale Monza'},
    'mugello':          {'name': 'Mugello Circuit'},
    'nurburgring_gp':   {'name': 'Nürburgring Grand-Prix-Strecke'},
    'nurburgring_nordschleife': {'name': 'Nürburgring Nordschleife'},
    'okayama':          {'name': 'Okayama International Circuit'},
    'oulton_park':      {'name': 'Oulton Park'},
    'paul_ricard':      {'name': 'Circuit Paul Ricard'},
    'phillip_island':   {'name': 'Phillip Island Circuit'},
    'portland':         {'name': 'Portland International Raceway'},
    'red_bull_ring':    {'name': 'Red Bull Ring'},
    'road_america':     {'name': 'Road America'},
    'road_atlanta':     {'name': 'Road Atlanta'},
    'sebring':          {'name': 'Sebring International Raceway'},
    'silverstone':      {'name': 'Silverstone Circuit'},
    'snetterton':       {'name': 'Snetterton Circuit'},
    'sonoma':           {'name': 'Sonoma Raceway'},
    'spa':              {'name': 'Circuit de Spa-Francorchamps'},
    'suzuka':           {'name': 'Suzuka International Racing Course'},
    'vallelunga':       {'name': 'Autodromo Piero Taruffi (Vallelunga)'},
    'virginia':         {'name': 'Virginia International Raceway'},
    'watkins_glen':     {'name': 'Watkins Glen International'},
    'zandvoort':        {'name': 'Circuit Zandvoort'},
}

# Ordered list of track names for datalist
TRACK_LIST = sorted(
    [{'key': k, 'name': v['name']} for k, v in TRACKS.items()],
    key=lambda x: x['name']
)


def track_display_name(track_key: str) -> str:
    return TRACKS.get(track_key, {}).get('name', track_key)
