"""Five street-boundary piers and the boarded spans visible on the 2023 face view."""
from terrace_wall import photo,block,limits,WHITE,BUFF,COURT,WOOD,finish
import numpy as np
CAP='Changchun terrace | pale coping and base'
BRONZE='Changchun terrace | bronze plaques'
SHADOW='Changchun terrace | shadow behind yard pales'
PALES=['Changchun terrace | stained yard board '+n for n in ('cedar','umber','ochre','rose')]
PALETTE={CAP:finish([188,181,163]),BRONZE:finish([109,76,47],.75,.30),SHADOW:finish([58,48,42])}
PALETTE.update({n:finish(c)for n,c in zip(PALES,[(103,70,54),(89,62,51),(113,82,63),(98,65,52)])})
YARD=-6.64
def add_enclosure(b,lod=False):
    # Cap and base centres are independently read on the front photo.
    # The gate photograph and the entrance on the building were taken at different distances.
    stations=[((87,411),(64,537),.73),((259,415),(248,538),.73),((438,414),(437,539),.72),((616,414),(625,538),.72),((782,415),(798,538),.76)]
    rows=[]
    for i,(uvtop,uvbase,width) in enumerate(stations):
        x1,zt=photo(*uvtop,YARD);x0,base=photo(*uvbase,YARD);x=(x1+x0)/2
        rows.append([x,width,base,zt]);tag='Street wall | pier '+str(i+1)
        block(b,x-width/2,x+width/2,YARD,YARD+.39,base,zt-.26,WHITE,tag+' brick shaft')
        block(b,x-width*.54,x+width*.54,YARD-.047,YARD+.43,base,base+.52,CAP,tag+' base')
        for zm,zp,out in [(-.29,-.222,.045),(-.223,-.132,.085),(-.135,-.075,.125),(-.076,-.020,.093),(-.021,.015,.045)]:
            block(b,x-width/2-out,x+width/2+out,YARD-out,YARD+.39+out,zt+zm,zt+zp,CAP,tag+' stepped coping')
        if i in (0,4):
            block(b,x-width*.32,x+width*.32,YARD-.025,YARD+.005,zt-1.23,zt-.69,BRONZE,tag+' wall plaque')
    for i,(a,c) in enumerate(zip(rows,rows[1:])):
        l=a[0]+a[1]/2;r=c[0]-c[1]/2;base=(a[2]+c[2])*.5
        mid_u=(stations[i][1][0]+stations[i+1][1][0])*.50
        bottom=photo(mid_u,497.7+i*.47,YARD)[1]
        top=min(a[3],c[3])-.54;tag='Street wall | span '+str(i+1)
        block(b,l,r,YARD+.04,YARD+.36,base,bottom,WHITE,tag+' red brick plinth')
        block(b,l,r,YARD+.005,YARD+.395,base,base+.34,CAP,tag+' base facing')
        block(b,l,r,YARD-.009,YARD+.38,bottom-.077,bottom+.067,CAP,tag+' sill')
        block(b,l,r,YARD+.10,YARD+.198,bottom+.067,top,SHADOW,tag+' timber backing')
        n=max(5,round((r-l)/.175))
        for j in range(n):
            xl=l+j*(r-l)/n+.004;xr=l+(j+1)*(r-l)/n-.004
            block(b,xl,xr,YARD+.055,YARD+.112,bottom+.069,top-.035,PALES[(j+j//3+i*3)%4],tag+' vertical boards')
        block(b,l,r,YARD+.03,YARD+.24,top-.041,top+.012,WOOD,tag+' top rail')
    left,right=limits();ground=float(np.mean([r[2]for r in rows]))
    # A narrow strip of pavement shows the boundary; the building is a street-side section.
    block(b,left,right,YARD-.93,.32,ground-.11,ground-.035,COURT,'North yard | visible paving to wall')
