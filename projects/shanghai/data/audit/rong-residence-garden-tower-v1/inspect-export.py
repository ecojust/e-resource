"""Render the Rong residence garden tower and the first veranda bay from their decoded web geometry."""
import argparse,json,runpy
from pathlib import Path

HERE=Path(__file__).resolve().parent
RENDERER=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded',type=Path)
    parser.add_argument('out',type=Path)
    options=parser.parse_args()
    cameras=json.loads((HERE/'inspection-cameras.json').read_bytes())
    views=[(row['name'],row['eye'],row['target'],row['width_m']) for row in cameras]
    runpy.run_path(RENDERER)['render'](options.decoded,options.out,views,830,670)
