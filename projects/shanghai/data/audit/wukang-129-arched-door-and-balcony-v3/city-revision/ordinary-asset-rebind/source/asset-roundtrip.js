// A supplementary object-level measurement. The normal map is tested separately.
(async () => {
  const THREE = await import('/vendor/three.module.js');
  const {GLTFLoader} = await import('/vendor/GLTFLoader.js');
  const {MeshoptDecoder} = await import('/vendor/meshopt_decoder.module.js');
  const {loadOrdinaryLandmarkAsset} = await import('/src/ordinary-scene-adapter.js?v=asset-timeout-retry-v1');
  const {getVerifiedOrdinaryAsset} = await import('/src/ordinary-asset-verification.js');
  const rows = await (await fetch('/data/landmarks.json')).json();
  const record = rows.find(item => item.id === 'xuhui-wukang-129');
  record.ordinaryBaseURL = new URL('/', location.href).href;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf3efe5);
  const renderer = new THREE.WebGLRenderer({alpha:false,antialias:false,preserveDrawingBuffer:true});
  renderer.setSize(320,220);
  const container = document.getElementById('map');
  container.style.cssText='display:grid;place-items:center;background:#f3efe5';
  container.append(renderer.domElement);
  const label = document.getElementById('name');
  const halfWidth=22.07/2, halfHeight=halfWidth*220/320;
  const camera=new THREE.OrthographicCamera(-halfWidth,halfWidth,halfHeight,-halfHeight,.1,200);
  camera.position.set(-29.948699271954514,8.532833167201922,-10.645578849354314);
  camera.lookAt(-2.2574833611473233,2.78283316720192,-1.5057450772850103);
  scene.add(new THREE.HemisphereLight(0xffffff,0xaba69d,2.0));
  const sun = new THREE.DirectionalLight(0xffffff,2.0);
  sun.position.set(12,20,8);scene.add(sun);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  let current;
  window.drawCityAsset = async (variant) => {
    const next = await loadOrdinaryLandmarkAsset({record,variant,loader});
    const object = next.scene;
    const receipt = getVerifiedOrdinaryAsset(object);
    if (!receipt || receipt.variant !== (variant==='distant'?'lod':'web')) throw Error('Missing loader receipt');
    let drawn=0, meshTriangles=0, previousDrawnAfterRelease=0;
    const before=current?getVerifiedOrdinaryAsset(current):null;
    if(current){
      scene.remove(current);
      const geometry=new Set(), materials=new Set(), textures=new Set();
      current.traverse(mesh=>{if(!mesh.isMesh)return;mesh.onBeforeRender=()=>{previousDrawnAfterRelease++};geometry.add(mesh.geometry);for(const m of [].concat(mesh.material)){materials.add(m);for(const value of Object.values(m))if(value?.isTexture)textures.add(value)}});
      for(const value of [...geometry,...textures,...materials]) value.dispose();
    }
    object.traverse(mesh=>{if(mesh.isMesh){mesh.onBeforeRender=()=>{drawn++};meshTriangles+=(mesh.geometry.index?.count||mesh.geometry.attributes.position.count)/3;}});
    scene.add(object);current=object;
    const bounds=new THREE.Box3().setFromObject(object), mid=bounds.getCenter(new THREE.Vector3());
    
    label.textContent='武康路129号 · '+(variant==='distant'?'城市远景模型':'城市近景模型');
    renderer.render(scene,camera);
    const gl=renderer.getContext(),pixels=new Uint8Array(320*220*4);gl.readPixels(0,0,320,220,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
    const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',pixels)),x=>x.toString(16).padStart(2,'0')).join('');
    const counts=renderer.info.render;
    if(!drawn||previousDrawnAfterRelease||!counts.triangles||meshTriangles!==record[variant==='distant'?'lod_triangles':'triangles']||gl.getError()!==gl.NO_ERROR)throw Error('The actual WebGL drawing statistics do not match the signed role');
    return {variant,receipt,before,drawCalls:drawn,previousDrawnAfterRelease,meshTriangles,triangles:counts.triangles,webglPixelSHA256:h,viewport:[320,220],anchor:record.anchor,bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()}};
  };
  window.roundtripReady=true;
})().catch(error=>{document.body.dataset.setupError=error.stack});
