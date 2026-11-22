from oriel_sashes import *
def test(t,names,hit):
    result=[]
    for i in range(4):
        cx,cy,ux,uy,a=frame(i)
        def probe(s,z,want,meaning):
            o=point(i,s,.50,z);ans=hit(t,names,np.array(o),np.array([-uy,ux,0.]))
            assert (ans[0] if ans else None)==want,(i,s,z,want,ans)
            result.append(dict(label=meaning,material=ans[0] if ans else None,point=ans[1] if ans else None))
        for side in (0,1):
            s=(side-.5)*a/2
            v0=LOW+.053;v1=HIGH-.053;step=(v1-v0)/4
            for j in range(4):
                for u in (-.071,.073):probe(s+u,v0+(j+.5)*step,GLASS,'Glass in each of the 32 panes')
            for j in (1,2,3):probe(s+.051,v0+j*step,PAINT,'Three glazing bars in each tall sash')
            for z in (.30,.55):probe(s+.077,z,BOARD,'Weathered timber boarding below the window')
            for z,m in ((.714,EDGE),(2.041,PAINT),(2.13,CORNICE)):probe(s+.087,z,m,'Sill, head and grey top')
        for s in (-a*.5+.023,a*.5-.023):
            for z in (.89,1.79):probe(s,z,HINGE,'Exposed hinge on outer edge of a sash')
    return result
