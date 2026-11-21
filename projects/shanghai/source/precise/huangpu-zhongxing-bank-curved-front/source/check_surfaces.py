"""Trace independent radial first contacts and check the two levels of spandrel relief."""
from pathlib import Path
from math import cos,sin
import runpy
import numpy as np

def check_triangles(triangles,materials,distant):
    project=Path(__file__).resolve().parents[4]
    shoot=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['first_hit']
    mat=np.asarray(materials);rows=[];radius=9.733486353059083
    def cast(why,arc,z,name,depth,tolerance=.046):
        angle=arc/radius
        outward=np.array((sin(angle),-cos(angle),0.))
        face=np.array((radius*sin(angle),radius*(1-cos(angle)),z))
        orig=face+2.5*outward
        index,dist,hit=shoot(triangles,orig,-outward)
        assert np.isfinite(dist) and mat[index]==name and abs(dist-(2.5-depth))<=tolerance,(why,arc,z,distant,str(mat[index]) if np.isfinite(dist) else 'miss',dist,depth)
        rows.append(dict(feature=why,arc_m=round(arc,4),z_m=z,expected_depth_m=depth,first_surface=str(mat[index]),range_m=round(float(dist),5)))
    for axis in [-4.34890665,0.,4.34890665]:
        cast('ground glass',axis+.39,1.95,'grey blue glazing',-.33)
        cast('ground grille',axis,1.95,'dark metal sash',-.175)
        cast('ground plinth',axis+.45,.09,'weathered pale moulding',.085)
        cast('granular base at pier',axis+1.50,1.12,'warm ground stone',0)
        cast('continuous waist cornice',axis+.36,4.41,'weathered pale moulding',.32)
        for z in (4.67,8.13,11.59,15.05):
            for off in (-.68,.68):
                cast('paired upper clear pane',axis+off+.12,z+.83,'grey blue glazing',-.33)
                cast('paired upper transom',axis+off+.20,z+1.94*.71,'dark metal sash',-.17)
            cast('stone centre pier',axis,z+1.07,'cream jointed facing',0)
            cast('projecting sill',axis+.59,z-.046,'weathered pale moulding',.078)
            if z>5:
                cast('recessed rectangular panel',axis+.51,z-.67,'pale recessed panels',-.105)
                cast('spandrel lip',axis+.23,z-.33,'weathered pale moulding',.084)
        for dx in (-1.60,1.60):
            for delta in (-.074,.074):
                cast('individual bracket toe',axis+dx+delta,18.20,'weathered pale moulding',.44)
                cast('individual bracket foot',axis+dx+delta,17.76,'weathered pale moulding',.115)
            cast('gap between bracket pair',axis+dx,17.75,'cream jointed facing',0)
        for z,dep in ((18.22,.12),(18.34,.24),(18.46,.47),(18.60,.62),(18.70,.52)):
            cast('stepped eave profile',axis+.6,z,'weathered pale moulding',dep)
        for off in (-.59,.59):
            cast('upper band paired pane',axis+off+.09,19.84,'grey blue glazing',-.33)
        cast('curved parapet',axis+.72,21.59,'weathered pale moulding',.10)
    return {'rays':rows,'triangles':len(triangles),'passes':len(rows)}
