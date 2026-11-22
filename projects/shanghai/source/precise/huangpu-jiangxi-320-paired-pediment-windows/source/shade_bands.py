"""Measured blue and ochre bands on four individual side drops of the 2015 awnings."""
from pathlib import Path
import json
import numpy as np

TABLE=json.loads((Path(__file__).absolute().parents[1]/'measurements/curtain-band-heights.json').read_bytes())

def band_count(name,side):
    return 1+len(TABLE[name+'/'+str(side)]['edge_v'])

def band_interval(name,side,i,u):
    """Return normalized top, bottom and whether the stripe is blue at this cloth width."""
    row=TABLE[name+'/'+str(side)]; edges=row['edge_v']; across=row['across']
    top=float(np.interp(u,across,edges[i-1])) if i else 0.
    bottom=float(np.interp(u,across,edges[i])) if i<len(edges) else 1.
    return top,bottom,(i%2==0)==row['first_blue']
