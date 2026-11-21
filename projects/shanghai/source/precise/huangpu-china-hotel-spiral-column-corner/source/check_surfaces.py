"""Compare depths and materials of the two spiral columns, recessed doorway and both wing facades."""
import json
from pathlib import Path
from math import cos,pi
import numpy as np
import runpy

HERE=Path(__file__).resolve().parent
REG=json.loads((HERE/'frontage-registration.json').read_bytes())
HALF=REG['front_width_m']/2

def basis(side):
    if side=='corner':return np.array([0.,0.]),np.array([1.,0.])
    x,y=REG['wing_tangents'][side]
    if side=='left':return np.array([-HALF,0.]),np.array([-x,-y])
    return np.array([HALF,0.]),np.array([x,y])

def check_triangles(triangles,materials,distant):
    helper=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    rows=[]
    def probe(side,feature,s,z,mat,depth,tol=.032):
        anchor,along=basis(side);normal=np.array([along[1],-along[0]])
        eye=np.r_[anchor+s*along+2.8*normal,z];direction=np.r_[-normal,0.]
        k,dist,pos=helper['first_hit'](triangles,eye,direction)
        material=materials[k]if np.isfinite(dist)else 'sky'
        found=2.8-dist
        assert material==mat and abs(found-depth)<tol,(side,feature,s,z,mat,material,depth,found)
        rows.append(dict(side=side,feature=feature,x_along=s,z_m=z,material=str(material),projection_m=round(found,5),point=np.asarray(pos).tolist()))
    pale='pale limestone carving';glass='smoky blue window glass';metal='dark bronze frames';brick='interwoven warm facing brick';red='red entrance surround'
    for s in (-.57,-.21,.21,.57):
        probe('corner','Door glazing behind return',s,1.47,glass,-.75)
        probe('corner','Red square lintel',s,3.20,red,.18)
    for s in (-.95,.95):probe('corner','Red entry jamb',s,1.73,red,.112)
    for s in (-1.73,1.73):
        for i in range(32):
            z=5.78+i*.309
            r=.174+.032*cos(5*(-pi/2)-2*pi*(z-5.60)/.765)
            probe('corner','Profile of helical limestone column',s,z,pale,.105+r,.022)
        probe('corner','Circular column base',s,5.48,pale,.347,.012)
        probe('corner','Shaft capital rim',s,15.93,pale,.374,.01)
    for name,z,depth in [('Lower corner sash',7.22,-.33),('Second corner sash',10.83,.08),('Arched corner sash',14.15,.04)]:
        for s in (-.29,.29):probe('corner',name,s,z,glass,depth)
    for z,depth in [(8.22,.08),(9.25,.26),(12.23,.23)]:
        probe('corner','Projecting stone panel',.32,z,pale,depth)
    for side in ('left','right'):
        sign=-1 if side=='left' else 1;x=1.86*sign
        probe(side,'Street arch glazing',x+.27,2.23,glass,-.36)
        probe(side,'Crown keystone',x,4.37,pale,.24)
        probe(side,'First arch stone edge',x+1.13,2.17,pale,.13)
        probe(side,'First brick pier',x+1.52,2.27,brick,0)
        for j in (-.55,.55):
            xx=x+j
            for name,z,depth in [('Lower wing window',7.28,-.22),('Middle wing pair',10.93,-.12),('Top arched pair',13.88,-.16)]:
                probe(side,name,xx+.13,z,glass,depth)
        for z,d in ((9.05,.48),(9.78,.35),(12.1,.20),(12.89,.12)):
            probe(side,'Projecting stone bay and apron',x+.16,z,pale,d)
        for z,d in ((5.065,.24),(5.50,.21),(16.09,.22),(16.39,.38),(16.57,.51),(17.22,.19)):
            probe(side,'Cornice and carved string course',x+.17,z,pale,d)
        for z in [7.55,10.57,13.21,15.04]:probe(side,'Buff diamond brickwork',((.38 if side=='right' else -3.72+.38)+.297),z,'buff diaper brick',.022)
    for s in (-2.14,2.14):
        for z in (6.21,8.23,12.11,15.11):probe('corner','Facing bricks beside columns',s,z,brick,0)
    return dict(passes=len(rows),rays=rows,triangles=len(triangles),lod=bool(distant))
