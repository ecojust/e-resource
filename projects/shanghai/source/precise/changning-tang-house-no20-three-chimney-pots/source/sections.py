from chimney_stack import *
def test(t,m,hit):
    rows=[]
    def ray(pt,d,material,label):
        v=hit(t,m,np.array(pt,dtype=float),np.array(d,dtype=float));assert v and v[0]==material,(pt,label,v)
        rows.append(dict(label=label,material=material,point=v[1]))
    for x in(-.65,-.43,-.21,.03,.17,.33,.53,.67):
        for z in(.19,.41,.89,1.38,1.78,2.09,2.40,2.54):ray((x,-1,z),(0,1,0),BRICK,'Brick face of the stack')
        for z in(2.64,2.73,2.835,2.890):ray((x,-1,z),(0,1,0),LIGHT,'Three successive pale cornice faces')
        ray((x,-1,2.795),(0,1,0),LIP,'Dark cap joint')
    for cx in (-.49,0,.49):
        for dx,dy in[(.11,0),(-.11,0),(0,.112),(0,-.111)]:
            ray((cx+dx,-.10+dy,4),(0,0,-1),LIGHT,'Raised circular rim')
        ray((cx,-.10,4),(0,0,-1),MOUTH,'Open throat of each of the three pots')
        ray((cx,-1,3.015),(0,1,0),POT,'Short pot barrel')
    for x in (1.12,1.43,1.76,2.03):
        z=1.76+(x-.73)*(-1.09/1.55)
        ray((x,-1,z-.035),(0,1,0),LIGHT,'Coping on right slope')
    return rows
