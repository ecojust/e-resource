from curved_green_roof import *
def test(tri,names,hit):
    rows=[]
    def probe(a,h,expected,label):
        start=np.array([4*sin(a),-4*cos(a),h]);direction=np.array([-sin(a),cos(a),0.])
        q=hit(tri,names,start,direction);assert q and q[0]==expected,(label,a,h,q,expected)
        rows.append(dict(label=label,material=q[0],point=q[1]))
    for a in [-1.19,-1.08,-.77,-.64,-.52,-.27,-.16,-.04,.21,.32,.41,.48,.76,.84,.95,1.24,1.34]:
        for h in [.09,.164,.33,.52,.655,.78,.845]:probe(a,BASE+h*RISE,METAL,'Green surface between standing seams and overlaps')
    for a in [-1.38,-.9,-.42,.09,.61,1.12]:
        for h in [.12,.40,.60,.78]:probe(a,BASE+h*RISE,SEAM,'Raised metal rib before the sheets')
    for a in [-1.294,-.647,0,.647,1.294]:
        for h in [.28,.37,.444]:probe(a,h,PANEL,'Inset on curved stone drum')
    for a in [-1.18,-.72,-.22,.33,.85,1.4]:probe(a,.94,EDGE,'Dark rolled edge above cornice')
    return rows
