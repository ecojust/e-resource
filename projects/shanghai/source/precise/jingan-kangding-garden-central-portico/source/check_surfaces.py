"""Independent material/depth probes on the actual exported south garden elevation."""
from pathlib import Path
import runpy
import numpy as np

HERE = Path(__file__).resolve().parent

def check_triangles(triangles,materials,distant):
    hit=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit'];rows=[]
    def probe(name,x,z,expected,lo,hi):
        eye=np.array([x,-4.,z]);i,t,p=hit(triangles,eye,np.array([0.,1.,0.]))
        y=float(t)-4.;material=str(materials[i])if np.isfinite(t)else 'sky'
        assert material==expected and lo<=y<=hi,(name,x,z,material,expected,y,lo,hi)
        rows.append(dict(feature=name,x_m=round(x,4),z_m=z,material=material,actual_y_m=round(y,5),expected_y_m=[lo,hi]))
    stone='Ivory carved stone';glass='Dark grey glazing';sash='Oxide red timber'
    ends=(-7.95,-2.68,2.68,7.95)
    for x in ends[1:3]:
        for z in (.32,1.02,3.63,6.56,7.81,8.27,8.46,8.59):probe('Giant round shaft, capitals and square abaci',x,z,stone,-.52,-.29)
        for dx in (-.25,.25):probe('Curved cylindrical face',x+dx,3.32,stone,-.35,-.20)
    for x in (ends[0],ends[-1]):
        for z in (.6,4,6.8,8.38):probe('End pilaster',x,z,stone,-.255,-.20)
    for i,(a,c) in enumerate(zip(ends,ends[1:])):
        mid=(a+c)/2;left=a+.28;right=c-.28;spacing=(right-left)/19
        for k in (3,7,11,15):
            x=left+k*spacing
            probe('Turned baluster',x,5.82,stone,-.33,.10)
            ox=x+.5*spacing
            # Open balusters give a direct view of the recessed timber or glass reveal.
            eye=np.array([ox,-4.,5.82]);idx,dist,_=hit(triangles,eye,np.array([0.,1.,0.]));m=str(materials[idx]);assert m in (glass,sash) and 2.70<dist-4.<2.85
            rows.append(dict(feature='Unobstructed opening between two turned balusters',x_m=round(ox,4),z_m=5.82,material=m,actual_y_m=round(float(dist-4),4)))
        for z in (2.36,6.79):
            for dx in (-1.73,-.39,.54,1.66):probe('Timber gallery glazing behind the columns',mid+dx,z,glass,2.79,2.84)
        for z in (.8,3.70,6.12,7.84):probe('Timber vertical glazing bar in the deep gallery',mid,z,sash,2.71,2.75) if z!=6.12 else probe('Solid balcony coping',mid,6.23,stone,-.36,-.20)
        probe('Solid upper terrace masonry',mid+.10,10.12,'Warm white render',-.22,-.18)
        probe('Dentilled normal cornice band',mid,12.68,stone,-.51,-.46)
    for x in (-1.10,-.42,.42,1.10):probe('Gabled dormer timber-backed glazing',x,14.0,glass,1.85,1.91)
    probe('Centre dormer ornament',0.,15.91,sash,1.32,1.36)
    for x in (-5.8,-4.8,4.8,5.8):
        for z in (13.4,14.38,15.03):probe('Exposed pitched terracotta roof',x,z,'Terracotta roof tiles',.65,4.0)
    return dict(distant=distant,rays=rows)
