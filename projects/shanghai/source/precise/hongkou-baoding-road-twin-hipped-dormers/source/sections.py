from twin_hipped_dormers import *
def test(t,m,hit):
    reads=[]
    def ask(o,d,target,label):
        r=hit(t,m,np.array(o,float),np.array(d,float));assert r and r[0] in target,(label,o,r)
        reads.append(dict(label=label,material=r[0],point=r[1]))
    for c in CENTRES:
        for ds in(-.084,-.052,0,.046,.093):
            for y in(-.323,-.205,-.095,.055):
                ask([c+ds,y,2.54],[0,0,-1],[FRONT,BED],'Front triangular tile plane')
        for sign in(-1,1):
            for dx in(.178,.267,.376):
                for y in(.465,.616,.753):
                    ask([c+sign*dx,y,2.6],[0,0,-1],[SIDE,BED],'Two pitched cheeks of the roof')
        for y in(.375,.563,.719,.855):ask([c,y,2.44],[0,0,-1],[HIP],'Short central ridge')
        for dx in(-.258,0,.261):
            for z in(.53,.627,.765,.915):ask([c+dx,-1.3,z],[0,1,0],[GLASS],'Inset glazing beneath hip')
        for dx in(-.352,-.123,.122,.352):ask([c+dx,-1.35,.735],[0,1,0],[MULL],'Independent window bars')
    for x in(-1.68,-1.48,-.41,-.04,.35,1.5,1.66):
        for y in(-.73,-.63):ask([x,y,2.45],[0,0,-1],[FIELD,BED],'Parent roof continues below both dormers')
    return reads
