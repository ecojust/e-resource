"""Measure the chamfer and the repeating arch hoods in the delivered triangles."""
from math import cos, sin, pi
import numpy as np
from corner import *

def test(mesh,names,hit):
    rows=[]
    def ray(origin,direction,material,note):
        result=hit(mesh,names,np.array(origin),np.array(direction))
        assert result and result[0] in material,(note,origin,direction,result)
        rows.append(dict(label=note,material=result[0],point=result[1]))
        return np.array(result[1])
    for base in LEVELS:
        for x in (-1.18,-1.06,-.94,.94,1.06,1.18):
            for height in (.20,.58,.97,1.28,1.77,2.15):
                p=ray((x,-3.,base+height),(0.,1.,0.),[BRICK],'Projecting brick pilaster')
                assert abs(p[1]+.072)<.001
        for r in (-.42,-.18,.18,.42):
            for z,mat in [(.67,PANE),(1.09,PANE),(1.43,SKY),(1.67,SKY)]:
                p=ray((r,-3.,base+z),(0.,1.,0.),[mat],'Glazing behind the red masonry reveal')
                assert abs(p[1]-.121)<.001
        for x in (-.541,0.,.541):
            p=ray((x,-3.,base+.77),(0.,1.,0.),[WINDOW],'Window frame')
            assert p[1]<.08
        for x in (-.56,-.25,.16,.52):ray((x,-3.,base+.432),(0.,1.,0.),[EDGE],'Projected sill above brick apron')
        for ang in (pi*.13,pi*.30,pi*.44,pi*.61,pi*.79,pi*.91):
            for elev in (.19,.39,.61):
                x=.67*cos(ang)*cos(elev)
                y=-.018-.59*sin(ang)*cos(elev)
                p=ray((x,y,base+2.59),(0.,0.,-1.),[CLOTH,SEAM],'Three-dimensional awning surface')
                assert abs(p[2]-(base+1.93+.39*sin(elev)))<.057
        for x in (-.44,-.18,.23,.47):
            p=ray((x,-3.,base+1.907),(0.,1.,0.),[HEM],'Scalloped awning valance')
            assert p[1]<-.35
        for x in (-.87,-.35,0.,.43,.82):
            p=ray((x,-3.,base+.026),(0.,1.,0.),[EDGE],'Stone lip along chamfer')
            assert abs(p[1]+.147)<.002
        for mapper,u in [(LEFT,-.54),(RIGHT,.54)]:
            for z in (.531,1.053,1.678,2.313):
                target=np.array(mapper(u,base+z,0.))
                normal=np.array(mapper(u,base+z,1.))-target
                p=ray(target+normal*2.,-normal,[BRICK,DARK],'Returns bend away from the corner')
                assert np.linalg.norm(p-target)<.02
    for x in [-.87,-.62,-.32,0.,.33,.62,.87]:
        p=ray((x,-3.,8.152),(0.,1.,0.),[STONE],'Shoulders and central gable')
        assert p[1]<0
    return rows
