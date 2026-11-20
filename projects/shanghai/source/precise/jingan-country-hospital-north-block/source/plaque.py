"""Solid, editable characters on the central north entrance plaque."""
from pathlib import Path
from shapely.affinity import translate
from sign_lettering import lettering_shapes


FONT = Path(__file__).with_name('fonts') / 'HospitalPlaqueSubset.otf'


def add_plaque_text(builder):
    for char, outline in lettering_shapes('华东医院', 2.25, .62, font=FONT):
        builder.prism(translate(outline, yoff=5.98), 1.954, 1.993,
                      lambda x, z, distance: (x, -distance, z),
                      'bronze window frame', 'North entry/plaque ' + char)
