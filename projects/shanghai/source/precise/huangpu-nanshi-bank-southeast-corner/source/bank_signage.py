"""Extruded traces of the gold vertical sign, medallion and 1783 date band."""
from pathlib import Path
import json
from shapely import constrained_delaunay_triangles
from shapely.geometry import shape,Point,Polygon,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.affinity import affine_transform,scale
from bank_finishes import GOLD,GOLD_EDGE,DARK_GOLD,OCHRE,BLACK
SOURCE=Path(__file__).parent
letters=json.loads((SOURCE/'street-name-relief.json').read_bytes())['characters']
def outline(geo,x,z,width,height):
    l,b,r,t=geo.bounds
    sx=width/(r-l);sz=height/(t-b)
    return affine_transform(geo,[sx,0,0,-sz,x-sx*(l+r)/2,z+sz*(b+t)/2])
def pieces(poly):
    return [poly] if poly.geom_type=='Polygon' else list(poly.geoms)
def smooth_gold(poly):
    fixed=[]
    for part in pieces(poly):
        if part.area<.0012:continue
        holes=[ring.coords for ring in part.interiors if Polygon(ring).area>=.0017]
        fixed.append(Polygon(part.exterior.coords,holes))
    return unary_union(fixed).buffer(.012,quad_segs=3).buffer(-.012,quad_segs=3)
def raised(f,poly,base,lod,label,fine=False):
    material=smooth_gold(poly).simplify(.010 if lod else .003,preserve_topology=True)
    if material.is_empty:return
    thickness=.036 if fine else .115
    bevel=.012 if fine else .033
    f.prism(material,base,base+thickness*.62,DARK_GOLD,label+'/cast-back')
    f.prism(material,base+thickness*.62,base+thickness,GOLD_EDGE,label+'/bronze-side')
    inside=material.buffer(-bevel,quad_segs=3)
    if inside.is_empty:
        f.prism(material,base+thickness,base+thickness+.006,GOLD,label+'/gilding');return
    region=material.difference(inside);boundary=material.boundary
    verts=[];faces=[]
    for part in pieces(region):
        for tri in constrained_delaunay_triangles(part).geoms:
            face=[]
            for u,z in list(orient(tri,sign=1).exterior.coords)[:3]:
                depth=base+thickness+.004+.022*min(1.,Point(u,z).distance(boundary)/bevel)
                face.append(len(verts));verts.append(f.point(u,z,depth))
            faces.append(face)
    f.builder.add(verts,faces,GOLD,f.label+'/'+label+'/rounded gold shoulder')
    f.prism(inside,base+thickness+.021,base+thickness+.026,GOLD,label+'/raised gilded face')

def date_number(digit):
    # Stroke paths were read from the enlarged 2015 numerals. Wires run over their top edge.
    strokes={
        '1':[[(.23,.82),(.48,.99),(.49,.06)],[(.24,.05),(.72,.05)]],
        '7':[[(.06,.91),(.22,.97),(.88,.96),(.68,.76),(.52,.45),(.43,.05)]],
        '8':[],
        '3':[[(.07,.84),(.26,.98),(.56,.98),(.82,.89),(.85,.76),(.70,.61),(.41,.53),(.62,.51),(.83,.40),(.87,.23),(.76,.08),(.48,.04),(.25,.07),(.08,.18)]]}
    if digit=='8':
        def oval(x,z,rx,ry):
            from shapely.affinity import scale
            return scale(Point(x,z).buffer(1,quad_segs=12),xfact=rx,yfact=ry,origin=(x,z))
        return unary_union([oval(.50,.72,.32,.245).boundary.buffer(.065),oval(.50,.30,.37,.25).boundary.buffer(.065)])
    return unary_union([LineString(path).buffer(.070,cap_style='round',join_style='round')for path in strokes[digit]])

def add(f,lod):
    for ch,z,width,height in [('童',12.07,1.32,1.46),('涵',10.32,1.41,1.42),('春',8.42,1.32,1.42),('堂',6.64,1.31,1.38)]:
        raw=shape(letters[ch]['pixel_geometry'])
        if ch=='春':
            bridges=[[(140,592),(136,604),(127,614)],[(161,592),(158,604),(154,612)],[(182,594),(194,606),(202,614)]]
            raw=unary_union([raw,*[LineString(v).buffer(3.0)for v in bridges]])
        poly=outline(raw,0,z,width,height)
        raised(f,poly,.255,lod,'vertical-name/'+ch)
    for radius,depth,thickness,mat,name in [(1.02,.07,.12,OCHRE,'outer-boss'),(.94,.19,.06,GOLD_EDGE,'patinated-rim'),(.82,.25,.04,BLACK,'enamel-disc')]:
        f.prism(Point(0,15.36).buffer(radius,quad_segs=11 if lod else 22),depth,depth+thickness,mat,'medallion/'+name)
    med=json.loads((SOURCE/'medallion-and-year.json').read_bytes())
    raised(f,outline(shape(med['medallion']),0,15.36,1.50,1.14),.29,lod,'medallion/photographed-monogram')
    for i,ch in enumerate('1783'):
        poly=outline(scale(date_number(ch),xfact=1,yfact=-1,origin=(0,0)),-.56+i*.37,14.03,.13 if ch=='1' else .205,.285)
        raised(f,poly,.185,lod,'founded-date/'+ch,fine=True)
