"""Project the five street-wall casements back to each publicly documented photographic view."""
from pathlib import Path
import json
import sys

directory = Path(__file__).resolve().parent
sys.path.insert(0, str(directory.parent / 'source'))
from xiangshan_photo_plane import pixel

# First three apertures were read from the aligned winter frontage, where the
# plane-tree branches cover different parts of the photograph than in July 2018.
# The final pair uses the separate summer/winter point registration.
windows = [
    ('east', -9.857, -8.857, 5.80, 7.043, 2, 3),
    ('east centre', -6.286, -5.40, 5.786, 7.057, 2, 2),
    ('middle', -4.071, -3.414, 5.80, 7.043, 2, 2),
    ('west narrow', -1.646, -.913, 5.896, 7.263, 1, 2),
    ('west paired', .316, 1.394, 6.098, 7.298, 2, 1),
]
slots = []
for label,left,right,bottom,top,columns,rows in windows:
    corners = [(left,0,top),(right,0,top),(right,0,bottom),(left,0,bottom)]
    samples = {camera:[[round(c,2) for c in pixel(p,camera)] for p in corners]
               for camera in ['alignment-roof-0','roof-15-west','2018_commons']}
    slots.append(dict(label=label,left=left,right=right,bottom=bottom,top=top,
                      columns=columns,rows=rows,source_pixels=samples))
out = dict(source='Five street-facing windows below the main eaves. The photographs show two different leaf patterns in the western pair and an iron guard on the eastern windows. The silhouettes of the two western openings were additionally fitted in the 2018 image.',windows=slots)
(directory/'five-main-wall-windows.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
