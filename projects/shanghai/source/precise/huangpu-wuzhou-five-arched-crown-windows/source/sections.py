from crown import *
def test(t,names,hit):
    out=[]
    def ray(x,z,expected,label):
        r=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]))
        if expected:assert r and r[0] in expected,(x,z,label,r,expected)
        else:assert r is None,(x,z,label,r)
        out.append(dict(label=label,point=r[1] if r else None,material=r[0] if r else None))
        return r[1] if r else None
    for c in CENTERS:
        for x in (-.26,-.14,.14,.26):
            for z in (.49,.85,1.39,2.93,3.35,3.51):
                p=ray(c+x,z,[SKY,PANE],'Five aligned upper and lower glazed openings');assert abs(p[1]-.168)<.001
        for dx in (-.246,0.,.246):
            for z in (1.86,2.27,2.52):
                p=ray(c+dx,z,[APRON],'Three panels on the spandrel');assert abs(p[1]+.028)<.001
        for x in (-.19,-.06,.06,.19):
            p=ray(c+x,3.87,[PANE],'Recess behind the round window head');assert abs(p[1]-.185)<.001
    for l,r,h in levels:
        x=(l+r)*.5;ray(x,h+.045,[],'Open sky above individual parapet cap')
        ray(x,h-.017,[EDGE,PIER],'Solid leading edge of the stepped skyline')
    for j in range(9):
        ray(.035,4.49+j*.158+.031,[GRILLE],'Central slot');ray(.035,4.49+j*.158+.095,[EDGE],'Rib of central grille')
    return out
