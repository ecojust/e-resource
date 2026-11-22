from brick_chimney import *
def test(tri,names,hit):
    rows=[]
    def shot(x,z,material,name):
        a=hit(tri,names,np.array([x,-.83,z]),np.array([0.,1.,0.]));assert a and a[0]==material,(x,z,material,a)
        rows.append(dict(label=name,material=material,point=a[1]))
    for s in [-1,1]:
        for dx in [-.072,.052]:
            for z in [.294,.39,.561,.748,.834]:shot(s*.84+dx,z,GLASS,'Attic glazing beside stack')
        for z in [.32,.47,.592,.74]:shot(s*.84,z,FRAME,'Slim upright sash')
        for x in np.linspace(.49,1.72,18):shot(s*x,roofheight(s*x)+.038,ROOF,'Sloping dark verge')
        for z in [.278,.633,1.013,1.533,2.117,2.64,2.889,3.102]:shot(s*.284,z,BRICK,'Face of high masonry shaft')
        for z in [3.138,3.201,3.254]:shot(s*.057,z,CAP if z>3.230 else BRICK,'Corbelled cap course')
        for z in [.122,.337,.515,.662]:shot(s*1.121,z,BRICK,'Gable wall beside paired lights')
    return rows
