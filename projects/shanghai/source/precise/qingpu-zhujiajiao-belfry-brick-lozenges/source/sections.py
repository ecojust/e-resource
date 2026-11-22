from blind_arcade import *
def test(tris,mats,hit):
    result=[]
    def sample(x,z,m,label):
        ans=hit(tris,mats,np.array([x,-1,z]),np.array([0.,1.,0.]));assert ans and ans[0]==m,(x,z,m,ans)
        result.append(dict(label=label,material=ans[0],point=ans[1]))
    for centers,spring,r,h,thick in BANDS:
        count=11 if len(centers)==2 else 7
        for cx in centers:
            for j in range(count):
                a=math.pi*(j+.5)/count;sample(cx+(r+thick/2)*math.cos(a),spring+(h+thick/2)*math.sin(a),RED if j%2==0 else ASH,'Radial brick in the historic blind arches')
    for cx in BAYS:
        for j,off in enumerate((0,1,2,3,4,3,2,1,0)):
            for dx in ([-off,off] if off else [0]):sample(cx+.087*dx,.49+.078*j,RED,'Stepped lozenge brick')
        sample(cx,.806,RED,'Small central brick inside the lozenge')
    for x in (-1.45,1.44):
        for j in range(7):sample(x,.37+j*.401,RED,'Horizontal pier band')
    return result
