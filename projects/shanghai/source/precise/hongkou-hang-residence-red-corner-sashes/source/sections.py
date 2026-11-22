import numpy as np
from corner_sashes import frame,GLASS,POST,FINE,WALL,STONE
def test(tri,m,hit):
    results=[]
    for i in range(2):
        length,count,xyz,out=frame(i)
        def probe(t,z,expected,label):
            d=np.array([-out[0],-out[1],0.]);origin=np.array(xyz(t,z,0))-.85*d
            r=hit(tri,m,origin,d);assert r and r[0]==expected,(i,t,z,expected,r)
            results.append(dict(label=label,material=r[0],point=r[1]))
        for bay in range(count):
            for f in (.17,.3,.67,.81):
                t=(bay+f)*length/count
                for z in (.53,.72,1.04,1.21,1.49,1.72):probe(t,z,GLASS,'Recessed upper and lower lights')
                for z in (.395,1.305,1.91):probe(t,z,POST,'Three red returning rails')
                probe(t,.332,STONE,'Projecting sill face')
                probe(t,.19,WALL,'Wall beneath sill')
            for z in (.56,.82,1.18):probe((bay+.5)*length/count,z,FINE,'Lower fine vertical')
    return results
