from relief_panels import *
def test(t,names,hit):
 out=[]
 def shot(x,z,materials,label):
    r=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]));assert r and r[0] in materials,(x,z,label,r)
    out.append({'label':label,'material':r[0],'point':r[1]});return -r[1][1]
 for c in CS:
    for j in (-OFFSET,OFFSET):
        x=c+j
        assert shot(x,Z,[BORDER],'Central boss')>.33
        for side in (-1,1):
            for h in (-.27,-.14,.04,.17,.26):
                assert shot(x+side*.367,Z+h,[BORDER],'Paired square moulding')>.32
                assert shot(x+h,Z+side*.367,[BORDER],'Paired square moulding')>.32
        for a in (pi/4,3*pi/4,5*pi/4,7*pi/4):
            angle=a+.24;s=.52;u=np.array([cos(angle),sin(angle)]);v=np.array([-sin(angle),cos(angle)])
            q=np.array([x,Z])+u*(.14+.183*s)+v*.007*sin(s*pi*.82)
            assert shot(*q,[FOL],'Three-dimensional folded leaf ridge')>.335
        for h in (-.28,.23):
            shot(x+h,Z,[BASE],'Unadorned ground between curls')
    for h in (-.62,-.38,.10,.49):
        for z in (.45,.97,1.47,3.64,4.07,4.45):shot(c+h,z,[PANE,SKY],'Glazing to both sides of the metal spandrel')
    for h in (-.70,-.22,.24,.69):
        for z in (2.09,3.371):assert shot(c+h,z,[BORDER],'Projecting lower moulding or head')>.29
 return out
