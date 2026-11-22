from lancets import *
def test(t,m,hit):
    rows=[]
    def p(x,z,mat,caption):
        r=hit(t,m,np.array([x,-.99,z]),np.array([0.,1.,0.]));assert r and r[0]==mat,(x,z,caption,r)
        rows.append(dict(label=caption,material=r[0],point=r[1]))
    for c in(-.308,.308):
        for off in(-.175,-.08,.081,.176):
            for z in(1.08,1.37,1.65,2.05,2.98,3.64,4.16):p(c+off,z,CENTRE if 1.90<z<3.815 else BACK,'Dark glazing beyond the two lancets')
            for z in(.46,.84):p(c+off,z,CREAM,'Pale spandrel at the foot')
        for z in(1.20,1.54,1.88,3.84,4.061):p(c+.08,z,BARS,'Steel transom')
    for z in(.57,.85,1.35,1.80,2.16,2.83,3.36,4.09):p(0,z,BLUE,'Long central blue pier')
    for x in(-.68,-.65,.65,.68):
        for z in(.65,1.35,2.20,3.77,4.22):p(x,z,BLUE,'Blue shoulder below pointed hood')
    for x in(-.93,.93):
        for z in(.72,1.93,3.07,4.15,5.12):p(x,z,PAINT,'Ochre wall beyond the tower reveal')
    for x in(-.06,0,.06):p(x,4.796,BLUE,'Blue diamond above center')
    return rows
