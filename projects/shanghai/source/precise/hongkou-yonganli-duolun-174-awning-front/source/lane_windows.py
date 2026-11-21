"""Recessed wood casements, ornamental sills and staggered stucco joints."""
import math
import numpy as np
from shapely.geometry import box,LineString
from fabric_canopies import IRON

STONE='Dressed grey sill'
SASH='Oxblood timber casements'
GLASS='Cool shopfront glass'
DARK='Interior timber and shade'
WARM='Reflected pale window'
RECESS='Moulding shadow'
PANEL='Pale relief render'


def framed_window(f,u,sill,width,height,central,lod):
    cut=box(u-width/2,sill,u+width/2,sill+height)
    trim=cut.buffer(.066,join_style=2).difference(cut)
    f.prism(trim,-.037,.040,STONE,'Dressed window surround')
    frame=cut.difference(cut.buffer(-.069,join_style=2))
    f.prism(frame,-.187,-.119,SASH,'Timber window jamb and head')
    # Each of the two timber leaves is divided into individual panes.
    clear_w=width-.138;clear_h=height-.138;bottom=sill+.069
    inner=clear_w/2
    for leaf in (-1,1):
        centre=u+leaf*clear_w/4
        angle=math.radians(26) if central and leaf==-1 else 0.
        hinge=centre-inner/2
        def pane(poly,back,front,mat,name):
            # A rigidly yawed opening leaf has its own real thickness and edges.
            if not angle:f.prism(box(centre+poly.bounds[0],poly.bounds[1],centre+poly.bounds[2],poly.bounds[3]),back,front,mat,name)
            else:
                xmin,zmin,xmax,zmax=poly.bounds
                vv=[]
                for d in (back,front):
                    for x,z in ((xmin,zmin),(xmax,zmin),(xmax,zmax),(xmin,zmax)):
                        dx=x+inner/2
                        vv.append(f.point(hinge+dx*math.cos(angle)-(d+.135)*math.sin(angle),z,
                                          -.135+dx*math.sin(angle)+(d+.135)*math.cos(angle)))
                f.builder.add(vv,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,f.label+'/'+name)
        for side in (-1,1):
            x=side*(inner-.052)/2;pane(box(x-.026,bottom,x+.026,bottom+clear_h),-.169,-.112,SASH,'Opening sash stiles')
        for zz in (bottom+.029,bottom+clear_h-.029,bottom+clear_h*.62):
            pane(box(-inner/2+.041,zz-.027,inner/2-.041,zz+.027),-.172,-.114,SASH,'Sash meeting rails')
        for z0,z1 in ((bottom+.05,bottom+clear_h*.62),(bottom+clear_h*.62,bottom+clear_h-.05)):
            pane(box(-inner*.5+.044,z0,inner*.5-.044,z1),-.176,-.168,WARM if leaf==1 and central else GLASS,'Glass within timber leaf')
        if not lod:
            for x in (-inner*.22,inner*.22):
                pane(box(x-.010,bottom+.047,x+.010,bottom+clear_h-.047),-.151,-.113,SASH,'Vertical glazing bars')
    if central:
        f.prism(cut.buffer(-.078,join_style=2),-.48,-.461,DARK,'Recess behind open casement')
    f.box(u,sill-.044,width+.205,.10,.22,.039,STONE,'Stepped window sill')
    return cut


def spandrel(f,u,z,width):
    x=width/2;h=.40
    line=[(-x,h),(-x,.12),(-x*.55,.12),(-x*.55,0),(x*.55,0),(x*.55,.12),(x,.12),(x,h)]
    strip=LineString([(u+a,z+b)for a,b in line]).buffer(.029,join_style=2,cap_style=2)
    f.prism(strip,.006,.041,PANEL,'Stepped spandrel moulding')
