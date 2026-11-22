from pediment_grille import *
def test(tri,names,hit):
    rows=[]
    def ck(x,z,m,name):
        r=hit(tri,names,np.array([x,-.7,z]),np.array([0,1,0.]));assert r and r[0]==m,(x,z,m,r);rows.append(dict(label=name,material=m,point=r[1]))
    for x in np.linspace(-.44,.44,7):
        for z in [.068,.189,.375,.470,.921,1.235,1.334]:ck(x,z,IRON,'Upright bar of the grille')
    for x in CENTRES:
        for angle in [.44,.83,1.91,2.39,3.59,4.03,5.12,5.78]:
            ck(x+.056*np.cos(angle),.678+.056*np.sin(angle),RING,'Outer ring of grille ornament')
    for x in [-.742,.709]:
        for z in [.148,.399,.801,1.108,1.443,1.691,1.928]:ck(x,z,BRICK,'Exposed red surrounding brickwork')
    for x in [-.175,-.089,0,.079,.182]:
        for z in [1.65,1.679,1.721]:ck(x,z,SHADE,'Plain inset triangular field')
    for x in [-.049,.049]:
        p=diamond(x,.678,.071,.061);q=p.exterior.interpolate(.167,normalized=True);line=p.exterior.interpolate(.167,normalized=True);pos=np.array([x,.678])*.032+np.array([line.x,line.y])*.968
        ck(*pos,RING,'Edge of central interlocked lozenge')
    return rows
