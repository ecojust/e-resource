from round_bay import *
def test(tri,names,hit):
    rows=[]
    def test_at(u,z,mat,tag):
        t=u/R;p=np.array(pos(u,z,.45));direction=np.array([-np.sin(t),np.cos(t),0.])
        a=hit(tri,names,p,direction);assert a and a[0]==mat,(u,z,mat,a)
        rows.append(dict(label=tag,material=mat,point=a[1]))
    for u in np.linspace(-1.21,1.21,21):
        for z in [.20,.48,2.19,2.632,2.823]:
            target=WHITE if z in [.20,2.632,2.823] else PLASTER
            test_at(u,z,target,'Concentric wall and stringcourse surface')
    for sign in [-1,1]:
        for x in [.082,.158,.233]:
            for z in [.76,.902,1.086,1.384]:test_at(sign*x,z,GLASS,'Dark inset pane between metal glazing bars')
        for z in [.953,1.219,1.484]:test_at(sign*.162,z,FRAME,'Transverse steel bar')
    for z in [.75,1.03,1.33]:test_at(0,z,FRAME,'Central steel mullion')
    return rows
