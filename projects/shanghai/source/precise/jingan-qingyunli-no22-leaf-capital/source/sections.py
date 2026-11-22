"""Verify the mouldings, front and side ornament, shaft recess and convex boss in both exports."""
from gate_capital import *
def test(tri,materials,hit):
    rows=[]
    def at(x,z,mat,name):
        row=hit(tri,materials,np.array([x,-1.25,z]),np.array([0.,1.,0.]))
        assert row and row[0]==mat,(name,x,z,mat,row)
        rows.append(dict(material=mat,label=name,point=row[1]));return -row[1][1]
    for x in (-.278,-.17,-.076,0,.064,.175,.298):
        for z in (.17,.32,.492,.624,.751,.886):
            d=at(x,z,STONE,'Stone shaft and inset long panel')
            assert abs(d-(.178 if abs(x)<.116 and z<.679 else .214))<.001
    for z,mat in ((.955,BED),(.992,TRIM),(1.027,TRIM),(1.436,TRIM),(2.228,TRIM),(2.26,TRIM),(2.355,SOFFIT),(2.467,TRIM)):
        for x in (-.3,-.192,-.08,.08,.192,.30):at(x,z,mat,'Stepped capital and cornice mouldings')
    for x in (-.139,-.078,0,.081,.145):
        for off in (-.081,0,.086):at(x,1.823+off,DISC,'Convex circular stone ornament')
    assert at(0,1.824,DISC,'Crown of convex disk')>at(.194,1.824,DISC,'Edge of convex disk')+.029
    for x in (-.265,-.004,.258):
        for dz in (.055,.084,.116):at(x,1.048+dz,RIB,'Three separate plant stems')
    for x in (-.3,.305):
        for z in (1.55,1.725,1.887,2.08):at(x,z,STONE,'Flat stone bordering the disk')
    return rows
