"""Regression check: blender --background --threads 1 --python check_box_winding.py."""
import sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_utils import Builder

for name,basis in [('identity',None),('mirrored facade',[(1,0,0),(0,-1,0),(0,0,1)]),
                   ('rotated mirrored facade',[(.6,.8,0),(.8,-.6,0),(0,0,1)])]:
    basis=[Vector(axis) for axis in basis] if basis else None
    center=Vector((5,7,11));builder=Builder();builder.box(center,(2,3,4),0,basis)
    assert len(builder.vertices)==8 and len(builder.faces)==6
    for face in builder.faces:
        a,b,c,*_=map(lambda i:Vector(builder.vertices[i]),face)
        midpoint=sum((Vector(builder.vertices[i]) for i in face),Vector())/len(face)
        assert (b-a).cross(c-a).dot(midpoint-center)>0, name
    print('PASS:',name,'has six outward faces')
