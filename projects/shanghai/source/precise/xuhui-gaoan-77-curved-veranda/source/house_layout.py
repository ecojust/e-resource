"""Local axes orient +x along the garden elevation, +y into the house, and +z up."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
STREET=json.loads((HERE.parent/'measurements/relative-street-dimensions.json').read_text())
POST_SPAN=STREET['working_span_m']
DECK_Z=STREET['working_timber_level_m']
CENTRE_X=.765*POST_SPAN
LAYOUT={'post_span':POST_SPAN,'center_x':CENTRE_X,'front_y':0.,'deck_z':DECK_Z}
FIT=json.loads((HERE.parent/'measurements/south-window-and-gallery-fit.json').read_text())
def U(x):return CENTRE_X+x*POST_SPAN
def Z(z):return DECK_Z+z*POST_SPAN
def D(d):return d*POST_SPAN
