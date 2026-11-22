from tiled_posts import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,mat,desc):
        r=hit(tri,names,np.array([x,-.66,z]),np.array([0,1,0]));assert r and r[0]==mat,(x,z,mat,r)
        rows.append(dict(label=desc,material=mat,point=r[1]))
    for x in CENTRES:
        for xx in [-.097,0,.096]:
            for z in [.34,.57,.91,1.19,1.40,1.56]:check(x+xx,z,RENDER,'Rectangular buff panel')
        for side in [-1,1]:
            for z in [.16,.49,1.27,1.799]:check(x+side*.17,z,BASE if z<.2 else BORDER,'Cement base and edge')
        for xx in [-.05,0,.05]:
            check(x+xx,2.035,RENDER,'Inset triangular panel')
        check(x,2.281,RIDGE,'Rounded end of ridge')
    for p in digit_lines():
        q=p.representative_point();check(q.x,q.y,MARK,'Painted digit')
    return rows
