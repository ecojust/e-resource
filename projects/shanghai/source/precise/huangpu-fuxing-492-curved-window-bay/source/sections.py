"""Check the first visible material and glazing depth across each face of the bay."""
from curved_bay import *
def test(tri,materials,hit):
    observations=[]
    for index,(a,e) in enumerate(SIDES):
        span,pt=frame(a,e);mid=span/2;ww=1.27 if index==1 else .96
        lo,hi=mid-ww/2,mid+ww/2
        direction=np.array(pt(0,0,0))-pt(0,0,1)
        def test_at(u,z,mat,label):
            res=hit(tri,materials,np.array(pt(u,z,2)),direction)
            assert res and res[0]==mat,(index,u,z,mat,res)
            observations.append(dict(label=label,material=mat,point=res[1]));return np.dot(np.array(res[1])-pt(u,z,0),-direction)
        for u in (lo+.065,mid-.19,mid+.17,hi-.059):
            for z in (1.56,1.91,2.64,3.04):
                depth=test_at(u,z,GLASS,'Glass recessed behind its own bay')
                assert -.245 < depth < -.241
            test_at(u,2.83,METAL,'Sash transom')
        for u in np.linspace(lo+.104,hi-.104,5 if index==1 else 3):
            for z in (.72,.852,1.034):test_at(u,z,RAIL,'Solid belly and neck of turned baluster')
        us=np.linspace(lo+.104,hi-.104,5 if index==1 else 3)
        for u in (us[:-1]+us[1:])/2:
            for z in (.695,.86):test_at(u,z,FLOOR,'Clear gap reveals recessed backing')
        for u in (mid-.11,mid+.17,mid+.35):
            for z,mat in [(3.835,JOINT),(3.91,TRIM),(4.095,TRIM),(4.20,STONE)]:
                test_at(u,z,mat,'Profile of projecting cornice')
    return observations
