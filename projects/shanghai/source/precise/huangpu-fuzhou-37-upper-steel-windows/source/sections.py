from steel_bays import *
def test(t,names,hit):
    result=[]
    def probe(x,z,accepted,label):
        p=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]))
        assert p and p[0] in accepted,(x,z,label,p)
        result.append({'label':label,'material':p[0],'point':p[1]});return -p[1][1]
    for c in CS:
        for off in (-.505,.505):
            mid=c+off
            for dz in (.19,.50,.89,1.20):
                for dx in (-.16,.15):
                    assert probe(mid+dx,3.213+dz,[PANE,SKY],'Narrow upper light')<-.13
            for dx in (-.19,.17):
                assert probe(mid+dx,3.15,[SILL],'Upper sill')>.10
            for z in (3.53,4.21):probe(mid,z,[FRAME],'Narrow upper central mullion')
        for dx in (-.77,-.47,-.15):
            for dz in (.14,.44,.80,1.2,1.61):
                probe(c+dx,.301+dz,[PANE,SKY],'Broad lower grid reduces the apparent sash spacing')
        for dx in (-.87,-.42,.43,.87):
            for z in (2.915,4.98,5.115):probe(c+dx,z,[WALL,SILL,CAP],'Continuous horizontal bands take a raised first hit')
    for z in np.linspace(.29,4.62,19):assert probe(.147,z,[PIPE,CLIP,WALL],'Rainwater pipe in front of the wall')>.13
    for z in (3.67,4.14,4.41):
        for c in CS:probe(c,z,[WALL],'Solid strip between each upper window pair')
    return result
