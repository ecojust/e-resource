/** Loaded-owner street support and collision proxies. Coordinates are WGS84;
 * elevations are world metres from the street model's ground-zero datum.
 * No owner is active until its model hash matches and the scene enables it.
 */
const R = 6378137, RAD = Math.PI / 180, EPS = 1e-8, CELL = 32;
export const DEFAULT_GROUND_HEIGHT = .075;
const finite = Number.isFinite;
const validPoint = p => p && finite(p.lng) && finite(p.lat) && Math.abs(p.lng) <= 180 && Math.abs(p.lat) < 85;
const mercatorY = lat => Math.log(Math.tan(Math.PI / 4 + lat * RAD / 2));
function project(point, origin) {
  const scale = R * Math.cos(origin[1] * RAD);
  return [(point.lng - origin[0]) * RAD * scale, (mercatorY(point.lat) - mercatorY(origin[1])) * scale];
}
function interpolate(a, b, t) {
  return {lng:a.lng+(b.lng-a.lng)*t,
    lat:(2*Math.atan(Math.exp(mercatorY(a.lat)+(mercatorY(b.lat)-mercatorY(a.lat))*t))-Math.PI/2)/RAD};
}
const cross = (a, b) => a[0]*b[1]-a[1]*b[0];
const sub = (a, b) => [a[0]-b[0],a[1]-b[1]];
const mix = (a, b, t) => [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];
function pointSegmentSquared(p, a, b) {
  const dx=b[0]-a[0],dy=b[1]-a[1],length=dx*dx+dy*dy;
  const t=length?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)):0;
  return (p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2;
}
function intersectionParameters(a,b,c,d) {
  const r=sub(b,a),s=sub(d,c),q=sub(c,a),denom=cross(r,s);
  if(Math.abs(denom)>EPS) {
    const t=cross(q,s)/denom,u=cross(q,r)/denom;
    return t>=-EPS&&t<=1+EPS&&u>=-EPS&&u<=1+EPS?[Math.max(0,Math.min(1,t))]:[];
  }
  const length=r[0]**2+r[1]**2;
  if(!length||Math.abs(cross(q,r))>EPS)return [];
  return [c,d].map(p=>((p[0]-a[0])*r[0]+(p[1]-a[1])*r[1])/length).filter(t=>t>=0&&t<=1);
}
function segmentSquared(a,b,c,d) {
  if(intersectionParameters(a,b,c,d).length)return 0;
  return Math.min(pointSegmentSquared(a,c,d),pointSegmentSquared(b,c,d),pointSegmentSquared(c,a,b),pointSegmentSquared(d,a,b));
}
function inRing(point,ring) {
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const a=ring[j],b=ring[i];
    if(pointSegmentSquared(point,a,b)<=EPS*EPS)return true;
    if((a[1]>point[1])!==(b[1]>point[1])&&point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}
const inArea = (point,polygons) => polygons.some(rings=>inRing(point,rings[0])&&!rings.slice(1).some(ring=>inRing(point,ring)));
const boundsOverlap = (a,b) => a[0]<=b[2]&&a[2]>=b[0]&&a[1]<=b[3]&&a[3]>=b[1];
const pathBounds = (a,b,r=0) => [Math.min(a[0],b[0])-r,Math.min(a[1],b[1])-r,Math.max(a[0],b[0])+r,Math.max(a[1],b[1])+r];

function prepareFeature(feature,origin,ids) {
  const p=feature?.properties||{},id=p.id??feature?.id,g=feature?.geometry;
  if(typeof id!=='string'||!id||ids.has(id))throw Error('Missing or duplicate feature id');
  ids.add(id);
  if(!['walk-surface','obstacle'].includes(p.role))throw Error(`Unsupported role: ${id}`);
  const surface=p.role==='walk-surface';
  if(surface&&(!finite(p.height_world_m)||!['Polygon','MultiPolygon'].includes(g?.type)))throw Error(`Invalid flat surface: ${id}`);
  if(!surface&&(!finite(p.base_world_m)||!finite(p.top_world_m)||p.top_world_m<p.base_world_m||typeof p.blocks_walk!=='boolean'||typeof p.blocks_camera!=='boolean'))throw Error(`Invalid obstacle heights/flags: ${id}`);
  const point = coordinates => {
    const value={lng:coordinates?.[0],lat:coordinates?.[1]};
    if(!validPoint(value))throw Error(`Invalid WGS84 point: ${id}`);
    return project(value,origin);
  };
  const ring = coordinates => {
    if(!Array.isArray(coordinates)||coordinates.length<4)throw Error(`Invalid polygon ring: ${id}`);
    const result=coordinates.map(point);
    if(pointSegmentSquared(result[0],result.at(-1),result.at(-1))>EPS*EPS)throw Error(`Unclosed polygon ring: ${id}`);
    return result;
  };
  let polygons=[],lines=[],points=[];
  if(g?.type==='Polygon')polygons=[g.coordinates.map(ring)];
  else if(g?.type==='MultiPolygon')polygons=g.coordinates.map(polygon=>polygon.map(ring));
  else if(g?.type==='LineString')lines=[g.coordinates.map(point)];
  else if(g?.type==='MultiLineString')lines=g.coordinates.map(line=>line.map(point));
  else if(g?.type==='Point')points=[point(g.coordinates)];
  else throw Error(`Unsupported geometry: ${id}`);
  if(polygons.some(polygon=>!polygon.length)||lines.some(line=>line.length<2))throw Error(`Empty geometry: ${id}`);
  const radius=polygons.length?0:p.radius_m;
  if(!polygons.length&&(!finite(radius)||radius<=0))throw Error(`Point/line needs physical radius_m: ${id}`);
  const vertices=[...polygons.flat(2),...lines.flat(),...points];
  if(!vertices.length)throw Error(`Empty geometry: ${id}`);
  const bounds=vertices.reduce((b,v)=>[Math.min(b[0],v[0]-radius),Math.min(b[1],v[1]-radius),Math.max(b[2],v[0]+radius),Math.max(b[3],v[1]+radius)],[Infinity,Infinity,-Infinity,-Infinity]);
  const segments=[];
  for(const line of [...polygons.flat(),...lines])for(let i=1;i<line.length;i++)segments.push([line[i-1],line[i]]);
  return {id,properties:p,surface,polygons,points,segments,radius,bounds};
}

/** Same-origin furniture generator primitives, local X east/Y up/Z south.
 * Frusta use their maximum analytic radius, cylinders conservative round caps,
 * and rotated ellipsoids their tight axis-aligned box. These are explicit
 * collision proxies, not claims that the visual meshes are solid boxes.
 */
function prepareLocalObstacle(primitive,ids) {
  const {id,type}=primitive;
  if(typeof id!=='string'||!id||ids.has(id))throw Error('Missing or duplicate local obstacle id');
  ids.add(id);
  const vector=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(finite);
  let polygons=[],points=[],segments=[],radius=0,base,top,bounds,axis=null;
  const box=(center,size)=>{
    if(!vector(center,3)||!vector(size,3)||size.some(v=>v<=0))throw Error(`Invalid box: ${id}`);
    const x=center[0],north=-center[2],hx=size[0]/2,hn=size[2]/2;
    polygons=[[[[x-hx,north-hn],[x+hx,north-hn],[x+hx,north+hn],[x-hx,north+hn],[x-hx,north-hn]]]];
    base=center[1]-size[1]/2;top=center[1]+size[1]/2;bounds=[x-hx,north-hn,x+hx,north+hn];
  };
  if(type==='box')box(primitive.center,primitive.size);
  else if(type==='ellipsoid') {
    if(!vector(primitive.center,3)||!vector(primitive.radii,3)||primitive.radii.some(v=>v<=0))throw Error(`Invalid ellipsoid: ${id}`);
    const angle=primitive.rotation_z_radians??0;
    if(!finite(angle))throw Error(`Invalid ellipsoid rotation: ${id}`);
    const [rx,ry,rz]=primitive.radii,c=Math.cos(angle),s=Math.sin(angle);
    box(primitive.center,[2*Math.hypot(rx*c,ry*s),2*Math.hypot(rx*s,ry*c),2*rz]);
  } else if(type==='vertical_frustum') {
    if(!vector(primitive.center_xz,2)||![primitive.bottom,primitive.top,primitive.bottom_radius,primitive.top_radius].every(finite))throw Error(`Invalid frustum: ${id}`);
    radius=Math.max(primitive.bottom_radius,primitive.top_radius);
    if(radius<=0||Math.min(primitive.bottom_radius,primitive.top_radius)<0)throw Error(`Invalid frustum radius: ${id}`);
    points=[[primitive.center_xz[0],-primitive.center_xz[1]]];base=primitive.bottom;top=primitive.top;
    bounds=pathBounds(points[0],points[0],radius);
  } else if(type==='cylinder_segment') {
    if(!vector(primitive.a,3)||!vector(primitive.b,3)||!finite(primitive.radius)||primitive.radius<=0)throw Error(`Invalid cylinder: ${id}`);
    radius=primitive.radius;axis=[primitive.a,primitive.b];
    segments=[[[primitive.a[0],-primitive.a[2]],[primitive.b[0],-primitive.b[2]]]];
    base=Math.min(primitive.a[1],primitive.b[1])-radius;top=Math.max(primitive.a[1],primitive.b[1])+radius;
    bounds=pathBounds(...segments[0],radius);
  } else throw Error(`Unsupported local obstacle: ${id}`);
  if(top<base)throw Error(`Inverted local obstacle: ${id}`);
  for(const ring of polygons.flat())for(let i=1;i<ring.length;i++)segments.push([ring[i-1],ring[i]]);
  const properties={role:'obstacle',kind:primitive.kind||type,base_world_m:base,top_world_m:top,
    blocks_walk:primitive.blocks_walk!==false,blocks_camera:primitive.blocks_camera!==false};
  return {id,properties,surface:false,polygons,points,segments,radius,bounds,axis};
}

function makeIndex(features) {
  const cells=new Map(),large=[];
  for(const feature of features) {
    const b=feature.bounds,loX=Math.floor(b[0]/CELL),hiX=Math.floor(b[2]/CELL),loY=Math.floor(b[1]/CELL),hiY=Math.floor(b[3]/CELL);
    if((hiX-loX+1)*(hiY-loY+1)>512){large.push(feature);continue;}
    for(let x=loX;x<=hiX;x++)for(let y=loY;y<=hiY;y++) {
      const key=`${x}:${y}`;
      if(!cells.has(key))cells.set(key,[]);
      cells.get(key).push(feature);
    }
  }
  return bounds=>{
    const cellCount=(Math.floor(bounds[2]/CELL)-Math.floor(bounds[0]/CELL)+1)*(Math.floor(bounds[3]/CELL)-Math.floor(bounds[1]/CELL)+1);
    if(cellCount>512)return features.filter(feature=>boundsOverlap(feature.bounds,bounds));
    const found=new Set(large);
    for(let x=Math.floor(bounds[0]/CELL);x<=Math.floor(bounds[2]/CELL);x++)for(let y=Math.floor(bounds[1]/CELL);y<=Math.floor(bounds[3]/CELL);y++) {
      for(const feature of cells.get(`${x}:${y}`)||[])found.add(feature);
    }
    return [...found].filter(feature=>boundsOverlap(feature.bounds,bounds));
  };
}

function geometryHit(a,b,radius,feature) {
  if(feature.polygons.length&&(inArea(a,feature.polygons)||inArea(b,feature.polygons)))return true;
  const squared=(radius+feature.radius)**2+EPS*EPS;
  return feature.segments.some(([c,d])=>segmentSquared(a,b,c,d)<=squared)||feature.points.some(point=>pointSegmentSquared(point,a,b)<=squared);
}

function verticalInterval(from,to,low,high) {
  if(Math.abs(to-from)<EPS)return from>=low&&from<=high?[0,1]:null;
  const values=[(low-from)/(to-from),(high-from)/(to-from)].sort((a,b)=>a-b);
  const lo=Math.max(0,values[0]),hi=Math.min(1,values[1]);
  return lo<=hi?[lo,hi]:null;
}

export class StreetInteraction {
  constructor({fallbackHeight=DEFAULT_GROUND_HEIGHT,maxStepHeight=.2}={}) {
    this.fallbackHeight=fallbackHeight;this.maxStepHeight=maxStepHeight;
    this.owners=new Map();this.revision=0;this.lastError=null;
  }
  /** modelSha256 is the loaded asset's verified/configured SHA, not a URL. */
  setOwner(ownerId,geojson,{modelSha256,active=false}={}) {
    try {
      const metadata=geojson?.metadata||geojson;
      if(geojson?.type!=='FeatureCollection'||metadata.schema_version!==1||metadata.owner!==ownerId)throw Error('Sidecar schema/owner mismatch');
      if(!/^[a-f0-9]{64}$/i.test(modelSha256||'')||![metadata.web_model_sha256,metadata.raw_model_sha256].includes(modelSha256))throw Error('Sidecar/model SHA mismatch');
      const origin=metadata.origin;
      if(!Array.isArray(origin)||!validPoint({lng:origin[0],lat:origin[1]}))throw Error('Invalid sidecar origin');
      if(!Array.isArray(geojson.features))throw Error('Missing sidecar features');
      const ids=new Set(),features=geojson.features.map(feature=>prepareFeature(feature,origin,ids));
      if(geojson.local_obstacles!==undefined&&!Array.isArray(geojson.local_obstacles))throw Error('Invalid local obstacles');
      for(const primitive of geojson.local_obstacles||[])features.push(prepareLocalObstacle(primitive,ids));
      this.owners.set(ownerId,{id:ownerId,origin,features,query:makeIndex(features),active:Boolean(active),modelSha256});
      this.lastError=null;this.revision++;return true;
    } catch(error) {
      this.owners.delete(ownerId);this.lastError={ownerId,message:error.message};this.revision++;return false;
    }
  }
  setOwnerActive(ownerId,active) {
    const owner=this.owners.get(ownerId);
    if(!owner)return false;
    if(owner.active!==Boolean(active)){owner.active=Boolean(active);this.revision++;}
    return true;
  }
  removeOwner(ownerId) {if(this.owners.delete(ownerId))this.revision++;}
  clear() {this.owners.clear();this.revision++;}
  groundAt(lng,lat) {
    const geographic={lng,lat};if(!validPoint(geographic))return null;
    let found=null;
    for(const owner of this.owners.values())if(owner.active) {
      const point=project(geographic,owner.origin);
      for(const feature of owner.query(pathBounds(point,point))) {
        if(feature.surface&&inArea(point,feature.polygons)&&(!found||feature.properties.height_world_m>found.height)) {
          found={height:feature.properties.height_world_m,id:feature.id,ownerId:owner.id};
        }
      }
    }
    return found;
  }
  _stepHit(from,to,groundHeight,maxStepHeight) {
    const times=new Set([0,1]);
    for(const owner of this.owners.values())if(owner.active) {
      const a=project(from,owner.origin),b=project(to,owner.origin);
      for(const feature of owner.query(pathBounds(a,b)))if(feature.surface) {
        for(const [c,d]of feature.segments)for(const t of intersectionParameters(a,b,c,d))times.add(t);
      }
    }
    const sorted=[...times].sort((a,b)=>a-b),samples=[];
    for(let i=1;i<sorted.length;i++)if(sorted[i]-sorted[i-1]>1e-9)samples.push((sorted[i]+sorted[i-1])/2);
    samples.push(1);let previous=groundHeight;
    for(const t of samples) {
      const p=interpolate(from,to,t),sample=this.groundAt(p.lng,p.lat),height=sample?.height??this.fallbackHeight;
      if(Math.abs(height-previous)>maxStepHeight+1e-7)return {blocked:true,type:'street-step',id:sample?.id??null,ownerId:sample?.ownerId??null,fromHeight:previous,toHeight:height};
      previous=height;
    }
    return null;
  }
  sweep(from,to,{radius=.38,groundHeight,height=1.75,maxStepHeight=this.maxStepHeight}={}) {
    if(!validPoint(from)||!validPoint(to)||!finite(radius)||radius<0)return null;
    const startHeight=finite(groundHeight)?groundHeight:(this.groundAt(from.lng,from.lat)?.height??this.fallbackHeight);
    const endHeight=this.groundAt(to.lng,to.lat)?.height??this.fallbackHeight;
    const step=this._stepHit(from,to,startHeight,maxStepHeight);
    if(step)return step;
    return this._obstacleHit(from,to,radius,startHeight,endHeight,height,false);
  }
  cameraCollision(from,to,{radius=.12}={}) {
    if(!validPoint(from)||!validPoint(to)||!finite(from.alt)||!finite(to.alt)||!finite(radius)||radius<0)return null;
    return this._obstacleHit(from,to,radius,from.alt,to.alt,0,true);
  }
  _obstacleHit(from,to,radius,fromHeight,toHeight,bodyHeight,camera) {
    for(const owner of this.owners.values())if(owner.active) {
      const a=project(from,owner.origin),b=project(to,owner.origin);
      for(const feature of owner.query(pathBounds(a,b,radius))) {
        const p=feature.properties;
        if(feature.surface||!(camera?p.blocks_camera:p.blocks_walk))continue;
        const interval=verticalInterval(fromHeight,toHeight,p.base_world_m-bodyHeight-(camera?radius:0),p.top_world_m+(camera?radius:0));
        if(!interval)continue;
        let proxy=feature;
        if(feature.axis&&!camera) {
          // Trim sloped furniture segments to the avatar's actual vertical band;
          // a lamp arm above the head must not block the pavement below it.
          const clipped=verticalInterval(feature.axis[0][1],feature.axis[1][1],Math.min(fromHeight,toHeight)-feature.radius,Math.max(fromHeight,toHeight)+bodyHeight+feature.radius);
          if(!clipped)continue;
          proxy={...feature,segments:[[mix(feature.segments[0][0],feature.segments[0][1],clipped[0]),mix(feature.segments[0][0],feature.segments[0][1],clipped[1])]]};
        }
        if(geometryHit(mix(a,b,interval[0]),mix(a,b,interval[1]),radius,proxy))return {blocked:true,type:'street-obstacle',kind:p.kind||'fixture',id:feature.id,ownerId:owner.id};
      }
    }
    return null;
  }
  getState() {
    const owners=[...this.owners.values()];
    return {revision:this.revision,owners:owners.length,activeOwners:owners.filter(o=>o.active).length,
      surfaces:owners.filter(o=>o.active).reduce((n,o)=>n+o.features.filter(f=>f.surface).length,0),
      obstacles:owners.filter(o=>o.active).reduce((n,o)=>n+o.features.filter(f=>!f.surface).length,0),lastError:this.lastError};
  }
}
