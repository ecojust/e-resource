"""The open lawn-side parapet with turned balusters, square dies and projecting deck."""
import numpy as np

DECK='Balcony warm grey coping'
STONE='Baluster limestone colour'
TRIM='Whitened plaster band'
GROOVE='Gable recessed moulding'

def add_balcony(builder,d,left,right,lod):
    projection=d['balcony_projection']
    top=d['deck_top_z'];rail=d['rail_top_z'];y=-projection+.10
    mid=(right+left)/2
    for name,z0,z1,edge,material in [
        ('underside',d['bottom'],top-.16,.01,GROOVE),('fascia',top-.16,top-.096,.09,STONE),
        ('shadow bed',top-.096,top-.06,.110,GROOVE),('overhanging lip',top-.06,top,.14,DECK)]:
        builder.box((mid,(-projection-edge+.25)/2,(z0+z1)/2),
                    (right-left+2*edge,projection+edge+.25,z1-z0),material,label='Deck/'+name)
    # The cluster at the left end is screened by foliage. Continue the visible
    # rail interval only as far as the cut, with the two outer end dies.
    dies=[left+.18,-2.16,2.02,right-.18]
    for n,x in enumerate(dies):
        for name,za,zb,width,depth,material in [
          ('foot',top,top+.10,.53,.43,DECK),('socle',top+.10,top+.18,.46,.39,STONE),
          ('square die',top+.18,rail+.04,.43,.38,STONE),('shadow collar',rail+.04,rail+.075,.48,.40,GROOVE),
          ('cap',rail+.075,rail+.145,.56,.44,DECK)]:
            builder.box((x,y,(za+zb)/2),(width,depth,zb-za),material,label=f'Parapet {n+1}/{name}')
    for n,(a,b) in enumerate(zip(dies,dies[1:])):
        clear=b-a-.43;cx=(a+b)/2
        for name,za,zb,depth,mat in [('plinth',top,top+.085,.24,STONE),('plinth bead',top+.085,top+.126,.265,DECK),
                      ('neck bed',rail-.127,rail-.091,.212,STONE),('handrail fascia',rail-.091,rail-.04,.258,STONE),('cap',rail-.04,rail,.29,DECK)]:
            builder.box((cx,y,(za+zb)/2),(clear,depth,zb-za),mat,label=f'Rail {n+1}/{name}')
        count=max(3,round(clear/.28))
        z0=top+.126;z1=rail-.127
        shape=[(0,.082),(.07,.082),(.12,.065),(.18,.055),(.27,.07),(.40,.085),(.53,.083),
               (.64,.069),(.76,.046),(.85,.047),(.90,.064),(.94,.072),(1.,.072)]
        if lod:shape=[shape[i]for i in [0,1,3,5,7,8,10,12]]
        profile=[(z0+z*(z1-z0),r)for z,r in shape]
        for k in range(count):
            x=a+.215+clear*(k+.5)/count
            builder.lathe((x,y),profile,STONE,8 if lod else 14,label=f'Rail {n+1}/turned balusters')
    for n,x in enumerate([dies[0],dies[-1]]):
        builder.box((x,(y+.02)/2,rail-.055),(.24,.02-y,.11),DECK,label=f'Balcony side {n+1}/return coping')
        start,end=y+.19,-.06
        if end<=start:continue
        for k in range(3):
            yy=start+(end-start)*(k+.5)/3
            builder.lathe((x,yy),[(top+.08,.075),(top+.22,.054),(top+.35,.081),(rail-.24,.046),(rail-.108,.07)],
                          STONE,7 if lod else 12,label=f'Balcony side {n+1}/balusters')
        builder.box((x,(start+end)/2,top+.05),(.20,end-start,.10),STONE,label=f'Balcony side {n+1}/curb')
