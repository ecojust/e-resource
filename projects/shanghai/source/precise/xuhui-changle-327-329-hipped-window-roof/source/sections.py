from hip_roof import *
def test(t,names,hit):
    checks=[]
    def sample(o,d,material,comment):
        result=hit(t,names,np.asarray(o),np.asarray(d));assert result and result[0]==material,(comment,o,result,material)
        checks.append(dict(material=material,label=comment,point=result[1]))
    for side in ('front','left','right'):
        for r in (1,3,5,7,9,11):
            for u in ((.17,.35,.61,.77) if side=='front' else (.34,.44,.56,.67)):
                x,y,z=roof_point(side,u,(r+.54)/16);sample([x,y,3.24],[0,0,-1],TILE,'Tiled roof slope '+side)
    for sign in (-1,1):
        for row in range(1,13):
            x,y,z=roof_point('front',0 if sign<0 else 1,(row+.35)/14)
            sample([x,y,3.21],[0,0,-1],RIDGE,'Diagonal hip cap')
    for center in (-.95,.96):
        for dx in (.093,.247,.321):
            for z in (.31,.55,.81,1.025):sample([center+dx,-.6,z],[0,1,0],GLASS,'Closed casement light')
        sample([center,-.5,.121],[0,1,0],SILL,'Pale projecting windowsill')
    for x in (-1.83,-1.29,-.38,.34,1.18,1.79):sample([x,-.5,1.56],[0,1,0],WOOD,'Front fascia')
    return checks
