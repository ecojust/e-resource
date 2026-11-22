from printing_works import *
def test(tri,names,hit):
 rows=[]
 def check(x,z,m,what):
    ans=hit(tri,names,np.array([x,-.47,z]),np.array([0.,1.,0.]))
    assert ans and ans[0]==m,(x,z,what,ans)
    rows.append(dict(label=what,material=m,point=ans[1]))
 for x in BAYS:
    for z in (1.03,1.24,1.40,1.64,1.78,1.99):
        for dx in (-.27,-.12,.12,.26):check(x+dx,z,GLASS,'Independent glazed light')
        check(x,z,SASH,'Central steel upright')
    for u in(-.315,-.155,0,.155,.315):
        for z in (2.38,2.68,2.78):check(x+u,z,CEMENT,'Concrete fin above the window')
    for j in range(11):
        k=0;u=x-.393+.1572*(k+.5)+(.0786 if j%2 else 0)
        check(u,.084+j*.069,RED if (j+2*k)%5==0 else BRICK,'Exposed brick stretcher in the apron')
        check(x,.084+j*.069,CEMENT,'Cast rib between red infill strips')
    check(x+.14,1.875,SASH,'Heavy transom')
 return rows
