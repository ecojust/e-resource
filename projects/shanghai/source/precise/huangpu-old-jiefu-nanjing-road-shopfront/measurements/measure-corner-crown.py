"""Measure the stepped roof, long brick returns and recessed teeth in the upright street exposure."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import gaussian_filter,gaussian_filter1d,map_coordinates,median_filter

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from crown_plane import VERTICAL_VP,at_row,on_wall

# The skyline jumps abruptly at the paired shoulders. The endpoints are marked
# either side of each jump to measure each separate brick parapet at its real height.
ROOF=[(1048,1300),(1302,1390),(1395,1477),(1480,1572),(1576,1602),(1605,1697),
      (1700,1725),(1727,1818),(1821,1905),(1909,1986),(1989,2223)]
# Positions are read at v=930. Each dark return has two visible parallel edges.
# A third point marks the end of the lit brick face. Projections are estimated in metres.
RIBS=[(1034,1046,1071,.12),(1087,1098,1113,.102),(1114,1123,1147,.14),
      (1150,1157,1174,.10),(1181,1188,1197,.11),(1198,1208,1236,.14),
      (1238,1249,1270,.115),(1300,1315,1350,.16),(1352,1365,1441,.215),
      (1482,1506,1533,.175),(1552,1559,1577,.10),(1580,1589,1699,.21),
      (1752,1762,1785,.107),(1830,1852,1937,.218),(1989,1996,2004,.10),
      (2006,2013,2044,.155),(2080,2089,2102,.113),(2102,2109,2130,.13),
      (2165,2175,2190,.10),(2191,2203,2230,.12)]
# Two central bands have particularly clear dark slots. Flank controls retain
# the separately visible open pockets in each run, omitting unresolvable shadows.
BANDS=[(1117,1295,782,650,[1129,1139,1153,1164,1200,1214,1230,1258,1269]),
       (1303,1387,606,566,[1309,1320,1336,1359,1373]),
       (1471,1567,611,600,[1478,1496,1515,1535,1554]),
       (1726,1826,600,611,[1737,1756,1774,1794,1812]),
       (1909,1986,565,604,[1911,1927,1944,1960,1976]),
       (1996,2175,660,786,[2012,2023,2032,2052,2066,2077,2116,2126,2136,2146,2157,2167])]
# At these oblique side openings the brick stops above the screen's nominal
# upper level. This leaves actual space for the stone overlights and steel windows.
WINDOW_HEADS=[(1071,1121,1027,999),(1158,1200,1004,980),(1248,1304,998,965),
              (2015,2074,960,987),(2109,2166,984,1015),(2187,2216,1021,1041)]


def rectangular_recess(lum,xs,ys,indices,band):
    u=xs;v=ys;off=np.arange(-18,30,dtype=float)
    strip=map_coordinates(lum,[v[None,:]+off[:,None]-230,np.broadcast_to(u,(len(off),len(u)))],order=1)
    grad=np.gradient(strip,axis=0)
    limits=[(-15,3),(-8,7),(-4,9),(-4,11),(0,19),(-13,14)][band]
    allowed=(off>=limits[0])&(off<=limits[1])
    top=gaussian_filter1d(median_filter(off[allowed][np.argmin(grad[allowed],axis=0)],size=9),4.5)
    lip=v+top
    raw=np.array([map_coordinates(lum,[lip+d-230,u],order=1)for d in np.arange(5,17)])
    tone=np.median(raw,axis=0);contrast=tone-gaussian_filter1d(tone,5.5)
    results=[]
    for seed in indices:
        nearby=np.flatnonzero(abs(u-seed)<=2.)
        j=nearby[np.argmin(contrast[nearby]+.65*(u[nearby]-seed)**2)]
        centre_u=u[j];cy=lip[j]+10
        limit=min(-2.,float(contrast[j])*.44);left=right=j
        while left>0 and j-left<6 and contrast[left-1]<limit:left-=1
        while right<len(u)-1 and right-j<6 and contrast[right+1]<limit:right+=1
        lo=np.clip(u[left]-.55,centre_u-4.75,centre_u-1.0)
        hi=np.clip(u[right]+.55,centre_u+1.0,centre_u+4.75)
        results.append(dict(centre_px=[float(centre_u),round(float(cy),2)],left_right_u_px=[float(lo),float(hi)],
                            local_luminance_residual=round(float(contrast[j]),2)))
    control=[[round(float(u[i]),2),round(float(lip[i]),2)]for i in list(range(0,len(u)-1,5))+[len(u)-1]]
    return dict(lip_polyline_px=control,slots=results)


def run(original):
    refs=json.loads((HERE/'corner-crown-image-controls.json').read_bytes())
    credit=refs['photo_references']['cc2024a']
    if hashlib.sha256(original.read_bytes()).hexdigest()!=credit['sha256']:raise ValueError('Unexpected 2024 street exposure')
    with Image.open(original)as source:img=np.asarray(ImageOps.exif_transpose(source).convert('RGB'),dtype=np.uint8)
    # Work only within the upper exposed part of the facade.
    a=gaussian_filter(img[230:1240,1000:2270].astype(float),(1.15,1.15,0))
    warm=(a[:,:,0]-a[:,:,2]>3.)&(a.mean(axis=2)<210.)
    edge=median_filter(np.argmax(warm,axis=0)+230,size=5)
    diff=np.linalg.norm(a[4:]-a[:-4],axis=2)
    samples=[]
    for left,right in ROOF:
        field=[]
        for u in list(range(left,right,3))+[right]:
            guess=int(edge[u-1000]);vs=np.arange(guess-12,guess+3)
            scores=diff[np.clip(vs-232,0,len(diff)-1),u-1000]-.08*(vs-guess)**2
            v=vs[scores.argmax()]
            field.append([u,int(v)])
        samples.append(field)
    ribs=[]
    for a0,peak,end,depth in RIBS:
        ribs.append(dict(dark_return_px=[a0,peak],lit_edge_u_px=end,estimated_projection_m=depth))
    lum=gaussian_filter((img[230:1250]@np.array([.2126,.7152,.0722])),.7)
    bands=[rectangular_recess(lum,np.arange(a,b+1.),np.linspace(v0,v1,b-a+1),seeds,i)
           for i,(a,b,v0,v1,seeds)in enumerate(BANDS)]
    return dict(photo=credit,coordinate_note='All original source pixels refer to the upright portrait. Street distances use the shared 822 tangent curve and the two straight returns.',
                roof_sections_px=samples,ribs_at_row_930=ribs,dentil_bands=bands,
                side_opening_upper_corners_px=[[a,v0,b,v1]for a,b,v0,v1 in WINDOW_HEADS],
                underside_elevation_m=23.30,
                interpretation='The upper surface is stepped brick with thin coping. Horizontal slots in the stone bands are modelled as recesses. Sun direction, brick colours, the covered central field and true return depths are approximate. The two changed retailer signs and the taller rear volume are outside this model.')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('--output',type=Path,default=HERE/'corner-crown-features.json');a=ap.parse_args()
    r=run(a.photo);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    print(len(r['roof_sections_px']),[len(s['slots'])for s in r['dentil_bands']])
