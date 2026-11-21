"""Intersect the delivered triangles with rays from the street, including open spaces between the rails."""
from pathlib import Path
import runpy
import numpy as np

HERE=Path(__file__).resolve().parent
def check_triangles(triangles,materials,distant):
    hit=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    rows=[]
    def probe(name,x,z,mat,depth,tol=.012):
        x=x*.96+.18;eye=np.array([x,-2.50,z])
        i,dist,pos=hit(triangles,eye,np.array([0.,1.,0.]))
        actual=materials[i]if np.isfinite(dist)else 'sky';found=2.50-dist
        assert actual==mat and abs(found-depth)<tol,(name,x,z,actual,mat,found,depth)
        rows.append(dict(feature=name,x_m=x,z_m=z,material=str(actual),projection_m=round(found,5),point=np.asarray(pos).tolist()))
    central=(-4.8,-2.9,-1.,.90,2.8,4.7)
    ends=(-6.8,6.8);glass='recessed grey green glass';sash='dark bronze sash';tile='red glazed tile bands';metal='oxidized railing';stone='pale carved relief';wall='warm ivory render'
    for x in (*central,*ends):
        for row,z in enumerate((5.17,8.20,11.02,14.03)):
            depth=-.22 if row==1 else -.18
            probe('Glazing in each of four occupied floors',x+.18,z,glass,depth)
            probe('Vertical sash in each opening',x,z,sash,depth+.07)
    for index,x in enumerate(central):
        door=index in (1,4)
        probe('Two returning entrances and four flanking display windows',x+.255,1.68,glass,-.50 if door else -.185)
        if door:probe('Centre door stile behind the pavement',x,1.68,sash,-.45)
        for z in (6.45,9.61,12.22):probe('Actual rectangular red tile bands',x,z,tile,.037)
    for x in ends:
        for z in (3.81,10.77):
            probe('Solid projecting end-balcony front',x+.22,z,wall,.69)
        probe('Tiled side apron',x,9.54,tile,.036)
    for x in central:
        for z in (7.14,7.37,7.58,7.79):
            probe('Four forward metal tubes',x+.18,z,metal,.95+.026 if z!=7.79 else .985,.014)
        probe('Open space between long rails',x-.18,7.25,glass,-.22)
        probe('Slab nose in front of lower window band',x+.21,6.90,stone,1.065)
    for x in (-3.72,.15,3.99):
        for z in (12.81,13.12,13.43):probe('Vertical red tile key',x,z,tile,.066)
    for x in (-7.30,-5.75,-3.58,-.10,3.88,6.90):
        probe('Raised parapet key',x+.040,15.90,wall,.004)
    for side in (-1,1):
        a,c=(-5.57,-.25)if side<0 else(.25,5.57);step=(c-a)/7
        for i in range(7):
            x=a+(i+.5)*step
            probe('Raised diamond in street-level frieze',x,4.0,stone,.16)
    return dict(passes=len(rows),lod=bool(distant),triangles=len(triangles),rays=rows)
