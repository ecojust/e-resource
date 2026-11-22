from veranda import *
def test(tri,names,hit):
    rows=[]
    def check(x,z,m,label):
        ans=hit(tri,names,np.array([x,-.62,z]),np.array([0.,1.,0.]))
        assert ans and ans[0]==m,(x,z,label,ans)
        rows.append(dict(label=label,material=m,point=ans[1]))
    for x in X:
        for z in (.49,.74,.99,1.21,1.48,1.66,1.89,2.035):
            for u in (-.132,.132):check(x+u,z,GLASS,'Independent ray within the glazed opening')
            check(x,z,FRAME,'Central steel muntin')
        for z in (.64,1.54,2.01):check(x+.245,z,STONE,'Pale narrow opening reveal')
        check(x,2.27,STONE,'Projecting ridge of the peaked head')
    for x in (-.89,-.39,.14,.44,.91):
        check(x,2.562,STONE,'Projected horizontal cornice')
        check(x,2.68,CREAM,'Parapet sill')
    for x in np.linspace(-.87,.87,15):
        check(x,3.011,STONE,'Individual turned baluster')
    return rows
