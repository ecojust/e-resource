from portal_and_aggregate import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,mat,label):
        r=hit(tri,names,np.array([x,-.61,z]),np.array([0,1,0.]));assert r and r[0]==mat,(x,z,mat,r);rows.append(dict(label=label,material=mat,point=r[1]))
    for x in [-.710,-.380]:
        for dx in [-.026,0,.026]:
            for dz in [-.023,0,.023]:check(x+dx,.688+dz,BOSS,'Circular boss on the flat frieze')
    for x in [-.781,-.51,-.18,.029,.112]:
        for z in [.932,.954,.976,1.006,1.028,1.052,1.228,1.281,1.317,1.382]:check(x,z,PROFILE,'Section through profiled cornice')
    for x in [-.22,-.10,.067,.127]:
        for z in [.089,.21,.45,.68,.79]:check(x,z,STONE,'Quoined side of the doorway')
    for row,col,x,z,rx,rz,height,j in relief_grains():
        if row%7 or col%3 or (row+3*col)%3 or x<.35:continue
        check(x,z,GRAINS[j],'Raised coloured stone grain')
    return rows
