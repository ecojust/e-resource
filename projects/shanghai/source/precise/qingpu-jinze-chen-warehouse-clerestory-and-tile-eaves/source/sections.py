from warehouse_eaves import *
def test(tris,mats,hit):
    records=[]
    def sample(start,d,mat,label):
        out=hit(tris,mats,np.array(start),np.array(d));assert out and out[0]==mat,(start,d,mat,out)
        records.append(dict(label=label,material=out[0],point=out[1]))
    for cy in (-.197,.109,.381,.697,.94,1.17):
        for x in CENTRES[1:-1:2]:
            sample((x,cy,2.9),(0,0,-1),TILE,'Crown of a hollow cover tile on either roof')
            sample((x+.086,cy,2.9),(0,0,-1),PAN,'Visible grey pan between tile crowns')
    for x in np.linspace(-1.45,1.45,11):
        for z in (1.02,1.25):sample((x,-.72,z),(0,1,0),WOOD,'Framing against the clerestory lights')
    for x in np.linspace(-1.305,1.305,10):
        for z in (1.04,1.27):sample((x,-.72,z),(0,1,0),GLASS,'Dark lights in the recessed band')
    for x in (-1.34,-.6,.18,1.27):sample((x,-.7,.586),(0,1,0),LIME,'Shallow lower eave moulding')
    return records
