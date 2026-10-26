/** Bund17/18 vegetation reconstructed approximately from a dated 2010 CC0 photo.
 * Tree roots come only from reviewed photo controls on mapped beds. Branches,
 * leaves and grass blades are procedural morphology, not a botanical survey.
 * No transparent cards, downloaded textures, animation loop, or extra lights.
 */
export async function createStreetGreenery({THREE, data, origin=[121.4862,31.2385], bedGroundHeights={}, signal}={}) {
  if(!THREE) throw new TypeError('THREE is required.');
  if(!data){const response=await fetch(new URL('../data/bund/greenery-v4.5.json',import.meta.url),{signal});if(!response.ok)throw new Error('Greenery data failed');data=await response.json();}
  if(data.version!=='bund-greenery-v4.5-photo-2010'||!data.validation?.passed||data.trees?.length!==7)throw new Error('Unreviewed greenery positions');
  const group=new THREE.Group();group.name='Bund 17/18 photo-proportioned greenery (2010)';group.userData={sourceDate:data.capture_date,note:data.disclaimer_zh,isSurvey:false};
  if(origin.length!==2 || origin.some((v,i)=>Math.abs(v-data.anchor[i])>1e-9)) throw new Error('Greenery must be attached at the street anchor.');
  // All positions are metres in the bund-streets owner frame. Do not place this
  // group independently in the global scene. The owner applies Mercator scale.
  const ground=(id,fallback)=>Number.isFinite(bedGroundHeights[id])?bedGroundHeights[id]:fallback;
  const geometries=new Set(),materials=new Set(),batches=[];let disposed=false;
  const geom=g=>(geometries.add(g),g),mat=m=>(materials.add(m),m);
  function rng(seed){return()=>{let t=seed+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}
  function batch(name,g,m){const b={name,g,m,instances:[]};batches.push(b);return b;}
  const bark=mat(new THREE.MeshStandardMaterial({color:0xffffff,roughness:.97,metalness:0}));bark.name='BundTreeBark';
  const foliage=mat(new THREE.MeshStandardMaterial({color:0xffffff,roughness:.88,metalness:0,vertexColors:true,side:THREE.DoubleSide}));foliage.name='BundTreeLeaves';
  const grassMaterial=mat(new THREE.MeshStandardMaterial({color:0xffffff,roughness:.98,metalness:0,vertexColors:true,side:THREE.DoubleSide}));grassMaterial.name='BundLivingGrassBlades';
  const wood=mat(new THREE.MeshStandardMaterial({color:0x8a8571,roughness:.96}));wood.name='BundTreeEstimatedBraces2010';
  const tieMaterial=mat(new THREE.MeshStandardMaterial({color:0x3b3c31,roughness:1}));tieMaterial.name='BundTreeSupportTies';
  const stemGeometry=new THREE.BufferGeometry(),stemVertices=[],stemIndices=[],stemRings=[[0,0,0,.16],[.05,.15/.42,-.03,.16*.72],[-.025,.29/.42,.06,.16*.72*.72],[.03,1,.015,.16*.72*.72*.72]],stemSides=10;
  for(const [x,y,z,r] of stemRings)for(let i=0;i<stemSides;i++){const a=i*Math.PI*2/stemSides;stemVertices.push(x+Math.cos(a)*r,y,z+Math.sin(a)*r);}
  for(let j=0;j<3;j++)for(let i=0;i<stemSides;i++){const a=j*stemSides+i,b=j*stemSides+(i+1)%stemSides,c=b+stemSides,d=a+stemSides;stemIndices.push(a,d,b,b,d,c);}
  for(let i=1;i<stemSides-1;i++){stemIndices.push(0,i,(i+1));stemIndices.push(30,30+i+1,30+i);}
  stemGeometry.setAttribute('position',new THREE.Float32BufferAttribute(stemVertices,3));stemGeometry.setIndex(stemIndices);stemGeometry.computeVertexNormals();stemGeometry.computeBoundingSphere();
  const stemBatch=batch('Continuous joined tree stems',geom(stemGeometry),bark);
  const branchBatch=batch('Tapered articulated branches',geom(new THREE.CylinderGeometry(.72,1,1,9,2)),bark);
  const supportBatch=batch('Photo-supported 2010 leaning braces',geom(new THREE.CylinderGeometry(1,1,1,6,1)),wood);
  const ties=batch('Estimated dark padded tree ties',geom(new THREE.TorusGeometry(1,.17,4,10)),tieMaterial);
  function makeLeaves(seed){
    const random=rng(seed),vertices=[],colors=[],base=new THREE.Color(),q=new THREE.Quaternion(),axis=new THREE.Vector3(),p=new THREE.Vector3();
    for(let i=0;i<210;i++){
      let x,y,z;do{x=random()*2-1;y=random()*2-1;z=random()*2-1;}while(x*x+y*y+z*z>1);
      // A gently folded four-triangle leaf: the contour is geometry, not a card.
      const length=.14+random()*.09,width=length*(.35+random()*.16),ridge=width*.16;
      const leaf=[[0,-length/2,0],[-width/2,0,0],[0,0,ridge],[width/2,0,0],[0,length/2,0]],faces=[[0,2,1],[0,3,2],[1,2,4],[2,3,4]];
      axis.set(random()-.5,random()-.5,random()-.5).normalize();q.setFromAxisAngle(axis,random()*Math.PI*2);
      base.setHSL(.205+random()*.055,.24+random()*.16,.23+random()*.115);
      for(const face of faces) for(const j of face){p.set(...leaf[j]).applyQuaternion(q).add(new THREE.Vector3(x,y,z));vertices.push(...p.toArray());const shade=j===2?1.07:j===0?.80:1;colors.push(base.r*shade,base.g*shade,base.b*shade);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeVertexNormals();g.computeBoundingSphere();return geom(g);
  }
  const leaves=[0,1,2].map(i=>batch(`Open irregular leaf clusters ${i+1}`,makeLeaves(1994+i*874),foliage));
  function makeGrass(){const vertices=[],colors=[],random=rng(2086),c=new THREE.Color();
    for(let i=0;i<6;i++){const angle=random()*Math.PI*2,w=.005+random()*.004,h=.04+random()*.018,bend=.012+random()*.017,cx=(random()-.5)*.055,cz=(random()-.5)*.055;
      const right=[Math.cos(angle)*w,Math.sin(angle)*w],lean=[Math.sin(angle)*bend,-Math.cos(angle)*bend];
      const pts=[[cx-right[0],0,cz-right[1]],[cx+right[0],0,cz+right[1]],[cx+lean[0]*.35-right[0]*.5,h*.6,cz+lean[1]*.35-right[1]*.5],[cx+lean[0]*.35+right[0]*.5,h*.6,cz+lean[1]*.35+right[1]*.5],[cx+lean[0],h,cz+lean[1]]];
      c.setHSL(.19+random()*.055,.35,.24+random()*.06);
      for(const face of [[0,1,3],[0,3,2],[2,3,4]])for(const k of face){vertices.push(...pts[k]);const f=k<2?.53:k===4?1.1:.9;colors.push(c.r*f,c.g*f,c.b*f);}}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeVertexNormals();g.computeBoundingSphere();return geom(g);}
  const grass=batch('Short curved lawn blades in mapped beds',makeGrass(),grassMaterial);
  const scratch=new THREE.Object3D(),up=new THREE.Vector3(0,1,0),color=new THREE.Color();
  function add(b,position,scale,quaternion,colour,owner){scratch.position.set(...position);scratch.scale.set(...scale);scratch.quaternion.copy(quaternion||new THREE.Quaternion());scratch.updateMatrix();b.instances.push({matrix:scratch.matrix.clone(),color:colour,owner});}
  function rod(b,a,c,r,colour,owner){const av=new THREE.Vector3(...a),cv=new THREE.Vector3(...c),d=cv.clone().sub(av),len=d.length();add(b,av.add(cv).multiplyScalar(.5).toArray(),[r,len,r],new THREE.Quaternion().setFromUnitVectors(up,d.normalize()),colour,owner);}
  for(const tree of data.trees){
    const random=rng(tree.seed),H=tree.height_m,W=tree.crown_width_m,x=tree.x,z=tree.z,y=ground(tree.bed,tree.ground_altitude_m),rotation=random()*Math.PI*2;
    const shift=(v)=>[x+v[0],y+v[1],z+v[2]],R=(lo,hi)=>lo+(hi-lo)*random();
    const stemPoints=[[0,0,0],[.05,H*.15,-.03],[-.025,H*.29,.06],[.03,H*.42,.015]];
    add(stemBatch,[x,y,z],[1,H*.42,1],new THREE.Quaternion(),color.setRGB(.145,.153,.126).multiplyScalar(R(.90,1.10)).getHex(),tree.id);
    for(let arm=0;arm<3;arm++){
      const angle=rotation+arm*Math.PI*2/3+R(-.25,.25),tip=[Math.cos(angle)*W*.28,H*R(.82,.90),Math.sin(angle)*W*.28],fork=[Math.cos(angle)*W*.09,H*.48,Math.sin(angle)*W*.09];
      const leaderStart=shift(stemPoints[2]),middle=fork.map((v,k)=>v*.45+tip[k]*.55);
      rod(branchBatch,leaderStart,shift(fork),.069,0x626757,tree.id);
      rod(branchBatch,shift(fork),shift(middle),.047,0x636959,tree.id);
      rod(branchBatch,shift(middle),shift(tip),.030,0x6b705f,tree.id);
      const fineTip=[tip[0]*1.06,tip[1]+H*.06,tip[2]*1.04];
      rod(branchBatch,shift(tip),shift(fineTip),.012,0x737766,tree.id);
      for(let j=0;j<5;j++){
        const t=.14+j*.17,start=fork.map((v,k)=>v*(1-t)+tip[k]*t),yaw=angle+R(-1.2,1.2),r=W*R(.20,.31),end=[Math.cos(yaw)*r,H*(.51+j*.085+R(-.03,.03)),Math.sin(yaw)*r];
        const twig=start.map((v,k)=>(v+end[k])*.5);
        rod(branchBatch,shift(start),shift(twig),.024,0x737666,tree.id);
        rod(branchBatch,shift(twig),shift(end),.012,0x7a7d6b,tree.id);
        for(let k=0;k<2;k++){
          const radial=k===0?1:.78,at=[end[0]*radial,end[1]+(k?-.18:.21),end[2]*radial],s=[W*R(.14,.19),H*R(.060,.090),W*R(.14,.19)];
          const q=new THREE.Quaternion().setFromEuler(new THREE.Euler(R(-.3,.3),random()*Math.PI*2,R(-.25,.25)));
          add(leaves[(arm+j+k)%3],shift(at),s,q,color.setHSL(.20+R(0,.035),.08,R(.76,.96)).getHex(),tree.id);
        }
      }
      add(leaves[arm%3],shift([tip[0],tip[1]+.15,tip[2]]),[W*.15,H*.07,W*.15],new THREE.Quaternion(),0xc9d1b3,tree.id);
    }
    for(let k=0;k<3;k++){const a=rotation+k*Math.PI*2/3;rod(supportBatch,shift([Math.cos(a)*tree.support_radius_m,.03,Math.sin(a)*tree.support_radius_m]),shift([Math.cos(a)*.12,tree.support_top_m,Math.sin(a)*.12]),.035,null,tree.id);}
    add(ties,shift([.01,tree.support_top_m,0]),[.165,.165,.165],new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI/2,0,0)),null,tree.id);
  }
  for(const [x,z,yaw,size,bed] of data.grass)add(grass,[x,ground(bed,.09),z],[size,size,size],new THREE.Quaternion().setFromEuler(new THREE.Euler(0,yaw,0)),null,'grass');
  let triangles=0,instances=0,resourceBytes=0;
  for(const b of batches){const mesh=new THREE.InstancedMesh(b.g,b.m,b.instances.length);mesh.name=b.name;mesh.userData.owners=b.instances.map(v=>v.owner);mesh.instanceMatrix.setUsage(THREE.StaticDrawUsage);
    b.instances.forEach((v,i)=>{mesh.setMatrixAt(i,v.matrix);if(v.color!==null&&v.color!==undefined)mesh.setColorAt(i,new THREE.Color(v.color));});mesh.instanceMatrix.needsUpdate=true;if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;mesh.computeBoundingBox();mesh.computeBoundingSphere();mesh.castShadow=b!==grass;mesh.receiveShadow=true;group.add(mesh);if(b===grass)mesh.userData.nearGrass=true;
    triangles+=(b.g.index?.count??b.g.attributes.position.count)/3*mesh.count;instances+=mesh.count;resourceBytes+=mesh.instanceMatrix.array.byteLength+(mesh.instanceColor?.array.byteLength||0);}
  for(const g of geometries){resourceBytes+=(g.index?.array.byteLength||0);for(const a of Object.values(g.attributes))resourceBytes+=a.array.byteLength;}
  const stats={trees:data.trees.length,grassClumps:data.grass.length,sourceDate:data.capture_date,drawCalls:group.children.length,instances,triangles,geometryAndInstanceBytes:resourceBytes,externalTextures:0,animationLoops:0,extraLights:0,speciesClaimed:false,rootPositionsAreEstimates:true};group.userData.stats=stats;
  function setActive(active){group.visible=Boolean(active);}
  function updateDistance(distanceMetres){for(const m of group.children)if(m.userData.nearGrass)m.visible=distanceMetres<65;}
  function dispose(){if(disposed)return;disposed=true;group.removeFromParent();for(const child of group.children)child.dispose();group.clear();for(const g of geometries)g.dispose();for(const m of materials)m.dispose();}
  return {group,stats,setActive,updateDistance,dispose};
}
