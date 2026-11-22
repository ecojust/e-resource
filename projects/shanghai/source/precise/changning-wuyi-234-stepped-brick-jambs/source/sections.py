from stepped_window import *
def test(tri,names,hit):
    rows=[]
    def probe(x,z,material,what):
        ans=hit(tri,names,np.array([x,-.7,z]),np.array([0.,1.,0.]))
        assert ans and ans[0]==material,(x,z,material,ans)
        rows.append(dict(label=what,material=material,point=ans[1]))
    for j in range(N):
        z=BOTTOM+(j+.5)*RISE
        for side in (-1,1):
            l,r=sorted((CORE*side,(CORE+reach(j,side))*side))
            for k,frac in enumerate((.22,.89)):
                probe(l+frac*(r-l),z,DEEP if (j+2*k)%7==0 else BRICK,'Two individual stretchers in the stepped jamb')
            probe(side*(CORE+reach(j,side)+.035),z,PLASTER,'Combed wall beyond the brick tooth')
    for z in (.89,1.04,1.3,1.5,1.75):
        for x in(-.18,0,.17):probe(x,z,GLASS,'Clear central single pane')
        for x in(-.355,.355):probe(x,z,FRAME,'Light painted frame')
    for x in(-.4,-.23,0,.23,.4):probe(x,BOTTOM-.037,STONE,'Projected sill')
    return rows
