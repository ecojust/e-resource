from bowed_balcony import *
def test(tri,names,hit):
    rows=[]
    def probe(x,z,mat,label,y=-.77):
        a=hit(tri,names,np.array([x,y,z]),np.array([0.,1.,0.]));assert a and a[0]==mat,(x,z,mat,a)
        rows.append(dict(label=label,material=mat,point=a[1]))
    for z in [.97,1.07,1.17,1.55,1.66,1.72]:
        for x in [-.485,-.129,.124,.491]:probe(x,z,GLASS,'Two rectangular door lights')
        probe(0,z,WOOD,'Central door stile')
    for sign in [-1,1]:
        for r in [.613,.651,.684,.712]:
            for a in [.10,.27,.46,.74,1.01]:probe(sign*r*np.cos(a),SPRING+r*np.sin(a),TRIM,'Concentric curved arch mouldings')
        for z in [.30,.98,1.59,2.11,2.51]:probe(sign*1.184,z,STONE,'Render beyond the shallow bow')
    for x in np.linspace(-.9,.9,15):probe(x,.866,STEEL,'Upper rail of the bowed balcony')
    for z in [2.455,2.491,2.543,2.565]:probe(0,z,TRIM if z<2.458 else PLINTH,'Tapered keystone and central tongue')
    return rows
