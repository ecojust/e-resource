from broken_pediment import *
def test(tri,names,hit):
    rows=[]
    def probe(x,z,mat,label):
        a=hit(tri,names,np.array([x,-.77,z]),np.array([0.,1.,0.]))
        assert a and a[0]==mat,(x,z,mat,a)
        rows.append(dict(label=label,material=mat,point=a[1]))
    for sign in (-1,1):
        for x in np.linspace(.266,.972,16):
            probe(sign*x,arc(x)+.045,EDGE,'Projecting upper lip of arched moulding')
            if arc(x)-.052 <= 1.057:
                probe(sign*x,arc(x)-.052,EDGE,'Lower spring disappears behind the horizontal coping')
            else:
                probe(sign*x,arc(x)-.052,STONE,'Lower stone face under lip')
        for z in (.16,.28,.42,.546):
            for x in (.143,.423,.592):probe(sign*x,z,GLASS,'Inset transom glass between timber bars')
            probe(sign*.311,z,TIMBER,'Vertical timber mullion')
        for z in (1.26,1.35,1.46,1.58):probe(sign*.204,z,BRICK,'Exposed red wall beside the stone urn')
        probe(sign*.824,.335,EDGE,'Lower round end of pendant bracket')
        probe(sign*.824,.824,EDGE,'Upper console below projecting lintel')
    for z in (1.122,1.26,1.32,1.41,1.48,1.54,1.59,1.63,1.674,1.713):probe(0,z,STONE,'Turned profile of the central urn')
    return rows
