import * as THREE from '../vendor/three.module.js';

/** Original procedural visitor. Metres, +Y up, facing -Z; no external assets.
 * The outer group belongs to the geographic adapter: animation never changes
 * its transform. Shoe soles meet the Bund paving at +0.075 m above map ground.
 */
const GROUND = .075;
const TAU = Math.PI * 2;
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

function ovalSections(sections, segments = 16) {
  // Sections: [height, half-width, half-depth, z-offset]. A tailored surface,
  // rather than joined capsules, gives clothes their waist, cuffs and drape.
  const vertices = [], indices = [];
  for (const [y, rx, rz, z = 0] of sections) {
    for (let i = 0; i < segments; i++) {
      const a = i / segments * TAU;
      vertices.push(Math.cos(a) * rx, y, z + Math.sin(a) * rz);
    }
  }
  for (let j = 0; j < sections.length - 1; j++) {
    for (let i = 0; i < segments; i++) {
      const a = j * segments + i, b = j * segments + (i + 1) % segments;
      indices.push(a, a + segments, b, b, a + segments, b + segments);
    }
  }
  for (const [row, reverse] of [[0, false], [sections.length - 1, true]]) {
    const index = vertices.length / 3;
    vertices.push(0, sections[row][0], sections[row][3] || 0);
    for (let i = 0; i < segments; i++) {
      const a = row * segments + i, b = row * segments + (i + 1) % segments;
      indices.push(index, reverse ? b : a, reverse ? a : b);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices); geometry.computeVertexNormals();
  return geometry;
}

function softShadowGeometry(rx, rz) {
  // Vertex alpha gives a continuous, texture-free contact shadow, with no
  // disk edge. Keeping it separate from the hips prevents a bouncing shadow.
  const positions = [0, 0, 0], colors = [.12, .15, .16, .22], indices = [];
  const steps = 40;
  for (let ring = 1; ring <= 5; ring++) {
    const t = ring / 5, alpha = .22 * Math.pow(1 - t, 2);
    for (let i = 0; i < steps; i++) {
      const a = i / steps * TAU;
      positions.push(Math.cos(a) * rx * t, 0, Math.sin(a) * rz * t);
      colors.push(.12, .15, .16, alpha);
    }
  }
  for (let i = 0; i < steps; i++) indices.push(0, 1 + (i + 1) % steps, 1 + i);
  for (let ring = 0; ring < 4; ring++) {
    const base = 1 + ring * steps;
    for (let i = 0; i < steps; i++) {
      const a = base + i, b = base + (i + 1) % steps;
      indices.push(a, b + steps, a + steps, a, b, b + steps);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 4));
  g.setIndex(indices); g.computeVertexNormals();
  return g;
}

export function makeWalker() {
  const group = new THREE.Group(); group.name = 'Visitor · original procedural character';
  const body = new THREE.Group(); body.name = 'Pelvis and articulated body'; group.add(body);
  const material = (color, roughness = .9) => new THREE.MeshStandardMaterial({color, roughness});
  const cloth = material('#687169'), seam = material('#555f59'), lining = material('#b7b9a8');
  const shirt = material('#d7d4c8'), trousers = material('#38434a'), trouserSeam = material('#455057');
  const skin = material('#c79b80', .86), skinShade = material('#ad816c', .92);
  const hair = material('#312c28'), hairLight = material('#403831');
  const shoe = material('#646663'), sole = material('#c5c3b8'), lace = material('#c1c0b5');
  const iris = material('#3b3833'), white = material('#c5b8a7'), bag = material('#504d43');
  const sphere = new THREE.SphereGeometry(1, 16, 12);
  const box = new THREE.BoxGeometry(1, 1, 1);
  function mesh(g, m, parent, name, x = 0, y = 0, z = 0) {
    const item = new THREE.Mesh(g, m); item.name = name;
    item.position.set(x, y, z); item.castShadow = true; item.receiveShadow = true;
    parent.add(item); return item;
  }
  function ellipsoid(parent, name, m, x, y, z, sx, sy, sz) {
    const item = mesh(sphere, m, parent, name, x, y, z); item.scale.set(sx, sy, sz); return item;
  }
  function block(parent, name, m, x, y, z, sx, sy, sz) {
    const item = mesh(box, m, parent, name, x, y, z); item.scale.set(sx, sy, sz); return item;
  }
  function line(parent, name, m, points, radius = .003) {
    const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
    return mesh(new THREE.TubeGeometry(curve, Math.max(4, points.length * 3), radius, 5, false), m, parent, name);
  }
  function joint(parent, name, x, y, z) {
    const item = new THREE.Group(); item.name = name; item.position.set(x, y, z); parent.add(item); return item;
  }

  // Hip pivot is at 0.93 m. Torso geometry is expressed relative to this pivot.
  mesh(ovalSections([[-.075,.125,.100],[-.015,.151,.109],[.075,.155,.112],[.13,.155,.115]]), trousers, body, 'Trouser waist');
  const torso = joint(body, 'Counter-rotating upper body', 0, .09, 0);
  mesh(ovalSections([[0,.151,.113],[.035,.165,.12],[.17,.161,.116],
    [.30,.193,.126],[.38,.203,.116],[.42,.176,.095],[.445,.092,.069]]), cloth, torso, 'Tailored field jacket');
  // Visible neckline and front placket: subdued everyday clothing, no branding.
  mesh(ovalSections([[.366,.062,.092,-.008],[.441,.065,.071,-.007]]), shirt, torso, 'Cotton neckline');
  block(torso, 'Recessed jacket zip', seam, 0,.208,-.122,.008,.352,.006);
  block(torso, 'Zip pull', lining, 0,.337,-.130,.009,.017,.004);
  for (const side of [-1,1]) {
    const collar = block(torso, 'Folded collar', lining, side*.068,.409,-.087,.058,.066,.015);
    collar.rotation.z = side*.36; collar.rotation.x = -.20;
    line(torso, 'Pocket welt', seam, [[side*.074,.133,-.119],[side*.116,.164,-.115]], .004);
    line(torso, 'Jacket hem stitching', seam, [[side*.014,.018,-.121],[side*.09,.018,-.118],[side*.15,.018,-.061]], .002);
  }
  // Small soft daypack and straps, useful silhouette from the walking camera.
  ellipsoid(torso,'Daypack body',bag,0,.225,.147,.132,.176,.070);
  ellipsoid(torso,'Daypack outer pocket',seam,0,.158,.205,.105,.089,.019);
  line(torso,'Daypack zipper',lining,[[-.09,.24,.202],[0,.265,.217],[.09,.24,.202]],.0025);
  for (const side of [-1,1]) {
    line(torso,'Padded shoulder strap',bag,[[side*.108,.055,-.087],[side*.135,.24,-.124],
      [side*.145,.408,-.067],[side*.135,.419,.037],[side*.108,.32,.16]],.014);
    block(torso,'Strap adjuster',seam,side*.123,.118,-.115,.028,.024,.012);
  }

  mesh(ovalSections([[.432,.047,.046],[.50,.045,.044]],16), skin, torso, 'Neck');
  const head = joint(torso,'Head',0,.59,-.008);
  // Contoured jaw/cheek/temple rings keep an adult face silhouette without
  // oversized round cheeks or the spherical head of a toy figure.
  mesh(ovalSections([[-.111,.025,.031,-.005],[-.092,.055,.053,-.010],
    [-.060,.073,.065,-.011],[-.025,.088,.077,-.005],[.026,.091,.080,.003],
    [.071,.086,.078,.009],[.106,.063,.061,.011],[.124,.018,.022,.011]],24),skin,head,'Contoured head');
  ellipsoid(head,'Nose bridge',skin,0,-.003,-.079,.010,.024,.011);
  ellipsoid(head,'Nose tip',skin,0,-.024,-.089,.012,.009,.011);
  for (const side of [-1,1]) {
    ellipsoid(head,'Ear',skin,side*.095,-.006,.003,.014,.027,.015);
    ellipsoid(head,'Inner ear',skinShade,side*.103,-.004,-.003,.006,.016,.009);
    ellipsoid(head,'Eyelid',skinShade,side*.036,.008,-.076,.021,.008,.008);
    ellipsoid(head,'Eye',white,side*.036,.007,-.081,.014,.005,.004);
    ellipsoid(head,'Iris',iris,side*.036,.007,-.084,.005,.005,.002);
    line(head,'Eyebrow',hair,[[side*.020,.025,-.080],[side*.037,.029,-.080],[side*.052,.024,-.072]],.003);
  }
  line(head,'Mouth',skinShade,[[-.022,-.058,-.076],[0,-.060,-.080],[.022,-.058,-.076]],.0023);
  const scalp = new THREE.SphereGeometry(1,24,12,0,TAU,0,Math.PI*.65);
  const scalpPosition=scalp.attributes.position;
  for(let i=0;i<scalpPosition.count;i++) {
    const a=Math.atan2(scalpPosition.getZ(i),scalpPosition.getX(i));
    const theta=Math.acos(clamp(scalpPosition.getY(i),-1,1));
    const hairline=Math.PI*(.52-.14*Math.max(0,-Math.sin(a))+.12*Math.max(0,Math.sin(a)));
    const t=theta/(Math.PI*.65)*hairline;
    scalpPosition.setXYZ(i,.101*Math.sin(t)*Math.cos(a),.017+.121*Math.cos(t),.009+.094*Math.sin(t)*Math.sin(a));
  }
  scalp.computeVertexNormals();
  mesh(scalp,hair,head,'Short fitted hair');
  // The cropped back and swept fringe avoid a smooth helmet silhouette.
  ellipsoid(head,'Nape hair',hair,0,.031,.071,.075,.047,.016);
  for(let i=0;i<7;i++) {
    const lock=ellipsoid(head,'Swept fringe',i%3?hair:hairLight,-.060+i*.018,.070-Math.abs(i-3)*.003,-.068,
      .023,.014,.013); lock.rotation.z=-.48;
  }
  for(const side of [-1,1]) ellipsoid(head,'Sideburn',hair,side*.083,.007,-.031,.008,.022,.010);

  function bendableCloth(parent, name, m, sections, pivotY, bendStart, bendEnd) {
    const geometry=ovalSections(sections,20);
    const rest=geometry.attributes.position.array.slice();
    const item=mesh(geometry,m,parent,name);
    item.userData.deforms=true;
    return angle=>{
      const positions=geometry.attributes.position.array;
      for(let i=0;i<positions.length;i+=3) {
        const y=rest[i+1],z=rest[i+2];
        let weight=clamp((bendStart-y)/(bendStart-bendEnd),0,1);
        weight=weight*weight*(3-2*weight);
        const a=angle*weight,c=Math.cos(a),q=Math.sin(a);
        positions[i+1]=pivotY+(y-pivotY)*c-z*q;
        positions[i+2]=(y-pivotY)*q+z*c;
      }
      geometry.attributes.position.needsUpdate=true;
      geometry.computeVertexNormals();
    };
  }
  const arms=[];
  for(const side of [-1,1]) {
    const arm=joint(torso, side<0?'Right shoulder':'Left shoulder',side*.210,.362,0);
    const bendSleeve=bendableCloth(arm,'Continuous sleeve',cloth,
      [[-.503,.038,.040],[-.477,.042,.043],[-.38,.049,.049],[-.29,.050,.051],
       [-.25,.052,.052],[-.18,.059,.061],[-.08,.065,.067],[0,.063,.066],[.035,.041,.048]],
      -.268,-.21,-.33);
    const elbow=joint(arm,'Elbow hinge',0,-.268,0);
    mesh(ovalSections([[-.239,.039,.041],[-.221,.040,.042]]),seam,elbow,'Stitched cuff');
    const hand=joint(elbow,'Relaxed hand',0,-.26,0);
    ellipsoid(hand,'Palm',skin,0,-.026,-.003,.034,.051,.023);
    for(let i=0;i<4;i++) {
      const finger=ellipsoid(hand,'Finger',skin,-.023+i*.015,-.068+(i===0||i===3?.007:0),-.008,
        .008,.025,.010); finger.rotation.x=.18;
    }
    const thumb=ellipsoid(hand,'Thumb',skin,-side*.033,-.032,-.014,.012,.027,.012);thumb.rotation.z=-side*.42;
    arms.push({arm,elbow,hand,side,bendSleeve});
  }

  const legs=[];
  const shadowMaterial=new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,depthWrite:false,
    side:THREE.FrontSide,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
  const broadShadow=mesh(softShadowGeometry(.36,.43),shadowMaterial,group,'Soft ambient contact',0,GROUND+.002,0);
  broadShadow.castShadow=false; broadShadow.receiveShadow=false;
  for(const side of [-1,1]) {
    const hip=joint(body,side<0?'Right hip':'Left hip',side*.091,0,0);
    const bendTrouser=bendableCloth(hip,'Continuous trouser leg',trousers,
      [[-.826,.046,.048],[-.79,.047,.049],[-.68,.053,.056],[-.57,.059,.060],
       [-.46,.058,.064],[-.40,.060,.064],[-.30,.067,.073],[-.15,.082,.087],[.035,.086,.094]],
      -.425,-.35,-.50);
    const knee=joint(hip,'Knee hinge',0,-.425,0);
    mesh(ovalSections([[-.401,.047,.049],[-.381,.047,.049]]),trouserSeam,knee,'Trouser cuff');
    const foot=joint(knee,'Ankle and trainer',0,-.425,0);
    mesh(ovalSections([[-.100,.073,.132,-.028],[-.081,.079,.140,-.031],[-.057,.075,.137,-.032]],20),sole,foot,'Rubber outsole');
    mesh(ovalSections([[-.059,.073,.133,-.031],[-.025,.071,.130,-.035],[.021,.057,.092,-.012],
      [.048,.046,.047,.022]],20),shoe,foot,'Trainer upper');
    ellipsoid(foot,'Heel collar',shoe,0,.032,.035,.048,.035,.047);
    for(let i=0;i<4;i++) line(foot,'Shoelace',lace,[[-.032,.028-i*.007,-.021-i*.018],[0,.032-i*.007,-.024-i*.018],[.032,.028-i*.007,-.021-i*.018]],.002);
    const shadow=mesh(softShadowGeometry(.115,.19),shadowMaterial,group,'Foot contact shadow',side*.091,GROUND+.003,-.032);
    shadow.castShadow=false;shadow.receiveShadow=false;
    legs.push({hip,knee,foot,shadow,side,bendTrouser});
  }

  // Deterministic two-bone leg IK. During support the sole stays flat on paving;
  // the swing foot clears it and the knee bends forward, including at low speed.
  function poseLeg(leg, footY, footZ, hipY, pelvisRoll, pitch) {
    const a=.425,b=.425;
    const y=footY-hipY-Math.sin(pelvisRoll)*leg.side*.091;
    const z=footZ;
    const distance=clamp(Math.hypot(y,z),.10,a+b-.001);
    const along=(a*a-b*b+distance*distance)/(2*distance);
    const bend=Math.sqrt(Math.max(0,a*a-along*along));
    const kneeY=y/distance*along-z/distance*bend;
    const kneeZ=z/distance*along+y/distance*bend;
    const upper=Math.atan2(-kneeZ,-kneeY), lower=Math.atan2(-(z-kneeZ),-(y-kneeY));
    leg.hip.rotation.set(upper,0,-pelvisRoll,'ZXY');
    leg.knee.rotation.x=lower-upper;
    leg.bendTrouser(lower-upper);
    leg.foot.rotation.x=-lower+pitch;
    leg.shadow.position.z=footZ-.032;
    const clearance=Math.max(0,footY-.100);
    leg.shadow.scale.setScalar(1+clearance*1.7);
    leg.shadow.visible=clearance<.14;
  }

  let phase=0, previousTime=null, blend=0;
  function animate(speed=0,time=0) {
    const safeSpeed=Number.isFinite(speed)?Math.max(0,speed):0;
    const now=Number.isFinite(time)?time:0;
    const dt=previousTime===null?0:clamp(now-previousTime,0,.08);previousTime=now;
    const moving=safeSpeed>.04?clamp(safeSpeed/1.3,0,1):0;
    blend+=(moving-blend)*(1-Math.exp(-dt*10));
    const run=clamp((safeSpeed-4.4)/4.1,0,1);
    if(moving) phase=(phase+dt*(.72+Math.min(safeSpeed,8.5)*.17))%1;
    const theta=phase*TAU, stride=(.285+run*.095)*blend;
    const breath=Math.sin(now*1.7)*.002*(1-blend);
    const roll=Math.sin(theta)*.018*blend;
    // Shorter at mid-stance, taller at passing; very small bounce avoids skating.
    const hipY=.93 - .04*blend - Math.cos(theta*2)*.016*blend - run*.035*blend + breath;
    body.position.y=GROUND+hipY;body.rotation.z=roll;
    torso.rotation.y=Math.sin(theta)*.038*blend;
    torso.rotation.x=.018+run*.055*blend;
    head.rotation.y=-torso.rotation.y*.45;head.rotation.x=-.018-run*.025*blend;
    for(let i=0;i<legs.length;i++) {
      const leg=legs[i],p=(phase+i*.5)%1,support=.59-run*.08;
      let z,lift,pitch=0;
      if(p<support) {
        const t=p/support; z=-stride+2*stride*t;lift=0;
        // The last part of stance is a gentle toe-off, not a rigid ski foot.
        pitch=-Math.max(0,t-.80)*.42*blend;
      } else {
        const t=(p-support)/(1-support),smooth=t*t*(3-2*t);
        z=stride*(1-2*smooth);lift=Math.sin(Math.PI*t)*(.10+run*.09)*blend;
        pitch=Math.sin(TAU*t)*.12*blend;
      }
      // The toe-off rotates about the ankle. Raise the ankle by the rotated
      // sole's lowest point, so neither toe nor heel cuts through the paving.
      const ankleY=.100*Math.cos(pitch)+lift+(pitch>=0?.104:-.160)*Math.sin(pitch);
      poseLeg(leg,ankleY,z,hipY,roll,pitch);
    }
    for(let i=0;i<arms.length;i++) {
      const {arm,elbow,hand,side,bendSleeve}=arms[i];
      const swing=Math.cos(theta+i*Math.PI)*(.30+run*.21)*blend;
      arm.rotation.set(-swing-.04,0,-side*(.055+.018*blend));
      elbow.rotation.x=.18+run*.45+Math.max(0,swing)*.38;
      bendSleeve(elbow.rotation.x);
      hand.rotation.x=-.10;hand.rotation.z=side*.045;
    }
    group.updateMatrixWorld(true);
  }
  // Batch all fixed detail in each animated rigid part. Material colours are
  // baked into vertices; face, fingers, laces and hair do not cost one draw call
  // per detail. Deforming cloth retains its own geometry and joint hierarchy.
  const vertexMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.9});
  function batchRigidParts(parent) {
    for(const child of parent.children.slice()) if(child.isGroup) batchRigidParts(child);
    const fixed=[];
    for(const child of parent.children.slice()) {
      if(!child.isMesh||child.material.transparent) continue;
      if(child.userData.deforms) {
        const c=child.material.color,n=child.geometry.attributes.position.count;
        const colors=new Float32Array(n*3);
        for(let i=0;i<n;i++) colors.set([c.r,c.g,c.b],i*3);
        child.geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
        child.material=vertexMaterial;
      } else fixed.push(child);
    }
    if(!fixed.length) return;
    const positions=[],normals=[],colors=[];
    for(const child of fixed) {
      child.updateMatrix();
      const transformed=child.geometry.clone().applyMatrix4(child.matrix);
      const geometry=transformed.index?transformed.toNonIndexed():transformed;
      const p=geometry.attributes.position.array,n=geometry.attributes.normal.array,c=child.material.color;
      for(let i=0;i<p.length;i+=3) {
        positions.push(p[i],p[i+1],p[i+2]);normals.push(n[i],n[i+1],n[i+2]);colors.push(c.r,c.g,c.b);
      }
      geometry.dispose();if(geometry!==transformed)transformed.dispose();parent.remove(child);
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    geometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
    geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    mesh(geometry,vertexMaterial,parent,`${parent.name} · batched detail`);
  }
  batchRigidParts(group);
  group.traverse(object=>{if(object.isMesh)object.frustumCulled=false;});
  group.userData={author:'Shanghai project · original procedural geometry',license:'MIT',
    heightMetres:1.75,pavingHeightMetres:GROUND,forwardAxis:'-Z',rig:'articulated knees/elbows, analytic foot IK'};
  animate(0,0);
  return {group,animate};
}
