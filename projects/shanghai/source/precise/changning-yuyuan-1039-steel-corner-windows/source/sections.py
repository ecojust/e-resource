from double_face import *
def test(tris,names,hit):
    result=[]
    for side in (False,True):
        def located(u,z,material,note):
            origin=np.array(place(side,u,.62,z));direction=np.array([-1.,0.,0.]) if side else np.array([0.,1.,0.])
            row=hit(tris,names,origin,direction)
            assert row and row[0]==material,(side,u,z,material,row)
            result.append(dict(label=('Return ' if side else 'Front ')+note,material=material,point=row[1]))
        for x in(-.43,-.13,.13,.43):
            for z in(1.14,1.36,1.57,1.81,2.05):located(x,z,PANE,'glazing')
            for z in(1.254,1.477,1.698,1.921):located(x,z,STEEL,'horizontal glazing rail')
        for x in(-.282,0,.282):
            for z in(1.16,1.56,2.03):located(x,z,STEEL,'vertical bar')
        for x in(-.512,-.384,.384,.512):
            for z in(.38,.62,.81):located(x,z,IRON,'straight lower bar')
        for x in(-.81,.81):
            for z in(.39,1.34,2.43):located(x,z,YELLOW,'ochre wall')
        if side:
            for x,z in[(.174,.575),(-.174,.575),(0,.800),(0,.350)]:located(x,z,IRON,'diamond points')
    return result
