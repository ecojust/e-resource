from branch_arch import *
def test(tri,m,hit):
    rows=[]
    def p(x,z,material,label):
        ray=hit(tri,m,np.array([x,-1,z]),np.array([0.,1.,0.]))
        assert ray and ray[0]==material,(x,z,material,ray)
        rows.append(dict(label=label,material=material,point=ray[1]))
    for x in(-2.30,-2.17,2.17,2.30):
        for z in(.08,.34,.45,.57,.86,1.27,1.83,2.07):p(x,z,GREY,'Blue-grey side wall')
        for z in(.167,.241,.65,.721):p(x,z,BAND,'Returning red stripe')
    for a in (.12,.25,.41,.58,.73,.88,1.03,1.19,1.32,1.83,1.97,2.12,2.30,2.44,2.60,2.76,2.92,3.05):
        p(2.042*cos(a),SPRING+1.256*sin(a),LIP,'Outside lip on red arch')
    for z in(1.63,1.70,1.81,1.90,2.01):
        for x in(-.092,-.037,.041,.095):p(x,z,INSET,'Inset of pale keystone')
        for x in(-.162,.162):p(x,z,STONE,'Raised border of keystone')
    for x in(-1.32,-.83,0,.71,1.22):
        for z in(.21,.57,.81):
            assert hit(tri,m,np.array([x,-1,z]),np.array([0.,1.,0.])) is None, 'open passage'
    return rows
