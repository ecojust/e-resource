from oculus_and_brickwork import *
def test(tri,names,hit):
    rows=[]
    def read(x,z,expected,label):
        r=hit(tri,names,np.array([x,-1.8,z]),np.array([0.,1.,0.]));assert r and r[0]==expected,(label,x,z,r)
        rows.append(dict(label=label,material=r[0],point=r[1]))
    for side in [-1,1]:
        for x in [.81,.94,1.05,1.16]:
            for z in [.12,.32,.54,.78,.99,1.22,1.45,1.61,2.42]:
                read(side*x,z,WALL,'Running bond around the opening')
    for n in range(-3,4):
        for x in [-.095,0,.095]:
            read(x,CZ+n*.071-.006,IRON,'Seven dark metal louvres')
            if abs(n)<3:read(x,CZ+n*.071+.029,SHADE,'Dark depth between louvres')
    for a in np.arange(0,2*pi,pi/2):
        for r in [.4,.471,.538]:read(r*cos(a),CZ+r*sin(a),KEY,'Wedge bridging the stone mouldings')
    for a in [.39,.71,1.01,2.15,2.42,3.59,4.08,5.21,5.68]:
        for r in [.376,.431,.548]:read(r*cos(a),CZ+r*sin(a),STONE,'Flats between concentric fillets')
    for z in [1.86,1.97,2.08,2.17]:read(0,z,STRIP,'Stone stem above the attic eye')
    return rows
