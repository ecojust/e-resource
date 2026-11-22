from tower import *
def test(t,names,hit):
    out=[]
    for f,l,r,c in FACES:
        def ray(u,z,m,label):
            p=np.array(f(u,z,0.));n=np.array(f(u,z,1.))-p
            res=hit(t,names,p+n*1.7,-n)
            if m:assert res and res[0] in m,(u,z,label,res,m)
            else:assert res is None,(u,z,label,res)
            out.append(dict(label=label,material=res[0]if res else None,point=res[1]if res else None))
            return np.dot(np.array(res[1])-p,n)if res else None
        for dx in (-.31,-.044,.27):
            for z in (2.52,2.66,2.98,3.18,3.39,3.545):
                assert abs(ray(c+dx,z,[GLASS,SKY],'Narrow steel lights')+.159)<.0002
        for dx in (-.13,.13):
            for z in (2.63,2.99,3.57,3.84,4.03):assert abs(ray(c+dx,z,[JOIN],'Continuous shaft of mullion')+.096)<.0002
        for z in (2.73,3.08,3.48):
            for side in (-1,1):assert abs(ray(c+side*.56,z,[FACING],'Retained jamb face'))<.0002
        for z in (4.41,4.68,4.95,5.24,5.39):
            for dx in (-.11,0.,.11):assert abs(ray(c+dx,z,[ACCENT],'Tapered pale wedge')-.038)<.0002
        for z in (1.65,1.85,2.079,2.20):
            for dx in (-.22,.22):assert abs(ray(c+dx,z,[ACCENT],'Striped spandrel')-.0125)<.0002
        for x in np.linspace(c-.48,c+.48,7):
            assert abs(ray(x,2.327,[EDGING],'Window sill')-.164)<.0003
        for dx in (-.34,.21):
            for z in (.355,.687,1.179):assert abs(ray(c+dx,z,[SKY,GLASS],'Lower window glazing')+.145)<.0003
        if f is FACE:
            for x,h in [(-1.03,5.68),(-.72,5.86),(-.37,6.08),(.011,6.36),(.4,6.07),(.68,5.86),(1.01,5.67)]:
                ray(x,h+.025,[],'Sky over stepped crown');ray(x,h-.025,[FACING],'Stepped profile')
    return out
