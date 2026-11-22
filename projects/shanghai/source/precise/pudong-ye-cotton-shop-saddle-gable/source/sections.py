from saddle_wall import *
def test(t,names,hit):
    out=[]
    def get(o,d,valid,meaning):
        a=hit(t,names,np.asarray(o),np.asarray(d));assert (a[0] if a else None) in valid,(o,meaning,valid,a)
        out.append(dict(label=meaning,material=a[0] if a else None,point=a[1] if a else None))
    for x in np.linspace(-1.11,.61,29):
        x=float(x)
        for z in (.20,.39):
            get((x,-.67,z),(0,1,0),(PLASTER,),'Whitewashed gable body')
        get((x,-.68,top(x)+.077),(0,1,0),(None,),'Clear daylight above the saddle')
        get((x,.061,2.22),(0,0,-1),(CAP,NOSE),'Arc of the cap tile against the sky')
    for y in (-.095,.0,.094):
        for z in (.992,1.083,1.130):get((1.45,y,z),(-1,0,0),(STONE,),'Exposed end of the stepped bands')
    return out
