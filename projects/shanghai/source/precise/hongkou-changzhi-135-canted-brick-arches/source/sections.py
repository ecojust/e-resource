from brick_arches import *
def test(t,m,hit):
    rows=[]
    def probe(u,z,material,label):
        x,y,_=projected(u,z,0)
        found=hit(t,m,np.array([x,y-1,z]),np.array([0.,1.,0.]))
        assert found and found[0]==material,(u,z,label,found)
        rows.append(dict(label=label,material=material,point=found[1]))
    for side in (-1,1):
        c=side*CENTRE
        for du in (-.28,-.13,.12,.27):
            for z in (.98,1.27,1.65,2.13,2.51,2.69):
                probe(c+du,z,GLASS,'Recessed lower sash')
            probe(c+du,.813,HOOD,'Red sill')
        for z in (1.17,1.66,2.12,2.72):probe(c,z,WOOD,'Central glazing bar')
        for a in (.44,.90,2.19,2.63):
            probe(c+.61*cos(a),SPRING+.61*sin(a),TILE,'Raised arch hood')
        for z in (3.292,3.423,3.505):probe(c,z,STONE,'Axial keystone')
        for dx in (-.22,.22):
            for z in (2.858,2.905):probe(c+dx,z,TRANS,'Separate upper fanlight')
        for u in (.35,.59,1.26,1.57):
            for z in (.110,4.089):
                probe(side*u,z,TILE,'Continuous projecting string')
        for z in(.39,.95,1.56,2.12,2.65,3.65):probe(side*.265,z,BRICK,'Brick next to corner pier')
    return rows
