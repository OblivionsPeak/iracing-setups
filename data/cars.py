"""
Car catalog. Keys are the iRacing car path slugs (as returned by setupdelta carName).
Multiple aliases per car handle legacy naming variations.
"""

# Map: car_key -> {name, class, aliases}
# aliases = other slugs the setupdelta API may return for the same car
CARS = {
    # ── GT3 ──────────────────────────────────────────────────────────────────
    'acuransxevogt3':           {'name': 'Acura NSX GT3 EVO22',              'class': 'GT3'},
    'amvantagegt3':             {'name': 'Aston Martin Vantage GT3',         'class': 'GT3'},
    'amvantageevogt3':          {'name': 'Aston Martin Vantage AMR GT3 EVO', 'class': 'GT3'},
    'audir8lmsevo2gt3':         {'name': 'Audi R8 LMS GT3 EVO II',           'class': 'GT3'},
    'bmwm4gt3':                 {'name': 'BMW M4 GT3',                       'class': 'GT3'},
    'bmwz4gt3':                 {'name': 'BMW Z4 GT3',                       'class': 'GT3'},
    'chevyvettez06rgt3':        {'name': 'Chevrolet Corvette Z06 GT3.R',     'class': 'GT3'},
    'ferrari296gt3':            {'name': 'Ferrari 296 GT3',                  'class': 'GT3'},
    'ferrari488gt3':            {'name': 'Ferrari 488 GT3',                  'class': 'GT3'},
    'ferrarievogt3':            {'name': 'Ferrari 296 GT3 EVO',              'class': 'GT3'},
    'fordgt':                   {'name': 'Ford GT GT3',                      'class': 'GT3'},
    'fordmustanggt3':           {'name': 'Ford Mustang GT3',                 'class': 'GT3'},
    'lamborghinievogt3':        {'name': 'Lamborghini Huracán GT3 EVO',      'class': 'GT3'},
    'mercedesamggt3':           {'name': 'Mercedes-AMG GT3',                 'class': 'GT3'},
    'mercedesamgevogt3':        {'name': 'Mercedes-AMG GT3 EVO',             'class': 'GT3'},
    'mclaren720sgt3':           {'name': 'McLaren 720S GT3 EVO',             'class': 'GT3'},
    'porsche911rgt3':           {'name': 'Porsche 911 GT3 R (992)',          'class': 'GT3'},
    'porsche992rgt3':           {'name': 'Porsche 911 GT3 R (992)',          'class': 'GT3'},

    # ── GT4 ──────────────────────────────────────────────────────────────────
    'amvantagegt4':             {'name': 'Aston Martin Vantage GT4',         'class': 'GT4'},
    'audir8gt4':                {'name': 'Audi R8 LMS GT4',                  'class': 'GT4'},
    'bmwm4evogt4':              {'name': 'BMW M4 GT4',                       'class': 'GT4'},
    'bmwm4gt4':                 {'name': 'BMW M4 GT4',                       'class': 'GT4'},
    'chevycamarogt4':           {'name': 'Chevrolet Camaro GT4.R',           'class': 'GT4'},
    'fordmustanggt4':           {'name': 'Ford Mustang GT4',                 'class': 'GT4'},
    'hyundaivelostern':         {'name': 'Hyundai Elantra N GT4',            'class': 'GT4'},
    'ktmxbowgt4':               {'name': 'KTM X-Bow GT4',                   'class': 'GT4'},
    'maseratigranturismo':      {'name': 'Maserati MC GT4',                  'class': 'GT4'},
    'mclaren570sgt4':           {'name': 'McLaren 570S GT4',                 'class': 'GT4'},
    'mercedesamggt4':           {'name': 'Mercedes-AMG GT4',                 'class': 'GT4'},
    'porsche718gt4':            {'name': 'Porsche 718 Cayman GT4 Clubsport', 'class': 'GT4'},
    'porsche9922cup':           {'name': 'Porsche 718 GT4 RS Clubsport',     'class': 'GT4'},
    'toyotagrsupra':            {'name': 'Toyota GR Supra GT4',              'class': 'GT4'},
    'toyotagrsupragtfour':      {'name': 'Toyota GR Supra GT4',              'class': 'GT4'},

    # ── LMP2 / LMP3 ──────────────────────────────────────────────────────────
    'dallarap217':              {'name': 'Dallara P217 LMP2',                'class': 'LMP2'},
    'ligierjsp320':             {'name': 'Ligier JS P320 LMP3',              'class': 'LMP3'},

    # ── GTE ──────────────────────────────────────────────────────────────────
    'bmwm8gte':                 {'name': 'BMW M8 GTE',                       'class': 'GTE'},
    'ferrari488gte':            {'name': 'Ferrari 488 GTE',                  'class': 'GTE'},
    'c8rvettegte':              {'name': 'Chevrolet Corvette C8.R GTE',      'class': 'GTE'},
    'porsche991rsr':            {'name': 'Porsche 911 RSR',                  'class': 'GTE'},

    # ── Porsche Cup ───────────────────────────────────────────────────────────
    'porsche911cup':            {'name': 'Porsche 911 GT3 Cup (991)',        'class': 'Porsche Cup'},
    'porsche992cup':            {'name': 'Porsche 911 GT3 Cup (992)',        'class': 'Porsche Cup'},

    # ── GTP ──────────────────────────────────────────────────────────────────
    'acuraarx06gtp':            {'name': 'Acura ARX-06 GTP',                 'class': 'GTP'},
    'bmwlmdh':                  {'name': 'BMW M Hybrid V8',                  'class': 'GTP'},
    'cadillacvseriesrgtp':      {'name': 'Cadillac V-Series.R GTP',         'class': 'GTP'},
    'porsche963gtp':            {'name': 'Porsche 963 GTP',                  'class': 'GTP'},
    'ferrari499p':              {'name': 'Ferrari 499P',                     'class': 'GTP'},
}

# Class ordering for display grouping
CLASS_ORDER = ['GT3', 'GT4', 'GTE', 'LMP2', 'LMP3', 'GTP', 'Porsche Cup', 'Other']


def get_car(car_key: str) -> dict:
    """Return car info dict or a fallback with the raw key as name."""
    return CARS.get(car_key, {'name': car_key, 'class': 'Other'})


def car_display_name(car_key: str) -> str:
    return get_car(car_key)['name']


def car_class(car_key: str) -> str:
    return get_car(car_key)['class']


def all_cars_grouped() -> dict:
    """Return cars grouped by class, sorted within each group."""
    grouped = {}
    for key, info in CARS.items():
        cls = info['class']
        grouped.setdefault(cls, [])
        grouped[cls].append({'key': key, 'name': info['name']})
    # Sort within each group by name
    for cls in grouped:
        grouped[cls].sort(key=lambda x: x['name'])
    # Return ordered dict
    return {cls: grouped[cls] for cls in CLASS_ORDER if cls in grouped}
