from front_arch import *
def test(tri,names,hit):
    rows=[]
    def shot(x,z,material,label,depth=-.94):
        result=hit(tri,names,np.array([x,depth,z]),np.array([0.,1.,0.]));assert result and result[0]==material,(x,z,material,result)
        rows.append(dict(label=label,material=result[0],point=result[1]))
    for left,right in openings:
        mid=(left+right)/2; quarter=(right-left)*.245
        for z in (.89,1.24,1.54,1.96,2.25,2.50):
            for x in (mid-quarter,mid+quarter):shot(x,z,GLASS,'A divided glass light')
        for z in (1.10,1.75,2.32,2.60):shot(mid,z,FRAME,'Painted glazing bar')
    for a in np.linspace(.18,pi-.18,19):
        shot(1.47*cos(a),SPRING+1.25*sin(a),PEBBLE,'Pebbled arched surround')
        shot(1.588*cos(a),SPRING+1.455*sin(a),CAP,'Overhanging dark arch hood')
    for cx in (-.8,-.47,0.,.47,.8):shot(cx,2.85,WASH,'Plastered area over the straight window heads')
    for j in range(6):
        cx=(j-2.5)*.47
        for off in (-.089,.089):shot(cx+off,.6185,RAIL,'Inclined edge of open diamond')
        shot(cx,.825,CAP,'Balcony handrail')
    for j in range(5):shot((j-2)*.47,.574,RAIL,'Vertical between adjacent diamonds')
    for s in (-1,1):
        for z in (1.06,1.41,1.9,2.40):shot(1.44*s,z,PEBBLE,'Side upright in pebble finish')
    return rows
