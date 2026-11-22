from flowered_window import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,m,label):
        a=hit(tri,names,np.array([x,-.6,z]),np.array([0,1,0.]));assert a and a[0]==m,(x,z,m,a)
        rows.append(dict(label=label,material=m,point=a[1]))
    for x,z in FLOWERS:
        check(x+.001,z+.001,CENTRE,'Boss of small flower')
        for dr in range(7):
            rad=2*np.pi*dr/7+.17
            check(x+.041*np.cos(rad),z+.041*np.sin(rad),RELIEF,'Separate petal around a flower boss')
    for x in np.linspace(-.59,.209,9):
        for z in [.24,.41,.69,.97]:check(x,z,GLASS,'Glass behind the wall moulding')
    for x in np.linspace(-.917,.87,11):
        for z in [1.515,1.477]:check(x,z,MOULD,'Horizontal raised moulding above flowers')
        check(x,1.657,BRICK,'Brickwork above decorated head')
    for z in [.217,.448,.74,1.024]:check(-.673,z,MOULD,'Left narrow moulding')
    return rows
