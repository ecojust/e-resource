"""Register the 1948 1C sheet to stable public crossroads, then check the bank corner independently."""
from pathlib import Path
import json
import numpy as np
import xml.etree.ElementTree as ET
import argparse, hashlib
p=argparse.ArgumentParser();p.add_argument('--osm',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=ET.parse(a.osm).getroot()
nodes={n.attrib['id']:[float(n.attrib['lon']),float(n.attrib['lat'])] for n in root.iter('node')}
# Measured on a screen rendering of native pixels [3200,6200]..[5800,10300], scaled to height 850.
# Intersections in the 1948 mosaic feature local perspective and seams.
controls=[('103795804','Beijing–Sichuan',111,374),('103831022','Beijing–Huqiu',161,373),
          ('1883276500','Beijing–Yuanmingyuan',220,374),('103781336','Dianchi–Sichuan',152,462),
          ('103781535','Nanjing–Sichuan',188,540),('267195118','Jiujiang–Sichuan',222,620),
          ('103788043','Hankou–Sichuan',246,683),('267195119','Jiujiang–Jiangxi',115,655),
          ('11152438014','Hankou–Jiangxi',127,712)]
pts=np.array([nodes[q[0]] for q in controls]);origin=np.array([121.484306318694,31.237170360402505])
scale=np.array([111320*np.cos(np.radians(origin[1])),110860.])
def xy(gps):return np.r_[(gps-origin)*scale,1.]
A=np.array([xy(v)for v in pts]);raw=np.array([i[-2:]for i in controls]);m=np.linalg.lstsq(A,raw,rcond=None)[0];residual=np.linalg.norm(A@m-raw,axis=1)
def native(pt):return (np.asarray(pt)+.5)*(4100/850)-.5+np.array([3200.,6200.])
sichuan=xy(np.array(nodes['103788196']))@m
parcel=xy(origin)@m
val={'historical_source_sha256':'83fc6bb650464734c968bd0fda658b3587b753986c75b9620336796832fee66a',
'current_roads_source_url':'https://api.openstreetmap.org/api/0.6/map?bbox=121.48,31.233,121.49,31.248','current_roads_sha256':hashlib.sha256(a.osm.read_bytes()).hexdigest(),
'gis_license':'© OpenStreetMap contributors, ODbL 1.0','controls':[{'name':i[1],'osm_node':i[0],'lon_lat':list(pt),'1948_native_pixel':native(uv).tolist(),'residual_source_px':float(re*4100/850)}for i,pt,uv,re in zip(controls,pts,raw,residual)],
'max_residual_source_px':float(residual.max()*4100/850),'rms_source_px':float(np.sqrt(np.mean(residual**2))*4100/850),
'held_out_intersection':{'osm_node':'103788196','name':'Fuzhou Road / Sichuan Middle Road','source_prediction_native_xy':native(sichuan).tolist(),'source_observation_native_xy':[4545,9984],'separation_source_px':float(np.linalg.norm(native(sichuan)-[4545,9984]))},
'registered_modern_arc_midpoint':{'lon_lat':origin.tolist(),'1948_predicted_native_xy':native(parcel).tolist()},'original_image_size':[14783,10446], '1948_original_frontage_outline_control_pixels': [[4333,10033],[4500,10008],[4516,10014],[4530,10030],[4570,10161]], 'reading':'The north and east roof edges run respectively along Fuzhou and Sichuan roads and meet at a short rounded corner. The two approximate endpoints and three corner points were read independently on a full-resolution 900 by 750 crop beginning at source [4140,9690]. These roof-edge points are not facade ground survey points.',
'explanation':'Matches the street block at the southwest side of the intersection. The registration is an approximate local affine fit to a photo mosaic. It supplies historical plan context and cannot resolve storefront lettering, glazing or entrance details.'}
a.output.write_text(json.dumps(val,ensure_ascii=False,indent=2)+'\n');print(residual,sichuan,parcel)
