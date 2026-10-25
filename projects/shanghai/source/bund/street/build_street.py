"""Bund pavement/curbs/crossings and photo-proportioned waterside fittings.
Public OSM positions; dimensions and fitting spacing are reconstruction estimates.
No facade imagery is used as a texture. GLB has local metres, X east/Y up/Z south.
"""
from pathlib import Path
import sys,json,math,struct,subprocess
import numpy as np
from shapely.geometry import shape,LineString,Polygon,box,Point
from shapely.ops import transform,unary_union
ROOT=Path(__file__).parent
PROJECT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'source/city'))
from build_district_models import Mesh,local_coordinates
ORIGIN=(121.4862,31.2385)
local=lambda x,y,z=None:local_coordinates(x,y,ORIGIN)
def metric(g):return transform(local,g)
COLORS={'BundStonePaving':(.39,.40,.37,1),'BundGraniteCurb':(.48,.49,.46,1),'BundRoadPaint':(.82,.83,.76,1),'BundRoadSurface':(.22,.25,.25,1),'BundRailingSteel':(.12,.14,.14,1),'BundLampSilver':(.34,.36,.35,1),'BundLampGlass':(.80,.84,.76,1)}
M={name:Mesh() for name in COLORS}
def face(mesh,points):
 p=np.asarray(points,float);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<1e-10:return
 start=mesh.vertices([tuple(v) for v in p],tuple(n/length))
 for i in range(1,len(points)-1):mesh.indices.extend([start,start+i,start+i+1])
def cuboid(name,center,size):
 x,y,z=center;a,b,c=[v/2 for v in size]
 verts=[(x+aa*a,y+bb*b,z+cc*c) for aa,bb,cc in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face(M[name],[verts[i] for i in inds])
def rod(name,start,end,radius,segments=10):
 a,b=np.array(start,float),np.array(end,float);n=b-a;n/=np.linalg.norm(n)
 u=np.cross(n,[0,1,0])
 if np.linalg.norm(u)<.01:u=np.array([1.,0.,0.])
 u/=np.linalg.norm(u);v=np.cross(n,u)
 rings=[[p+radius*(math.cos(i*math.tau/segments)*u+math.sin(i*math.tau/segments)*v) for i in range(segments)] for p in [a,b]]
 face(M[name],list(reversed(rings[0])));face(M[name],rings[1])
 for i in range(segments):j=(i+1)%segments;face(M[name],[rings[0][i],rings[0][j],rings[1][j],rings[1][i]])
def polygons(g):
 if g.is_empty:return []
 return [g] if g.geom_type=='Polygon' else [p for part in g.geoms for p in polygons(part)] if hasattr(g,'geoms') else []
def lines(g):
 if g.is_empty:return []
 return [g] if g.geom_type=='LineString' else [p for part in g.geoms for p in lines(part)] if hasattr(g,'geoms') else []
def solid(name,g,z0,z1):
 mesh=M[name]
 for poly in polygons(g):
  rings=[list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]
  mesh.polygon(rings,z0,z1,mesh)
def vector_at(line,d):
 a=np.array(line.interpolate(max(0,d-.1)).coords[0]);b=np.array(line.interpolate(min(line.length,d+.1)).coords[0]);t=b-a;t/=np.linalg.norm(t);return t,np.array([-t[1],t[0]])
def lamp(x,z,road=False):
 material='BundRailingSteel' if road else 'BundLampSilver';height=5.6 if road else 4.3
 cuboid('BundGraniteCurb',(x,.15,z),(.35,.30,.35));rod(material,(x,.25,z),(x,height,z),.065,12)
 if road:
  pts=[(x,height-.55,z),(x+.15,height-.10,z),(x+.6,height+.15,z),(x+1.45,height+.25,z)]
  for a,b in zip(pts,pts[1:]):rod(material,a,b,.05,10)
  cuboid(material,(x+1.55,height+.22,z),(1.05,.13,.30));cuboid('BundLampGlass',(x+1.55,height+.145,z),(.84,.025,.23))
 else:
  rod(material,(x,height-.15,z),(x,height+.57,z),.17,16)
  rod('BundLampGlass',(x,height-.09,z),(x,height+.48,z),.14,16)
  # Four visible cage ribs and a shallow mushroom cap, as in the modern photo.
  for a in [0,math.pi/2,math.pi,math.pi*1.5]:
   dx,dz=.165*math.cos(a),.165*math.sin(a);rod(material,(x+dx,height-.15,z+dz),(x+dx,height+.55,z+dz),.016,6)
  rod(material,(x,height+.54,z),(x,height+.62,z),.24,16)

osm=json.loads((ROOT/'osm-street.json').read_text())['elements'];by_id={e['id']:e for e in osm}
ways={e['id']:metric(LineString([(p['lon'],p['lat']) for p in e['geometry']])) for e in osm if 'geometry' in e}
crop=metric(box(121.4842,31.23545,121.4892,31.2419))
sidewalk=ways[178412507].intersection(crop)
source_candidates=json.loads((ROOT.parent/'bund-candidates.json').read_text())['candidates']
buildings=unary_union([metric(shape(c['geometry'])) for c in source_candidates]).buffer(.08)
crossings=[]
for e in osm:
 if e.get('tags',{}).get('footway')!='crossing' or e['id'] not in ways:continue
 line=ways[e['id']].intersection(crop)
 for l in lines(line):
  if 5<l.length<70 and l.distance(sidewalk)<5:crossings.append((e['id'],l))
walk_surface=sidewalk.buffer(2.0,cap_style=2,join_style=2).difference(buildings)
solid('BundStonePaving',walk_surface,0,.075)
crossing_cuts=unary_union([line.buffer(2.15) for _,line in crossings])
for line in lines(sidewalk):
 _,n=vector_at(line,line.length/2);sign=1 if n[0]>0 else -1
 curb=line.offset_curve(sign*1.95,join_style=2).buffer(.105,cap_style=2).difference(crossing_cuts)
 solid('BundGraniteCurb',curb,0,.14)
for _,line in crossings:
 # The source path is the crossing axis, not an invented road grid.
 start,end=1.8,line.length-1.8
 if end<=start:continue
 path=LineString([line.interpolate(d).coords[0] for d in np.linspace(start,end,20)])
 solid('BundRoadSurface',path.buffer(1.9,cap_style=2),.004,.008)
 for d in np.arange(start+.25,end-.25,1.15):
  p=np.array(line.interpolate(d).coords[0]);t,n=vector_at(line,d)
  stripe=Polygon([p-t*.24-n*1.75,p+t*.24-n*1.75,p+t*.24+n*1.75,p-t*.24+n*1.75])
  solid('BundRoadPaint',stripe,.012,.018)
 # Street-side endpoint is mapped; the small lamp offset and form are inferred.
 ends=[Point(line.coords[0]),Point(line.coords[-1])];point=min(ends,key=lambda p:p.distance(sidewalk))
 x,z=sidewalk.interpolate(sidewalk.project(point)).coords[0];lamp(x+1.65,z+2.8,road=True)

map_features=json.loads((ROOT/'bund-map.geojson').read_text())['features']
water=unary_union([metric(shape(f['geometry'])) for f in map_features if f['properties']['layer']=='water' and f['geometry']['type'] in ['Polygon','MultiPolygon']])
shorelines=[l for l in lines(water.boundary.intersection(crop)) if l.length>100]
shore=max(shorelines,key=lambda l:l.length)
t,n=vector_at(shore,shore.length/2);mid=np.array(shore.interpolate(shore.length/2).coords[0]);land_side=1 if not water.contains(Point(mid+n)) else -1
rail=shore.offset_curve(land_side*.8,join_style=2)
rail=max(lines(rail),key=lambda l:l.length)
# Pavement between two mapped references. Its exact construction edge/altitude
# is not surveyed; it stays close to the existing map's level for walk controls.
inner=ways[909084827].intersection(crop);inner=max(lines(inner),key=lambda l:l.length)
a=list(rail.coords);b=list(inner.coords)
if a[0][1]>a[-1][1]:a.reverse()
if b[0][1]<b[-1][1]:b.reverse()
promenade=Polygon(a+b).buffer(0).difference(water).difference(buildings)
solid('BundStonePaving',promenade,.005,.035)
post_count=0;lamps=0
for d0 in np.arange(0,rail.length,8.0):
 d1=min(d0+8.0,rail.length)
 p=np.array(rail.interpolate(d0).coords[0]);t,n=vector_at(rail,d0+.01)
 # Keep the leaning top toward water; OSM geometry determines the side.
 toward_water=n if water.contains(Point(p+n*2)) else -n
 cuboid('BundGraniteCurb',(p[0],.51,p[1]),(.43,1.02,.43));post_count+=1
 for h,radius in [(.29,.022),(.52,.022),(.76,.022),(1.08,.055)]:
  pa=np.array(rail.interpolate(d0).coords[0])+toward_water*(h/1.08*.24)
  pb=np.array(rail.interpolate(d1).coords[0])+toward_water*(h/1.08*.24)
  rod('BundRailingSteel',(pa[0],h,pa[1]),(pb[0],h,pb[1]),radius,8)
 for d in np.arange(d0+.9,d1,.95):
  p=np.array(rail.interpolate(d).coords[0]);top=p+toward_water*.24
  rod('BundRailingSteel',(p[0],.12,p[1]),(top[0],1.08,top[1]),.035,8)
 if round(d0)%32==0:
  p=p-toward_water*.75;lamp(p[0],p[1]);lamps+=1

# Pack one primitive per material; no external texture or buffer dependency.
binary=bytearray();views=[];accessors=[];primitives=[];materials=[]
def append(data,target,component,type_,count,minimum=None,maximum=None):
 while len(binary)%4:binary.append(0)
 offset=len(binary);binary.extend(data);view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data),'target':target})
 a={'bufferView':view,'componentType':component,'count':count,'type':type_}
 if minimum is not None:a['min']=minimum;a['max']=maximum
 accessors.append(a);return len(accessors)-1
triangles=0
for name,mesh in M.items():
 if not mesh.indices:continue
 v=np.asarray(mesh.positions,dtype='<f4');n=np.asarray(mesh.normals,dtype='<f4');idx=np.asarray(mesh.indices,dtype='<u4')
 vi=append(v.tobytes(),34962,5126,'VEC3',len(v),v.min(axis=0).tolist(),v.max(axis=0).tolist());ni=append(n.tobytes(),34962,5126,'VEC3',len(n));ii=append(idx.tobytes(),34963,5125,'SCALAR',len(idx))
 mi=len(materials);materials.append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':COLORS[name],'metallicFactor':.45 if 'Steel' in name or 'Silver' in name else .02,'roughnessFactor':.35 if 'Glass' in name else .72}})
 primitives.append({'attributes':{'POSITION':vi,'NORMAL':ni},'indices':ii,'material':mi});triangles+=len(idx)//3
gltf={'asset':{'version':'2.0','generator':'Shanghai Bund street reconstruction v3'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'Bund mapped public streetscape','mesh':0}],'meshes':[{'primitives':primitives}],'materials':materials,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
j=json.dumps(gltf,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
output=ROOT/'bund-streets.glb';output.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
metadata={'id':'bund-streets','anchor':list(ORIGIN),'units':'metres, X east / Y up / Z south','triangles':triangles,'bytes':output.stat().st_size,'mapped_sidewalk_way':178412507,'mapped_inner_promenade_way':909084827,'mapped_crossing_ways':[i for i,_ in crossings],'shoreline_source':'bund-map.geojson / OSM water via OpenFreeMap','railing_length_m':round(rail.length,3),'granite_posts':post_count,'promenade_lamps':lamps,'dimensions_are_estimates':{'sidewalk_width_m':4.0,'curb_height_m':.14,'handrail_height_m':1.08,'lamp_spacing_m':32,'crossing_paint_width_m':3.5},'accuracy':'Mapped path/shoreline positions. Pavement width, construction heights, rail/lamp shape and spacing are photo-proportioned reconstruction, not a survey; current game ground level is retained.','reference':'Modern wide-granite promenade photo in promenade-photo-search.json (Bund Promenade panoramio, CC BY 3.0); older Promenade du Bund photograph was inspected only to distinguish former fittings.','license':'ODbL-1.0 derived street database; original fitting meshes/code MIT; reference photograph licensing retained separately.'}
(ROOT/'bund-streets.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));assert output.stat().st_size<100_000_000;print(json.dumps(metadata,ensure_ascii=False))
