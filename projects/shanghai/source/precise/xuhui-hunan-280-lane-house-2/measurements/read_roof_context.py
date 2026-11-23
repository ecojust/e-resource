"""Measure visible front-to-back roof lines and document the intentionally open rear survey."""
from pathlib import Path
import json
from math import hypot
from hashlib import sha256
import sys

SOURCE = Path(__file__).resolve().parent
# Pixels in the 270 × 226 private study crop, translated by (+186,+212) into the
# 640 x 640 Wayback mosaics. Independent digitisation, not the statutory grant boundary.
PICKS = {
    '13240': {'front': [[102,138],[161,133]], 'east':None, 'status':'Tree cover obscures the rear roof. Bright southern face readable.'},
    '8432': {'front':[[100,137],[161,131]], 'east':[[161,131],[154,98]], 'status':'Southern parapet-to-roof break and eastern side readable. Northwest line interrupted by canopy and shadow.'},
    '39767': {'front':[[75,143],[151,136]], 'east':[[151,136],[147,104]], 'status':'Front lip visible in two separated stretches. Rooftop service equipment and vegetation cover the intervening part.'},
    '3692': {'front':None,'east':[[154,140],[151,101]], 'status':'Eastern rectangular pale roof strip is readable. Dark roof to its west merges into the neighbouring canopy; record no continuous north or west outline.'},
}

def read(folder):
    result={}
    for k,p in PICKS.items():
        j=json.loads((folder/f'release-{k}.json').read_bytes())
        usable=next(v['records'][0]for v in j['metadata']if v['records'] and v['records'][0].get('SRC_DATE'))
        def value(pts):return None if pts is None else {'study_pixels':pts,'mosaic_pixels':[[x+186,y+212]for x,y in pts],'plan_distance_m':hypot(pts[0][0]-pts[1][0],pts[0][1]-pts[1][1])*j['meters_per_pixel']}
        result[k]={'source_exposure_date':usable['SRC_DATE'],'source_resolution_m':usable.get('SRC_RES'),'mosaic_scale_m_per_pixel':j['meters_per_pixel'],'street_roof_line':value(p['front']),'east_roof_line':value(p['east']),
                   'status':p['status'],'image_url_template':j['release']['itemURL'],'tile_sha256s':[a['sha256']for a in j['tiles']],'metadata_record_url':next(v['url']for v in j['metadata']if v['records']and v['records'][0].get('SRC_DATE'))}
    return {'scope':'WGS registration follows the independent eight-camera ground origin. The aerial estimates are lengths within each dated image: high-edge parallax and tree cover preclude treating their absolute map pixels as ground corners. East side evidenced for about 8–10 m. The western and north edges are not jointly resolved in these dates. No full footprint or inferred flat roof is authored. The red tiled spread east of the pale roof is a separate building, aligned with ordinary feature #716.','source_image_policy':'Source imagery retained privately for research; publicly distributed materials contain only attribution, view footprints and numeric observations.','provenance':'Esri World Imagery Wayback dates from the footprint source acquisition field, not its release serial.','releases':result}

if __name__=='__main__':
    folder=Path(sys.argv[1]);out=Path(sys.argv[2]);out.write_text(json.dumps(read(folder),indent=2)+'\n')
