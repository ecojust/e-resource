/**
 * Small static traffic illustration on verified OSM Bund carriageways.
 * No animation loop, lights, external textures, live feed or random placement.
 * geographicPosition(lng, lat, altitudeMetres) must return a THREE.Vector3.
 */
export async function createStreetTraffic({THREE, geographicPosition, data, signal} = {}) {
  if (!THREE || typeof geographicPosition !== 'function') {
    throw new TypeError('Street traffic needs THREE and geographicPosition.');
  }
  if (!data) {
    const response = await fetch(new URL('../data/bund/traffic-v4.json', import.meta.url), {signal});
    if (!response.ok) throw new Error(`Street traffic data failed (${response.status}).`);
    data = await response.json();
  }
  if (data.mode !== 'static' || !data.validation?.passed || !Array.isArray(data.vehicles) || data.vehicles.length > 12) {
    throw new Error('Street traffic data must be a validated, small static illustration.');
  }
  const group = new THREE.Group();
  group.name = 'Bund static traffic illustration';
  group.userData = {isIllustrative: true, isLiveTraffic: false, note: data.disclaimer_zh};
  const geometries = new Set(), materials = new Set(), batches = new Map();
  let disposed = false;
  const geometry = value => {geometries.add(value); return value;};
  const material = value => {materials.add(value); return value;};

  // An ellipsoid-rounded box, shared by body sections and their trim. Scaling
  // changes the corner radii smoothly, with no texture or subdivision modifier.
  const rounded = geometry(new THREE.BoxGeometry(1, 1, 1, 4, 4, 4));
  const positions = rounded.attributes.position, normals = rounded.attributes.normal;
  const corner = new THREE.Vector3(), direction = new THREE.Vector3();
  for (let i = 0; i < positions.count; i++) {
    corner.set(positions.getX(i), positions.getY(i), positions.getZ(i));
    direction.copy(corner).clampScalar(-.36, .36);
    const centre = direction.clone();
    direction.copy(corner).sub(centre).normalize();
    corner.copy(centre).addScaledVector(direction, .14);
    positions.setXYZ(i, corner.x, corner.y, corner.z);
    normals.setXYZ(i, direction.x, direction.y, direction.z);
  }
  positions.needsUpdate = true; normals.needsUpdate = true;
  rounded.computeBoundingSphere();

  // Tapered, sloping passenger cabin: front/rear windscreens are actual angled
  // planes, and body-colored borders/pillars remain visible around the glazing.
  const cabin = geometry(new THREE.BufferGeometry());
  const cabinVertices = [
    [-.48, 0, -.5], [.48, 0, -.5], [.48, 0, .5], [-.48, 0, .5],
    [-.40, 1, -.32], [.40, 1, -.32], [.40, 1, .23], [-.40, 1, .23],
  ];
  const cabinFaces = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];
  const cabinTriangles = [];
  for (const [a,b,c,d] of cabinFaces) {
    for (const index of [a,c,b,a,d,c]) cabinTriangles.push(...cabinVertices[index]);
  }
  cabin.setAttribute('position', new THREE.Float32BufferAttribute(cabinTriangles, 3));
  cabin.computeVertexNormals(); cabin.computeBoundingSphere();
  const glazing = geometry(new THREE.BufferGeometry());
  glazing.setAttribute('position', new THREE.Float32BufferAttribute([
    -.5,-.5,0, .5,-.5,0, .43,.5,0, -.5,-.5,0, .43,.5,0, -.43,.5,0,
  ], 3));
  glazing.computeVertexNormals();
  const cylinder = geometry(new THREE.CylinderGeometry(1, 1, 1, 20, 1));
  const shadowDisk = geometry(new THREE.CircleGeometry(1, 24));
  const paint = material(new THREE.MeshStandardMaterial({color:0xffffff, metalness:.18, roughness:.34}));
  const glass = material(new THREE.MeshStandardMaterial({color:0x263c48, metalness:.36, roughness:.17, side:THREE.DoubleSide}));
  const trim = material(new THREE.MeshStandardMaterial({color:0xffffff, metalness:.35, roughness:.5}));
  const rubber = material(new THREE.MeshStandardMaterial({color:0x171b1d, metalness:0, roughness:.94}));
  const alloy = material(new THREE.MeshStandardMaterial({color:0xa4abb0, metalness:.75, roughness:.3}));
  const lamp = material(new THREE.MeshBasicMaterial({color:0xffffff, toneMapped:true}));
  const shadow = material(new THREE.MeshBasicMaterial({color:0x070b0e, transparent:true, opacity:.17, depthWrite:false, side:THREE.DoubleSide}));
  paint.name='VehiclePaint'; glass.name='VehicleGlass'; trim.name='VehicleTrim';
  rubber.name='VehicleTyres'; alloy.name='VehicleWheelAlloy'; lamp.name='VehicleLamps'; shadow.name='VehicleContactShadow';
  function batch(name, shape, surface) {
    const value = {name, geometry:shape, material:surface, instances:[]};
    batches.set(name, value); return value;
  }
  const bodyBatch = batch('Vehicle paint and rounded body', rounded, paint);
  const cabinBatch = batch('Sloped passenger cabins', cabin, paint);
  const glassBatch = batch('Opaque low-cost glazing', glazing, glass);
  const trimBatch = batch('Bumpers, handles, mirrors and registration plates', rounded, trim);
  const tyreBatch = batch('Rubber tyres', cylinder, rubber);
  const hubBatch = batch('Metal wheel hubs', cylinder, alloy);
  const lightBatch = batch('Head, tail and taxi lamps', rounded, lamp);
  const shadowBatch = batch('Subtle static contact shadows', shadowDisk, shadow);
  const scratch = new THREE.Object3D(), matrix = new THREE.Matrix4(), basis = new THREE.Matrix4();
  const xAxis = new THREE.Vector3(), yAxis = new THREE.Vector3(), zAxis = new THREE.Vector3();
  let vehicleMatrix, vehicleId;
  function add(target, at, size, color, rotation = [0,0,0], quaternion) {
    scratch.position.set(...at); scratch.scale.set(...size);
    if (quaternion) scratch.quaternion.copy(quaternion); else scratch.rotation.set(...rotation);
    scratch.updateMatrix(); matrix.multiplyMatrices(vehicleMatrix, scratch.matrix);
    target.instances.push({matrix:matrix.clone(), color:color ? new THREE.Color(color) : null, vehicleId});
  }
  function panel(lower, upper, width, horizontal = [1,0,0]) {
    const low = new THREE.Vector3(...lower), high = new THREE.Vector3(...upper);
    const centre = low.clone().add(high).multiplyScalar(.5);
    xAxis.set(...horizontal).normalize(); yAxis.copy(high).sub(low);
    const height = yAxis.length(); yAxis.normalize(); zAxis.crossVectors(xAxis,yAxis).normalize();
    basis.makeBasis(xAxis,yAxis,zAxis);
    add(glassBatch,centre.toArray(),[width,height,1],null,[0,0,0],new THREE.Quaternion().setFromRotationMatrix(basis));
  }
  function wheels(length, width, bus) {
    const radius = bus ? .47 : .315, tread = bus ? .27 : .205;
    const axles = bus ? [-length*.32,length*.34] : [-length*.30,length*.29];
    for (const z of axles) for (const side of [-1,1]) {
      const x = side*(width/2-tread/2);
      add(tyreBatch,[x,radius,z],[radius,tread,radius],null,[0,0,Math.PI/2]);
      add(hubBatch,[side*(width/2+.006),radius,z],[radius*.59,.024,radius*.59],null,[0,0,Math.PI/2]);
      add(trimBatch,[side*(width/2+.022),radius,z],[.025,radius*.22,radius*.22],'#59636a');
    }
  }
  for (const vehicle of data.vehicles) {
    const {lng,lat,heading_degrees:heading,length_m:length,width_m:width,height_m:height} = vehicle;
    if (![lng,lat,heading,length,width,height].every(Number.isFinite) || length < 3 || length > 13 || width > 2.6) {
      throw new Error(`Invalid illustrative vehicle ${vehicle.id}.`);
    }
    const altitude = vehicle.ground_altitude_m ?? .020;
    const point = geographicPosition(lng,lat,altitude);
    // Keep physical metre scale consistent with MapLibre's latitude scaling.
    const metre = geographicPosition(lng,lat,altitude+1).distanceTo(point);
    const transform = new THREE.Object3D(); transform.position.copy(point);
    transform.rotation.y = Math.PI - heading*Math.PI/180;
    transform.scale.setScalar(metre); transform.updateMatrix(); vehicleMatrix = transform.matrix;
    vehicleId=vehicle.id;
    const bus = vehicle.kind === 'bus';
    // The footprint stays within the independently validated road envelope.
    add(shadowBatch,[0,.003,0],[width*.53,length*.48,1],null,[-Math.PI/2,0,0]);
    wheels(length,width,bus);
    if (bus) {
      add(bodyBatch,[0,1.7,0],[width,2.9,length],vehicle.color);
      add(bodyBatch,[0,3.19,-.6],[width*.64,.24,2.1],'#b8beb7');
      for (const side of [-1,1]) {
        add(bodyBatch,[side*(width/2+.004),1.05,0],[.025,.50,length*.94],'#467c7a');
        for (let k=0;k<8;k++) {
          const z=-length*.38+k*length*.108;
          panel([side*(width/2+.018),1.65,z],[side*(width/2+.018),2.68,z],length*.095,[0,0,-side]);
        }
        // Two understated door seams on the curb side, without invented route text.
        if (side===-1) for (const z of [length*.32,-length*.02]) {
          add(trimBatch,[side*(width/2+.028),1.22,z],[.035,1.72,.035],'#283d42');
        }
      }
      panel([-0,1.35,length/2+.018],[0,2.73,length/2+.018],width*.89);
      panel([0,1.80,-length/2-.018],[0,2.65,-length/2-.018],width*.85,[-1,0,0]);
      add(trimBatch,[0,2.91,length/2+.023],[width*.70,.18,.035],'#182629');
      for (const side of [-1,1]) {
        add(lightBatch,[side*width*.33,.78,length/2+.025],[.38,.19,.045],'#dce3d6');
        add(lightBatch,[side*width*.36,.87,-length/2-.025],[.18,.32,.045],'#8d342d');
      }
    } else {
      const cabinLength=length*.49, cabinBase=.86, cabinHeight=.64;
      add(bodyBatch,[0,.59,0],[width,.63,length],vehicle.color);
      add(bodyBatch,[0,.88,length*.30],[width*.98,.25,length*.36],vehicle.color);
      add(bodyBatch,[0,.92,-length*.365],[width*.98,.23,length*.24],vehicle.color);
      add(cabinBatch,[0,cabinBase,0],[width,cabinHeight,cabinLength],vehicle.color);
      panel([0,.905,cabinLength*.48],[0,1.455,cabinLength*.245],width*.91);
      panel([0,.905,-cabinLength*.48],[0,1.455,-cabinLength*.335],width*.91,[-1,0,0]);
      for (const side of [-1,1]) {
        for (const z of [-cabinLength*.205,cabinLength*.175]) {
          panel([side*width*.484,.94,z],[side*width*.407,1.43,z],cabinLength*.36,[0,0,-side]);
          add(trimBatch,[side*(width/2+.018),.96,z-.10],[.035,.037,.18],'#8f9ba0');
        }
        add(trimBatch,[side*(width/2+.055),1.01,cabinLength*.34],[.12,.10,.20],vehicle.color);
        add(lightBatch,[side*width*.32,.88,length/2-.01],[width*.24,.14,.10],'#e0e5d4');
        add(lightBatch,[side*width*.32,.86,-length/2+.005],[width*.23,.16,.09],'#983e33');
      }
      if (vehicle.kind==='taxi') {
        add(trimBatch,[0,1.53,.04],[.53,.055,.24],'#445155');
        add(lightBatch,[0,1.63,.04],[.48,.16,.21],'#d8c771');
      }
    }
    add(trimBatch,[0,bus?.44:.40,length/2-.01],[width*.83,.115,.15],'#35434a');
    add(trimBatch,[0,bus?.44:.40,-length/2+.01],[width*.83,.115,.15],'#35434a');
    add(trimBatch,[0,bus?.63:.59,length/2+.066],[bus?.43:.35,.12,.018],'#315b72');
    add(trimBatch,[0,bus?.63:.59,-length/2-.066],[bus?.43:.35,.12,.018],'#315b72');
  }
  let triangleCount=0, instanceCount=0;
  for (const entry of batches.values()) {
    if (!entry.instances.length) continue;
    const mesh = new THREE.InstancedMesh(entry.geometry,entry.material,entry.instances.length);
    mesh.name=entry.name; mesh.userData.vehicleIds=entry.instances.map(instance=>instance.vehicleId); mesh.castShadow=false; mesh.receiveShadow=false;
    mesh.instanceMatrix.setUsage(THREE.StaticDrawUsage);
    entry.instances.forEach((instance,index)=>{
      mesh.setMatrixAt(index,instance.matrix);
      if (instance.color) mesh.setColorAt(index,instance.color);
    });
    mesh.instanceMatrix.needsUpdate=true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate=true;
    mesh.computeBoundingBox(); mesh.computeBoundingSphere(); group.add(mesh);
    triangleCount+=(entry.geometry.index?.count ?? entry.geometry.attributes.position.count)/3*entry.instances.length;
    instanceCount+=entry.instances.length;
  }
  const stats={mode:'static',isLiveTraffic:false,vehicles:data.vehicles.length,
    types:data.vehicles.reduce((out,v)=>(out[v.kind]=(out[v.kind]||0)+1,out),{}),
    drawCalls:group.children.length,instances:instanceCount,triangles:triangleCount,
    animationLoops:0,extraLights:0,externalTextures:0,roadValidation:data.validation};
  group.userData.stats=stats;
  function dispose() {
    if (disposed) return;
    disposed=true; group.removeFromParent();
    for (const child of group.children) child.dispose?.();
    group.clear();
    for (const value of geometries) value.dispose();
    for (const value of materials) value.dispose();
  }
  return {group,stats,dispose};
}
