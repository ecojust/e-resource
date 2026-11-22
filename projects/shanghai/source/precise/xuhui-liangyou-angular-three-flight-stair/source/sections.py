from faceted_stair import *
def test(tri,names,hit):
    rows=[]
    def cast(xy,z,mat,desc):
        result=hit(tri,names,np.array([*xy,z]),np.array([0.,0.,-1.]))
        assert result and result[0]==mat,(xy,z,mat,result)
        rows.append(dict(label=desc,material=mat,point=result[1]))
    for a,c,b,d,lo,hi in course():
        for v in [.30,.53,.72]:
            inside=a+.47*(b-a);outside=c+.47*(d-c)
            cast(inside+v*(outside-inside),lo+.11,MOSAIC,'Mosaic field')
        cast((a+c)/2+.04*((b+d-a-c)/2),lo+.10,STONE,'Pale anti-slip nosing')
        for t in [.25,.76]:cast(a+t*(b-a),lo+t*(hi-lo)+1.1,WOOD,'Crown of wooden handrail')
    return rows
