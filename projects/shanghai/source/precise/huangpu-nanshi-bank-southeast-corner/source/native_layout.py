"""Named editable groups and native cameras for the southeast cut corner."""
from hashlib import sha256
import json

SCHEDULE_SHA256 = '3c2a8c5ea0eaa03e78ad8dc1c79ac13ee08ca6a8a146b350a4a238a2d3cce352'

# Blender object names hold at most 63 UTF-8 bytes. The source label survives in a property.
ALIASES = {
    'Southeast chamfer/medallion/photographed-monogram/raised gilded face':
        'Southeast chamfer/medallion/monogram/gilded face',
    'Southeast chamfer/medallion/photographed-monogram/rounded gold shoulder':
        'Southeast chamfer/medallion/monogram/gold shoulder',
    'Southeast chamfer/swag under street-facing rectangular window/ribbon':
        'Southeast chamfer/swag below rectangular window/ribbon',
}

# Eye and target in local metres. Orthographic scale uses the long axis of the portrait frame.
CAMERAS = {
    'Small East Gate southeast corner': ((6,-31,8.6), (0,.6,9.6), 22.2),
    'Fangbang Road balcony ironwork': ((-10,-8,7.95), (-2.68,1.46,8.8), 9.3),
    'Renmin Road window pediment': ((10,-8,11.87), (2.78,1.25,11.62), 7.0),
    'Four gilt shop characters': ((-1.4,-15,9.1), (0,0,9.38), 9.9),
    'Round monogram and 1783 numerals': ((.9,-10,15.14), (0,0,15.12), 5.8),
    'Open pavilion and stone urns': ((-2.3,-10,17.83), (0,.79,18.04), 6.7),
    'January 2021 street enclosures': ((2.5,-15,2.65), (0,.42,2.65), 10.6),
}
MAIN = next(iter(CAMERAS))

def schedule_hash(groups):
    encoded = json.dumps(groups,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    return sha256(encoded).hexdigest()
