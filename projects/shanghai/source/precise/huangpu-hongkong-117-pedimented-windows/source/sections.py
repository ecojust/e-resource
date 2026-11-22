from window_hoods import *
def test(t,names,hit):
 out=[]
 def take(x,z,allowed,label):
    r=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]));assert r and r[0]in allowed,(x,z,label,r)
    out.append(dict(label=label,material=r[0],point=r[1]));return -r[1][1]
 for c in CS:
    for x in (-.68,-.62,-.48,.15,.40,.60):
        for z in (.21,.59,1.03,1.42,1.68):assert take(c+x,z,[PANE,GH],'Lower paired sash behind the street face')<-.156
    for side in (-1,1):
        for d in (.025,.11,.19):
            take(c+side*.904,2.411+d,[STEM,LEAF],'Narrow ornament shaft outside the spandrel')
        for z in (.38,.73,1.15,1.62):take(c+side*.849,z,[CAP],'Jamb continuing up to the hood')
    for x in (-.64,-.33,.31,.69):take(c+x,3.507,[LIGHT],'Upper window sill drip edge')
 for dx in (-.92,-.66,-.37,.29,.62,.89):assert take(CS[0]+dx,2.233,[LIGHT],'Level cap of flat hood')>.34
 for z in (1.987,2.,2.055,2.118,2.158):assert take(CS[0],z,[KEY],'Short central key in level hood')>.32
 for dx in (-.88,-.63,-.37,.28,.61,.83):
    z=2.639-(.492/1.116)*abs(dx)+.096
    assert take(CS[1]+dx,z,[LIGHT],'Two opposing sloped cornices')>.33
 for z in (2.012,2.098,2.206,2.323,2.460,2.546):assert take(CS[1],z,[KEY],'Tall key under triangular pediment')>.32
 for dx in (-.10,-.048,.022,.075):
    take(CS[0]+dx,2.888,[LIGHT],'Bright central face of upper diamond')
 return out
