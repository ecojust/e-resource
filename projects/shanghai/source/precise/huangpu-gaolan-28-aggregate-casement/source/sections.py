from garden_window import *
def test(t,names,hit):
    rows=[]
    def q(x,z,want,label):
        p=hit(t,names,np.asarray([x,-2,z]),np.asarray([0,1.,0]))
        assert p and p[0] in want,(x,z,p,want)
        rows.append(dict(label=label,material=p[0],point=p[1]));return -p[1][1]
    for c in (-.454,.454):
        for j in range(4):
            for i in (-1,1):
                for dx in (-.044,.044):
                    assert abs(q(c+i*.195+dx,1.011+(j+.5)*.294,[GLASS,SKY],'Small light in two-leaf window')+.107)<.0011
        for j in range(1,4):
            for dx in (-.31,-.16,.13,.33):assert abs(q(c+dx,1.011+j*.294,[EDGE],'Thin horizontal muntin')+.058)<.001
        for z in (1.082,1.44,1.64,1.95,2.08):assert abs(q(c,z,[EDGE],'Vertical centre muntin')+.059)<.001
    for x in (-1.65,-1.37,-1.15,1.1,1.45,1.74):
        for z in (.32,.65,1.1,1.68,2.31,2.53):assert -.001<=q(x,z,[WALL],'Pebbledash on either side of the window')<.008
    for x in np.linspace(-.91,.91,11):
        assert abs(q(x,.854,[STONE],'Projecting stone drip')-.164)<.0011
    for x in np.linspace(-1.58,1.58,6):
        for z in (2.63,2.672):assert q(x,z,[TIP],'Pale rafter tail')>.28
    for x in np.linspace(-1.82,1.82,15):
        assert abs(q(x,2.799,[EAVE],'Dark outer eave fascia')-.402)<.0011
    return rows
