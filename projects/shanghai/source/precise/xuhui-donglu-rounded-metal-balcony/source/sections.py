from curved_balcony import *
def test(tri,names,hit):
    rows=[]
    def ray(x,y,z,vec,mat,label):
        r=hit(tri,names,np.array([x,y,z]),np.array(vec,dtype=float));assert r and r[0]==mat,(x,y,z,mat,r)
        rows.append(dict(label=label,material=mat,point=r[1]))
    for x in np.linspace(-.88,.88,13):
        for z,mat in [(.589,CONCRETE),(.812,BAND),(.961,BAND),(1.018,RAIL),(1.166,RAIL),(1.323,RAIL),(1.482,RAIL)]:
            ray(x,-1.32,z,[0,1,0],mat,'Front face of the projecting slab, solid band or open horizontal rail')
    for x in [-.78,-.34,.29,.80]:
        for z in [1.10,1.246,1.412,1.67,2.18,2.45]:ray(x,-1.32,z,[0,1,0],GLASS,'Light through the opening onto recessed glazing')
    for z in [.15,.32,.77,1.37,1.68,2.18,2.60,2.75]:
        for x in [-1.5,1.5]:ray(x,-1.32,z,[0,1,0],BRICK,'Stack-bonded facing tile')
    for sign in [-1.,1.]:
        for y in [-.19,-.31,-.48]:
            for z,mat in [(.57,CONCRETE),(.824,BAND),(1.166,RAIL),(1.482,RAIL)]:ray(1.62*sign,y,z,[-sign,0,0],mat,'Return alongside the recess')
    return rows
