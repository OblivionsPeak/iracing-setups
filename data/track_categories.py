"""
Track categories for recommendation fuzzy-matching.
When no exact track match exists, recommend setups from the same category.
"""

TRACK_CATEGORIES = {
    'high_speed': [
        'monza', 'spa', 'le_mans', 'daytona_road', 'silverstone',
        'suzuka', 'fuji', 'road_america', 'hockenheim', 'nurburgring_gp',
        'paul_ricard', 'zandvoort',
    ],
    'technical': [
        'laguna_seca', 'hungaroring', 'mid_ohio', 'imola', 'mugello',
        'okayama', 'vallelunga', 'snetterton', 'oulton_park', 'ctmp',
        'portland', 'red_bull_ring',
    ],
    'street': [
        'long_beach', 'cota', 'barber', 'lime_rock',
    ],
    'mixed': [
        'brands_hatch', 'watkins_glen', 'road_atlanta', 'sebring',
        'bathurst', 'phillip_island', 'catalunya', 'interlagos',
        'donington', 'sonoma', 'virginia', 'charlotte_roval',
        'jerez', 'nurburgring_nordschleife', 'indianapolis_road',
    ],
}

# Reverse map: track_key -> category
_TRACK_TO_CATEGORY = {}
for _cat, _tracks in TRACK_CATEGORIES.items():
    for _t in _tracks:
        _TRACK_TO_CATEGORY[_t] = _cat


def get_category(track_key: str) -> str | None:
    return _TRACK_TO_CATEGORY.get(track_key)


def same_category_tracks(track_key: str) -> list[str]:
    """Return all other tracks in the same category."""
    cat = get_category(track_key)
    if not cat:
        return []
    return [t for t in TRACK_CATEGORIES[cat] if t != track_key]
