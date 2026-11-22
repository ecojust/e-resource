"""The second copper-clad roof dormer from the left in CyberCop's 2007 garden photograph."""
from math import sin
BASE_COLOURS={'oxidised cap edge':[.485,.555,.461],'deep cap shadow':[.145,.170,.142],'side copper sheet':[.305,.325,.263],'second sheet patina':[.354,.369,.299],'standing seam':[.24,.272,.224],'drip edge':[.356,.383,.285],'deep frame recess':[.145,.134,.106],'painted sash stile':[.45,.386,.307],'dark glazing bar':[.180,.170,.149],'smoked glass':[.301,.308,.284],'window reflection':[.374,.365,.324],'unseen reveal':[.170,.154,.131],'roof pan':[.497,.435,.287],'patinated roof pan':[.437,.419,.278]}
PALETTE={name:{'color':rgb,'roughness':.65} for name,rgb in BASE_COLOURS.items()}
HEIGHT=1.45
def block(b,name,x0,x1,y0,y1,z0,z1,material):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(3,7,6),(3,6,2),(0,4,7),(0,7,3),(1,2,6),(1,6,5)]
    b.add(v,f,material,name)
def folded_prism(b,name,profile,x0,x1,material):
    n=len(profile);v=[(x,y,z)for x in (x0,x1)for y,z in profile];f=[]
    for i in range(1,n-1):f.extend([(0,i+1,i),(n,n+i,n+i+1)])
    for i in range(n):
        k=(i+1)%n;f.extend([(i,k,n+k),(i,n+k,n+i)])
    b.add(v,f,material,name)
def add_building(b,lod):
    # The side panels disappear into a roof plane rising away from the front of the dormer.
    def roof_z(y):return -.055+.69*y
    def cap_z(y):return HEIGHT+.035*y
    for side,s in [('left',-1),('right',1)]:
        a,c=sorted((s*.615,s*.654))
        for j,(start,end)in enumerate([(0,.49),(.49,.89),(.89,1.22)]):
            shell=[(start,roof_z(start)),(end,roof_z(end)),(end,cap_z(end)),(start,cap_z(start))]
            folded_prism(b,side+' cheek sheet '+str(j+1),shell,a,c,'side copper sheet' if j%2==0 else 'second sheet patina')
        for j,y in enumerate([.49,.89]):
            off0,off1=sorted((s*.652,s*.668));folded_prism(b,side+' vertical cheek seam '+str(j+1),[(y-.006,roof_z(y)+.015),(y+.006,roof_z(y)+.025),(y+.006,cap_z(y)),(y-.006,cap_z(y))],off0,off1,'standing seam')
        outer0,outer1=sorted((s*.652,s*.690));folded_prism(b,side+' diagonal flashing',[(0,.011),(1.22,roof_z(1.22)+.065),(1.22,roof_z(1.22)+.093),(0,.038)],outer0,outer1,'drip edge')
    folded_prism(b,'shallow metal dormer cap',[(-.06,1.433),(1.24,1.477),(1.24,1.512),(-.06,1.47)],-.683,.683,'oxidised cap edge')
    block(b,'cap edge shadow',-.673,.673,-.065,-.02,1.407,1.436,'deep cap shadow')
    block(b,'front cap folded lip',-.689,.689,-.075,-.056,1.436,1.475,'oxidised cap edge')
    for name,a,c in [('left',-.652,-.553),('right',.553,.652)]:
        block(b,name+' outer copper trim',a,c,-.028,.088,-.002,1.424,'oxidised cap edge')
    block(b,'stone or painted outer sill',-.649,.649,-.051,.091,-.039,.019,'drip edge')
    block(b,'top inner frame shade',-.553,.553,.012,.10,1.304,1.416,'deep frame recess')
    for leaf,a,c in [('left',-.548,-.009),('right',.009,.548)]:
        left=a+.025;right=c-.025;mid=(left+right)/2;low=.040;up=1.276
        block(b,leaf+' outer stile',a,left,.021,.082,.013,1.305,'painted sash stile')
        block(b,leaf+' meeting stile',right,c,.021,.082,.013,1.305,'painted sash stile')
        block(b,leaf+' top rail',left,right,.021,.082,up,1.305,'painted sash stile')
        block(b,leaf+' bottom rail',left,right,.021,.082,.013,low,'painted sash stile')
        block(b,leaf+' fine mullion',mid-.009,mid+.009,.036,.059,low,up,'dark glazing bar')
        for j in range(1,4):
            z=low+(up-low)*j/4
            block(b,leaf+' horizontal glazing bar '+str(j),left,right,.034,.061,z-.009,z+.009,'dark glazing bar')
        for j in range(4):
            z0=low+(up-low)*j/4;z1=low+(up-low)*(j+1)/4
            for k,(x0,x1) in enumerate([(left,mid),(mid,right)]):
                block(b,leaf+' glass '+str(j+1)+'-'+str(k+1),x0,x1,.068,.077,z0,z1,'window reflection' if (j*3+k+(leaf=='right'))%4==1 else 'smoked glass')
        if not lod:
            for j in range(3):
                z=.246+j*.384;x=c-.036
                block(b,leaf+' came joining cap '+str(j+1),x-.009,x+.009,.018,.030,z-.020,z+.020,'painted sash stile')
    block(b,'recess behind meeting stiles',-.009,.009,.076,.104,0,1.305,'unseen reveal')
    for side,s in [('left',-1),('right',1)]:
        x0,x1=sorted((s*.655,s*.960))
        p=[(-.044,roof_z(-.044)-.018),(1.223,roof_z(1.223)-.018),(1.223,roof_z(1.223)),(-.044,roof_z(-.044))]
        folded_prism(b,side+' short pitch below cheek',p,x0,x1,'roof pan'if s==-1 else 'patinated roof pan')
        a,c=sorted((s*.821,s*.838))
        folded_prism(b,side+' folded roof seam',[(y,z+.018)if i>=2 else(y,z)for i,(y,z)in enumerate(p)],a,c,'standing seam')
