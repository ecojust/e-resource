from roof_dormer import *
def test(t,names,hit):
    out=[]
    def ck(o,d,material,label):
        r=hit(t,names,np.asarray(o),np.asarray(d));assert r and r[0]==material,(o,d,material,r);out.append(dict(label=label,material=material,point=r[1]))
    for side in [-1,1]:
        for ix in [1,3,5,7]:
            x=side*(.586+ix*.053)
            for j in range(14):ck([x,.052+j*.11,2.25],[0,0,-1],TILE,'Curved tile crown beside the dormer')
    for mid in [-.239,.239]:
        for x in [-.124,.077,.137]:
            for z in [.635,.773,.99,1.15]:ck([mid+x,-.59,z],[0,1,0],GLASS,'Distinct half of the twin light')
    for x in [-.45,-.22,.03,.26,.47]:ck([x,-.60,1.375],[0,1,0],CAP,'Dark projected dormer edge')
    for h in [.66,.82,1.20]:ck([.002,-.52,h],[0,1,0],SASH,'Central meeting stile')
    return out
