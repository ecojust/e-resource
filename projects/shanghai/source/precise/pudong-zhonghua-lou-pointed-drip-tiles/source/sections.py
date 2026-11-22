from drip_eaves import *
def test(t,names,hit):
    out=[]
    def ray(o,d,w,label):
        a=hit(t,names,np.asarray(o),np.asarray(d))
        assert (a[0] if a else None) in w,(o,d,w,a)
        out.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    for c in CENTRES:
        for y in (-.19,.110,.325,.60):
            ray((c+.012,y,1.70),(0,0,-1),(TILE,),'Crown of each overlapped cap')
        for y in (-.254,-.011,.228,.470):
            ray((c-.003,y,1.70),(0,0,-1),(EDGE,),'Front raised rim of each convex tile')
        ray((c,-.80,.470),(0,1,0),(WOOD,),'Dark timber end below the ceramic')
    for a,b in zip(CENTRES,CENTRES[1:]):
        c=(a+b)/2
        for y in (-.235,.153,.410,.55):ray((c+.014,y,1.70),(0,0,-1),(TILE,),'Bottom of the rain channel')
        for x,z in ((0,.542),(.043,.555),(-.043,.555)):
            ray((c+x,-.83,z),(0,1,0),(LIP,),'Continuous face of the pointed drip')
    return out
