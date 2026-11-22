from red_casements import *
def test(t,names,hit):
    out=[]
    def r(origin,d,expected,label):
        ans=hit(t,names,np.array(origin),np.array(d));assert (ans[0] if ans else None)==expected,(origin,d,expected,ans)
        out.append(dict(label=label,material=ans[0] if ans else None,point=ans[1] if ans else None))
    for leaf in (0,1):
        hx,side,ang=HINGES[leaf];d=(-side*math.sin(ang),math.cos(ang),0.)
        for z in (.55,.98,1.50,1.69):
            for s in (.11,.21,.343,.42):r(leaf_point(leaf,s,-.041,z),d,GLASS,'Glazing in each differently posed sash')
            for s in (.027,.513):r(leaf_point(leaf,s,-.041,z),d,PAINT,'Red outer and meeting stiles')
        for i in (1,2):
            z=ZB+.066+(ZT-ZB-.136)*i/3
            for s in (.13,.29,.412):r(leaf_point(leaf,s,-.041,z),d,PAINT,'Red horizontal glazing bar')
    for x in (-.242,-.086):
        for z in (.53,.79,1.28,1.55):r((x,-.75,z),(0,1,0),IRON,'Fixed rod visible behind open leaf')
    for x in (-.19,-.043):
        for z in (.68,.91,1.33):r((x,-.75,z),(0,1,0),DARK,'Interior visible between rods')
    for x in (-.614,.613):
        for z in (.45,.75,1.13,1.56,1.71):r((x,-.73,z),(0,1,0),STONE,'Green-grey side of the reveal')
    for x in (-.51,-.174,.185,.515):
        for z in (2.073,2.13,2.19):r((x,-.73,z),(0,1,0),MOULD,'Layer of the projecting hood')
    return out
