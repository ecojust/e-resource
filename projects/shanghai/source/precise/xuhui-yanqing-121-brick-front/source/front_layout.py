"""Local metres, +X towards the gabled bay on the right and +Y into the residence."""
from pathlib import Path
import json
from shapely.geometry import box
HERE=Path(__file__).resolve().parents[1]
DATA=json.loads((HERE/'measurements/brick-front-openings.json').read_text())
OPENINGS={key:box(*v['box_xmin_zmin_xmax_zmax']) for key,v in DATA['opening_boxes'].items()}
LEFT=-16.30
RIGHT=-1.72
PARAPET=8.14
