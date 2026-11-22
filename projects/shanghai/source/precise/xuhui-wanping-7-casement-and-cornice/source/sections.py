from upper_window import *

def test(tri,names,hit):
    result=[]
    def check(x,z,material,label):
        r=hit(tri,names,np.array([x,-.80,z]),np.array([0,1.,0]))
        assert r and r[0]==material,(x,z,material,r)
        result.append(dict(label=label,material=material,point=r[1]))
    for x in CENTRES:
        for xx in [-.104,.108]:
            for z in [.703,1.029,1.427,1.702,1.901]:
                check(x+xx,z,GLASS,'Individual panes in five rows')
        for z in [.702,1.030,1.423,1.695,1.906]:
            check(x,z,BAR,'Continuous vertical glazing bar')
        for z in [.872,1.225,1.797]:
            check(x+.087,z,BAR,'Transverse bar')
        check(x,1.599,STEEL,'Deep fixed transom')
    for side in [-1,1]:
        for j in range(8):check(side*1.34,.11+j*.274,STONE,'Banded pilaster stone')
        for j in range(1,8):check(side*1.34,j*.274,BED,'Recess of a pilaster joint')
        check(side*.738,1.06,STONE,'Thin stone surround')
        check(side*.669,.485,DRIP,'Sill')
        for xx in [.87,1.02,1.12]:
            for z in [.34,1.38,1.81]:check(xx*side,z,RENDER,'Independent ochre wall sample')
    for i in range(19):check((i-9)*.158,2.343,DENTIL,'Front of projecting dentil')
    return result
