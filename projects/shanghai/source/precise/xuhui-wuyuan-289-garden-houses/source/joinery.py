"""Recessed casements, brick arches and house-number plates on the photographed lane front."""
import math
from shapely.geometry import Polygon,box
from materials import *
def segmental(center,width,bottom,spring,rise):
    """Circular segment, tangent to the rising arch at the observed springings."""
    half=width/2
    r=(half**2+rise**2)/(2*rise)
    zc=spring+rise-r
    arc=[(center+half*(1-i/8),zc+math.sqrt(max(0,r*r-(half*(1-i/8))**2)))for i in range(17)]
    return Polygon([(center-half,bottom),(center+half,bottom),*arc])
def window(f,left,right,bottom,top,front,cols,rows,label,lod=False,brick_sill=True):
    edge=.052;width=right-left;h=top-bottom
    f.rect(left+.008,right-.008,bottom+.008,top-.008,front-.239,front-.226,GLASS,label+' inset glass')
    ring=box(left,bottom,right,top).difference(box(left+edge,bottom+edge,right-edge,top-edge))
    f.solid(ring,front-.224,front-.118,SASH,label+' recessed casement surround')
    for j in range(1,cols):
        x=left+width*j/cols;w=.035 if j*2==cols else .019
        f.rect(x-w/2,x+w/2,bottom+edge,top-edge,front-.219,front-.149,SASH,label+' glazing bar')
    for j in range(1,rows):
        z=bottom+h*j/rows
        f.rect(left+edge,right-edge,z-.010,z+.010,front-.215,front-.157,SASH,label+' glazing bar')
    if brick_sill:f.rect(left-.05,right+.055,bottom-.071,bottom-.010,front-.12,front+.077,SILL,label+' sloping red brick sill')
def door(f,center,width,bottom,spring,rise,front,label,lod=False):
    hole=segmental(center,width,bottom,spring,rise)
    f.solid(hole,front-.372,front-.345,DARK,label+' arch recess')
    surround=hole.difference(hole.buffer(-.062,join_style=2))
    f.solid(surround,front-.34,front-.235,OAK,label+' lintel and jamb lining')
    half=width/2
    f.rect(center-half+.078,center+half-.078,bottom+.061,spring-.04,front-.34,front-.305,DOOR,label+' inset entrance leaf')
    for a,b in [(.15,.84),(1.01,1.69)]:
        if bottom+b<spring-.06:
            inset=box(center-half+.15,bottom+a,center+half-.15,bottom+b)
            f.solid(inset.difference(inset.buffer(-.026,join_style=2)),front-.304,front-.29,OAK,label+' moulded panel')
    f.rect(center+half-.159,center+half-.116,bottom+.93,bottom+1.035,front-.289,front-.25,IRON,label+' handle')
    # Segmental header is laid radially. A narrow joint separates adjacent voussoirs.
    upper=segmental(center,width+.32,bottom,spring+.035,rise+.12)
    zone=upper.difference(hole).intersection(box(center-half-.18,spring-.025,center+half+.18,spring+rise+.17))
    f.solid(zone,front+.003,front+.022,SILL,label+' segmental brick head')
    if not lod:
        for i in range(11):
            x=center+(i/10-.5)*(width+.12)
            f.band([(x,spring-.04),(x+.32*(x-center),spring+rise+.23)],.009,front+.023,front+.025,CREAM,label+' arch joints',zone)
def plaque(f,cx,cz,num,front,scale=1):
    w=.205*scale;h=.155*scale
    f.rect(cx-w/2,cx+w/2,cz-h/2,cz+h/2,front,front+.012,BOARD,'number '+str(num)+' green enamel address plate')
    if num==1: path=[(-.26,.38),(-.02,.65),(-.02,-.61)]
    elif num==2:path=[(-.42,.42),(-.22,.64),(.24,.64),(.4,.39),(.31,.12),(-.4,-.57),(.41,-.57)]
    elif num==4:
        path=[(.24,-.60),(.24,.66),(-.43,-.10),(.44,-.10)]
    else:return
    f.band([(cx+x*h*.42,cz+y*h*.46)for x,y in path],.009*scale,front+.0125,front+.015,LETTER,'enamel numeral '+str(num))
