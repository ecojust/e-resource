from faceted_quoined_bay import *
def test(t,names,hit):
    rows=[]
    for i in range(3):
        x,y,u,v,width=frame(i);mid=width/2;half=.447 if i==1 else .321
        def probe(s,z,m,label):
            start=position(i,s,-.55,z);r=hit(t,names,np.array(start),np.array([-v,u,0.]))
            assert r and r[0]==m,(i,s,z,m,r)
            rows.append(dict(label=label,face=i,material=r[0],point=r[1]))
        for n in range(11):
            for s in (.071,width-.071):probe(s,.11+.212*n,STONE,'Rusticated blocks on both facets of a corner')
        for s in (mid-.13,mid+.13):
            for z in (.32,.47,.62,2.39,2.49):probe(s,z,BRICK,'Coursed wall beyond sill and lintel')
            for z in (.739,2.62,2.711,2.771):probe(s,z,STONE if z<2.7 else SOFFIT if z<2.74 else CAP,'Projecting sill or stepped eave')
        for z in (1.,1.37,1.68,2.0):
            probe(mid,z,WOOD,'Meeting stile')
            for side in (-1,1):probe(mid+side*half*.50,z,DARK if side==1 and i==1 else GLASS,'Casement beyond stile')
    return rows
