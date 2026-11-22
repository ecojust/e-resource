from riverside_wall import *
def test(t,names,hit):
    rows=[]
    def probe(x,z,expected,detail):
        r=hit(t,names,np.array([x,-.7,z]),np.array([0.,1.,0.]));assert r and r[0]==expected,(x,z,expected,r)
        rows.append(dict(label=detail,material=r[0],point=r[1]))
    for x,z,r,t0 in (GATE,LEFT,RIGHT):
        for fx in (.18,.37,.59,.81):
            for fz in (.19,.39,.65,.82):probe(x+(r-x)*fx,z+(t0-z)*fz,INSIDE,'Dark opening inside the thickness of its surrounding wall')
    a,z,b,top=GATE
    for h in (.175,.42,.76,1.12,1.40,1.69):
        for side in (a-.046,b+.043):probe(side,h,STONE,'Stone gate jamb at riverside')
    for x in np.linspace(a-.032,b+.039,7):probe(x,top+.043,STONE,'Horizontal stone lintel')
    for x in (-3.03,-2.03,-1.60,-.66,.19,1.67,2.60,2.91):
        for z in (.27,.57,2.12,3.14,4.54):probe(x,z,LIME,'Riverbank elevation above the weathered base')
        probe(x,4.84,CAP,'Coping standing forward of the upper wall')
    for x,z,r,t0 in (LEFT,RIGHT):
        for pos in np.linspace(x+.042,r-.042,5):probe(pos,z-.027,SILL,'Sill of the smaller window')
    return rows
