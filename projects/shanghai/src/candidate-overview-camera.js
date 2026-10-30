const DEG=Math.PI/180,EARTH=6371008.8;
// MapLibre jumpTo passes padding directly to its transform; unlike fitBounds,
// numeric zero does not clear a previous asymmetric padding object.
export const OVERVIEW_CAMERA_RESET={elevation:0,padding:{top:0,bottom:0,left:0,right:0}};

/** Fit the delivered GLB's eight corners, including height, into the free map
 * viewport. Coordinates and camera elevation are display parameters only. */
export function candidateOverviewCamera(place,{width,height,insets={}}){
  if(!place.city_integration)return null;
  const bounds=place.bounds_glb;
  if(!bounds?.min?.every(Number.isFinite)||!bounds?.max?.every(Number.isFinite))return null;
  const padding={left:Math.max(0,insets.left||0),right:Math.max(0,insets.right||0),top:Math.max(0,insets.top||0),bottom:Math.max(0,insets.bottom||0)};
  const availableWidth=Math.max(80,width-padding.left-padding.right),availableHeight=Math.max(80,height-padding.top-padding.bottom);
  const scale=place.scale||1,angle=(place.heading||0)*DEG,c=Math.cos(angle),s=Math.sin(angle),points=[];
  for(const x of [bounds.min[0],bounds.max[0]])for(const y of [bounds.min[1],bounds.max[1]])for(const z of [bounds.min[2],bounds.max[2]])
    points.push([(c*x-s*z)*scale,(-s*x-c*z)*scale,y*scale+(place.altitude||0)]);
  const midpoint=[0,1,2].map(axis=>(Math.min(...points.map(p=>p[axis]))+Math.max(...points.map(p=>p[axis])))/2);
  const bearing=place.overviewBearing??place.navigation?.bearing??place.bearing??35;
  // Near-vertical views expose the narrow courtyard and low pool behind the
  // preserved surrounding source buildings without changing their geometry.
  const pitch=place.overviewPitch??(place.id==='hongkou-luxun-residence-facade'?16:place.id==='chongming-pan-pool-bridge'?20:place.id==='huangpu-grand-theatre'?25:50);
  const b=bearing*DEG,p=pitch*DEG,sb=Math.sin(b),cb=Math.cos(b),sp=Math.sin(p),cp=Math.cos(p);
  const focal=height/(2*Math.tan(36.87*DEG/2)),tanX=availableWidth/(2*focal),tanY=availableHeight/(2*focal);
  let distance=20;
  for(const point of points){
    const [east,north,up]=point.map((v,i)=>v-midpoint[i]);
    const horizontal=east*cb-north*sb,vertical=(east*sb+north*cb)*cp+up*sp,depth=(east*sb+north*cb)*sp-up*cp;
    // A 15% interior margin also leaves room for roof ornaments and antialiasing.
    distance=Math.max(distance,Math.abs(horizontal)*1.15/tanX-depth,Math.abs(vertical)*1.15/tanY-depth,-depth+2);
  }
  const lat=place.lat+midpoint[1]/EARTH/DEG,lng=place.lng+midpoint[0]/(EARTH*Math.cos(place.lat*DEG))/DEG;
  const zoom=Math.max(8,Math.min(24,Math.log2(focal*2*Math.PI*EARTH*Math.cos(lat*DEG)/(512*distance))));
  return {center:[lng,lat],elevation:midpoint[2],zoom,bearing,pitch,padding};
}
