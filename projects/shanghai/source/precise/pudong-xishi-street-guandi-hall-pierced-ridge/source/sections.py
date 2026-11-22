from temple_ridge import *
def test(t,names,hit):
    out=[]
    def sample(o,d,material,what):
        v=hit(t,names,np.asarray(o),np.asarray(d))
        assert (v[0] if v else None)==material,(o,what,material,v)
        out.append(dict(label=what,material=material,point=v[1] if v else None))
    for left,right in LATTICE:
        for i in range(1,7):
            # At this elevation the two sets of diagonals approach quarter points of each period.
            z=.332;x=left+i*.074+(.332-.255)*.119/.154
            sample((x,-1.61,z),(0,1,0),BAR,'Diagonal rib crossing')
            sample((x-.022,-1.61,z),(0,1,0),None,'Unfilled space between the crossing ribs')
    for x in (-1.91,-1.78,-1.125,-.372,-.21,.010,.24,.38,1.12,1.76,1.93):
        sample((x,-1.58,.35),(0,1,0),RIDGE,'Solid portion of ridge between panels')
    for x in (-1.98,1.98):sample((x,-1.58,.35),(0,1,0),LIP,'Descending end ridge crossing the view of the solid panel')
    for i in (2,5,9,13,18,22,26,31,36,39):
        for j in range(7):
            x=-2.185+(i+.43)*4.37/42;y=-.99+(j+.49)*.139
            sample((x,y,.90),(0,0,-1),TILE,'Upper grey tile courses')
    for x in (-1.86,-1.21,-.77,-.35,.13,.61,1.33,1.86):
        sample((x,-1.71,.235+crown(x)),(0,1,0),LIP,'Curved plinth below pierced rail')
    return out
