from arched_light import *
def test(t,names,hit):
    rows=[]
    def take(x,z,allowed,label):
        result=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]));assert result and result[0]in allowed,(x,z,label,result)
        rows.append(dict(label=label,material=result[0],point=result[1]));return -result[1][1]
    for i,(c,r,spring,bottom)in enumerate(CASES):
        scale=.62 if i else 1.
        for theta in np.linspace(.20,pi-.20,18):
            for dr,mat in [(.034,DARK),(.096,LIP),(.156,STONE)]:
                rr=r+dr*scale;take(c+rr*cos(theta),spring+rr*sin(theta),[mat],'Arc moulding at several angles')
        for d in (-.77,-.48,.26,.67):
            for z in (.22,.45,.74):assert take(c+d*r,bottom+(spring-bottom)*z,[GLASS],'Recessed window glass beneath straight transom')<-.202
            take(c+d*r,spring-.030*scale,[BAR],'Straight transom')
        for a in (-1,1):
            for dz in (.17,.34):take(c+a*(r+.08*scale),spring-dz,[JAMB],'Arch load path to jamb')
    return rows
