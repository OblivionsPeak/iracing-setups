"""
Track catalog. Keys are URL-safe slugs used as track_key in the DB.

Characteristics used for recommendation matching:
  downforce   : 'low' | 'medium' | 'high' | 'very_high'
  style       : 'flowing' | 'stop_go' | 'mixed'
  tire_stress : 'low' | 'medium' | 'high'
  braking     : 'light' | 'medium' | 'heavy'   (how hard/frequent braking zones are)
  bumpy       : True | False
"""

TRACKS = {
    'barber':            {'name': 'Barber Motorsports Park',                      'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'bathurst':          {'name': 'Mount Panorama Circuit',                        'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': True},
    'brands_hatch':      {'name': 'Brands Hatch',                                  'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'medium',  'bumpy': True},
    'catalunya':         {'name': 'Circuit de Barcelona-Catalunya',                'downforce': 'high',    'style': 'mixed',   'tire_stress': 'high',   'braking': 'medium',  'bumpy': False},
    'charlotte_roval':   {'name': 'Charlotte Motor Speedway Roval',               'downforce': 'low',     'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'cota':              {'name': 'Circuit of the Americas',                       'downforce': 'high',    'style': 'stop_go', 'tire_stress': 'high',   'braking': 'heavy',   'bumpy': True},
    'ctmp':              {'name': 'Canadian Tire Motorsport Park',                 'downforce': 'medium',  'style': 'technical','tire_stress': 'medium','braking': 'medium',  'bumpy': False},
    'daytona_road':      {'name': 'Daytona International Speedway (Road)',         'downforce': 'low',     'style': 'mixed',   'tire_stress': 'low',    'braking': 'medium',  'bumpy': False},
    'donington':         {'name': 'Donington Park',                                'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'fuji':              {'name': 'Fuji International Speedway',                   'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'hockenheim':        {'name': 'Hockenheimring',                                'downforce': 'low',     'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'hungaroring':       {'name': 'Hungaroring',                                   'downforce': 'very_high','style': 'stop_go','tire_stress': 'high',   'braking': 'heavy',   'bumpy': False},
    'imola':             {'name': 'Autodromo Enzo e Dino Ferrari (Imola)',         'downforce': 'high',    'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': True},
    'indianapolis_road': {'name': 'Indianapolis Motor Speedway (Road)',            'downforce': 'low',     'style': 'mixed',   'tire_stress': 'low',    'braking': 'medium',  'bumpy': False},
    'interlagos':        {'name': 'Autodromo Jose Carlos Pace (Interlagos)',       'downforce': 'high',    'style': 'mixed',   'tire_stress': 'high',   'braking': 'medium',  'bumpy': True},
    'jerez':             {'name': 'Circuito de Jerez',                             'downforce': 'high',    'style': 'stop_go', 'tire_stress': 'high',   'braking': 'heavy',   'bumpy': False},
    'laguna_seca':       {'name': 'WeatherTech Raceway Laguna Seca',              'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': True},
    'le_mans':           {'name': 'Circuit des 24 Heures du Mans',                'downforce': 'low',     'style': 'flowing', 'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'lime_rock':         {'name': 'Lime Rock Park',                                'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'low',    'braking': 'light',   'bumpy': False},
    'long_beach':        {'name': 'Long Beach Street Circuit',                     'downforce': 'very_high','style': 'stop_go','tire_stress': 'high',   'braking': 'heavy',   'bumpy': True},
    'mid_ohio':          {'name': 'Mid-Ohio Sports Car Course',                    'downforce': 'medium',  'style': 'technical','tire_stress': 'medium','braking': 'medium',  'bumpy': False},
    'monza':             {'name': 'Autodromo Nazionale Monza',                     'downforce': 'low',     'style': 'flowing', 'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'mugello':           {'name': 'Mugello Circuit',                               'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'high',   'braking': 'medium',  'bumpy': False},
    'nurburgring_gp':    {'name': 'Nürburgring Grand-Prix-Strecke',               'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'nurburgring_nordschleife': {'name': 'Nürburgring Nordschleife',              'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'high',   'braking': 'medium',  'bumpy': True},
    'okayama':           {'name': 'Okayama International Circuit',                 'downforce': 'high',    'style': 'technical','tire_stress': 'medium','braking': 'medium',  'bumpy': False},
    'oulton_park':       {'name': 'Oulton Park',                                   'downforce': 'high',    'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': True},
    'paul_ricard':       {'name': 'Circuit Paul Ricard',                           'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'phillip_island':    {'name': 'Phillip Island Circuit',                        'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'light',   'bumpy': False},
    'portland':          {'name': 'Portland International Raceway',                'downforce': 'high',    'style': 'technical','tire_stress': 'medium','braking': 'medium',  'bumpy': False},
    'red_bull_ring':     {'name': 'Red Bull Ring',                                 'downforce': 'medium',  'style': 'stop_go', 'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'road_america':      {'name': 'Road America',                                  'downforce': 'low',     'style': 'flowing', 'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'road_atlanta':      {'name': 'Road Atlanta',                                  'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': True},
    'sebring':           {'name': 'Sebring International Raceway',                 'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'high',   'braking': 'medium',  'bumpy': True},
    'silverstone':       {'name': 'Silverstone Circuit',                           'downforce': 'high',    'style': 'flowing', 'tire_stress': 'high',   'braking': 'medium',  'bumpy': False},
    'snetterton':        {'name': 'Snetterton Circuit',                            'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'sonoma':            {'name': 'Sonoma Raceway',                                'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'spa':               {'name': 'Circuit de Spa-Francorchamps',                  'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'suzuka':            {'name': 'Suzuka International Racing Course',            'downforce': 'high',    'style': 'flowing', 'tire_stress': 'high',   'braking': 'medium',  'bumpy': False},
    'vallelunga':        {'name': 'Autodromo Piero Taruffi (Vallelunga)',          'downforce': 'high',    'style': 'technical','tire_stress': 'medium','braking': 'medium',  'bumpy': False},
    'virginia':          {'name': 'Virginia International Raceway',                'downforce': 'medium',  'style': 'flowing', 'tire_stress': 'medium', 'braking': 'medium',  'bumpy': False},
    'watkins_glen':      {'name': 'Watkins Glen International',                    'downforce': 'medium',  'style': 'mixed',   'tire_stress': 'medium', 'braking': 'heavy',   'bumpy': False},
    'zandvoort':         {'name': 'Circuit Zandvoort',                             'downforce': 'high',    'style': 'flowing', 'tire_stress': 'high',   'braking': 'medium',  'bumpy': True},
}

# Ordered list of track names for datalist
TRACK_LIST = sorted(
    [{'key': k, 'name': v['name']} for k, v in TRACKS.items()],
    key=lambda x: x['name']
)


def track_display_name(track_key: str) -> str:
    return TRACKS.get(track_key, {}).get('name', track_key)


def track_chars(track_key: str) -> dict:
    """Return characteristic dict for a track, or empty dict if unknown."""
    t = TRACKS.get(track_key, {})
    return {k: v for k, v in t.items() if k != 'name'}


def similarity_score(key_a: str, key_b: str) -> float:
    """
    0.0–1.0 similarity between two tracks based on characteristics.
    Used to pick the closest available setup when no exact match exists.
    """
    a = track_chars(key_a)
    b = track_chars(key_b)
    if not a or not b:
        return 0.0

    _df_order = ['low', 'medium', 'high', 'very_high']
    _br_order = ['light', 'medium', 'heavy']
    _ts_order = ['low', 'medium', 'high']

    def cat_score(va, vb, order):
        if va == vb:
            return 1.0
        ia, ib = order.index(va), order.index(vb)
        return max(0.0, 1.0 - abs(ia - ib) / (len(order) - 1))

    scores = [
        cat_score(a['downforce'],   b['downforce'],   _df_order) * 2.0,  # weighted double
        cat_score(a['braking'],     b['braking'],     _br_order) * 1.5,
        cat_score(a['tire_stress'], b['tire_stress'], _ts_order) * 1.0,
        (1.0 if a['style'] == b['style'] else 0.0) * 1.5,
        (1.0 if a['bumpy'] == b['bumpy'] else 0.5) * 0.5,
    ]
    total_weight = 2.0 + 1.5 + 1.0 + 1.5 + 0.5
    return sum(scores) / total_weight
