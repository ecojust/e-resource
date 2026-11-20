// Use MODEL_BASE_URL for a Shanghai project serving the production module and fixture.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');
const url = new URL(process.env.MODEL_BASE_URL || 'http://127.0.0.1:8784/');
const out = process.argv[2];
if (!out) throw Error('Pass a JSON audit output path');
const sha = b=>createHash('sha256').update(b).digest('hex');

(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
  try {
    const page = await browser.newPage(), errors = [];
    page.on('pageerror',error=>errors.push(error.message));
    page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
    await page.route('**/dense-owner-test',r=>r.fulfill({contentType:'text/html',body:'<link rel="icon" href="data:,">'}));
    await page.goto(new URL('dense-owner-test',url).href);
    const fixtureURL = new URL('tests/fixtures/dense-owner-clipping.json',url);
    const fixture = await (await page.request.get(fixtureURL.href)).body();
    const module = await (await page.request.get(new URL('src/candidate-city-clipping.js',url).href)).body();
    const result = await page.evaluate(async f => {
      const T = await import('./vendor/three.module.js');
      const {CandidateCityClipper} = await import('./src/candidate-city-clipping.js');
      const [lng,lat] = f.anchor, rad = Math.PI/180, k = 6371008.8*Math.cos(lat*rad);
      const geographicPosition = (x,y,z=0)=>new T.Vector3((x-lng)*rad*k,z*Math.cos(lat*rad)/Math.cos(y*rad),
        (Math.asinh(Math.tan(lat*rad))-Math.asinh(Math.tan(y*rad)))*k);
      const clipper = new CandidateCityClipper({THREE:T,geographicPosition});
      const renderer = new T.WebGLRenderer({antialias:false,alpha:false});
      const target = new T.WebGLRenderTarget(17,17);
      renderer.setClearColor(0xff00ff);renderer.setRenderTarget(target);
      const cam = new T.OrthographicCamera(-.25,.25,.25,-.25,.1,200);
      cam.up.set(0,0,-1);
      const scene = new T.Scene(), light = new T.PointLight(0xffffff);
      light.position.set(0,65,0);light.updateMatrixWorld();scene.add(new T.AmbientLight(0xffffff,2));
      const pixel = new Uint8Array(4), sameBackground = a=>a[0]===255&&a[1]===0&&a[2]===255;
      const stages = {old: [...f.previousCuts,f.hall], added: [...f.previousCuts,f.hall,f.nunnery]};
      const variants = {}, actualShadows = {};
      const samples = f.witnesses.map(w=>w.point);
      const passNames = ['visible','depth','distance'];
      function read(points) {
        return points.map(([x,z])=>{
          cam.position.set(x,90,z);cam.lookAt(x,0,z);
          renderer.render(scene,cam);renderer.readRenderTargetPixels(target,8,8,1,1,pixel);
          return [...pixel];
        });
      }
      function paint(mesh,visibleMaterial) {
        const byPass={};
        for(const [i,mat] of [visibleMaterial,mesh.customDepthMaterial,mesh.customDistanceMaterial].entries()){
          mat.side=T.DoubleSide;
          if(i===2)renderer.properties.get(mat).light=light;
          mesh.material=mat;
          const pixels=read(samples);
          byPass[passNames[i]]={drawn:pixels.map(a=>!sameBackground(a)),pixels};
        }
        mesh.material=visibleMaterial;return byPass;
      }
      for(const [variant,rows] of Object.entries(f.nativeSurfaces)){
        const geometry=new T.BufferGeometry(), positions=[],ids=[];
        for(const row of rows)for(const p of row.vertices){positions.push(...p);ids.push(row.owner);}
        geometry.setAttribute('position',new T.Float32BufferAttribute(positions,3));
        if(variant==='far')geometry.setAttribute('_feature_id_0',new T.Float32BufferAttribute(ids,1));
        geometry.computeVertexNormals();
        const material = new T.MeshStandardMaterial({color:0x00bb33,side:T.DoubleSide});
        const mesh = new T.Mesh(geometry,material);scene.add(mesh);
        const record=variant==='far'?{id:f.macro}:{id:f.macro+'/near',parent:{id:f.macro},ids:f.nearMembership};
        clipper.bindObject(mesh,record);const byStage={};
        for(const [stage,cl] of [['before',stages.old],['added',stages.added],['reduced',stages.old],['restored',[]]]){
          clipper.update(cl);
          const state=clipper.getState();
          byStage[stage]={passes:paint(mesh,material),triangles:state.triangles,dense:state.denseMacroTables,
            scoped:state.ownerScopedSources[0]??null};
        }
        variants[variant]=byStage;
        // Exercise the renderer's actual shadow-map rendering, including the
        // directional depth pass and the negative-Y face of a point-light atlas.
        // At each witness the light is directly above the native roof surface.
        actualShadows[variant]={};mesh.castShadow=true;
        renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.BasicShadowMap;
        for(const [kind,lamp] of [['directional',new T.DirectionalLight()],['point',new T.PointLight(0xffffff,1,200)]]){
          lamp.castShadow=true;lamp.shadow.mapSize.set(64,64);lamp.shadow.camera.near=.1;lamp.shadow.camera.far=200;
          if(lamp.target){
            Object.assign(lamp.shadow.camera,{left:-1,right:1,top:1,bottom:-1});
            scene.add(lamp.target);
          }
          scene.add(lamp);const stagesRead={};
          for(const [name,clips] of Object.entries(stages)){
            clipper.update(clips);
            const pixels=samples.map(([x,z])=>{
              lamp.position.set(x,90,z);if(lamp.target)lamp.target.position.set(x,0,z);
              cam.position.set(x,90,z);cam.lookAt(x,0,z);renderer.render(scene,cam);
              const vp=lamp.shadow.getViewport(kind==='point'?5:0);
              renderer.readRenderTargetPixels(lamp.shadow.map,Math.floor((vp.x+0.5)*64),Math.floor((vp.y+0.5)*64),1,1,pixel);
              return [...pixel];
            });
            stagesRead[name]={drawn:pixels.map(a=>a.some(channel=>channel!==255)),pixels};
          }
          actualShadows[variant][kind]=stagesRead;
          scene.remove(lamp);if(lamp.target)scene.remove(lamp.target);lamp.shadow.dispose();lamp.dispose();
        }
        renderer.shadowMap.enabled=false;clipper.releaseObject(mesh);scene.remove(mesh);geometry.dispose();material.dispose();
      }
      // Use the same native target roof faces with deliberately different owner or macro
      // attributes. Both overlap the real mask exactly; the former cells remain visible.
      const guards={};
      for (const [key,macro,owner] of [['differentOwner',f.macro,30],['differentMacro','other-macro',448],['sameOwner',f.macro,448]]) {
        const g=new T.BufferGeometry(), positions=f.nativeSurfaces.far.filter(r=>r.owner===448).flatMap(r=>r.vertices.flat());
        g.setAttribute('position',new T.Float32BufferAttribute(positions,3));g.setAttribute('_feature_id_0',new T.Float32BufferAttribute(new Array(positions.length/3).fill(owner),1));
        const m=new T.MeshBasicMaterial({color:0x00bb33,side:T.DoubleSide}),mesh=new T.Mesh(g,m);scene.add(mesh);
        clipper.bindObject(mesh,{id:macro});
        const wildcard={geometry:f.nunnery.geometry},local={...wildcard,owner:{macro_id:f.macro}};
        const hold={...f.nunnery,height_reference:f.anchor,min_height:100,max_height:110};
        const cover={...f.nunnery,height_reference:f.anchor,min_height:0,max_height:60};
        const flags={};
        for(const [name,rows] of Object.entries({production:stages.added,global:[...stages.added,wildcard],macroWildcard:[...stages.added,local],aboveRoof:[...stages.old,hold],throughRoof:[...stages.old,cover]})){
          clipper.update(rows);flags[name]=!sameBackground(read([samples[0]])[0]);
        }
        guards[key]=flags;clipper.releaseObject(mesh);scene.remove(mesh);g.dispose();m.dispose();
      }
      // The new owner sorts after every real source owner. Its two triangles
      // start beyond logical record 320, guarding both paged shader paths.
      const [rx,rz]=samples[1], toGeo=(x,z)=>[lng+x/(rad*k),Math.atan(Math.sinh(Math.asinh(Math.tan(lat*rad))-z/k))/rad];
      const square=[[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]].map(([x,z])=>toGeo(rx+x,rz+z));
      const late={geometry:{type:'Polygon',coordinates:[square]},owner:{macro_id:f.macro,feature_local_id:12000}};
      const allIds=new Set([12000]);
      for(const c of stages.added)for(const o of (c.owners||[c.owner||{}]))if(o.feature_local_id)allIds.add(o.feature_local_id);
      const lastRecords={};
      for(const tagged of [true,false]){
        const positions=f.nativeSurfaces.far.filter(row=>row.owner===448).flatMap(row=>row.vertices.flat());
        const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));
        if(tagged)g.setAttribute('_feature_id_0',new T.Float32BufferAttribute(new Array(positions.length/3).fill(12000),1));
        const material=new T.MeshBasicMaterial({color:0x00bb33,side:T.DoubleSide}),mesh=new T.Mesh(g,material);
        scene.add(mesh);clipper.bindObject(mesh,tagged?{id:f.macro}:{id:f.macro+'/many',parent:{id:f.macro},ids:[...allIds]});
        clipper.update(stages.added);const prior=read([samples[1]])[0];
        clipper.update([...stages.added,late]);const updated=read([samples[1]])[0];
        const dense=clipper.getState().denseMacroTables[0], table=clipper.macroTables.get(dense.macro);
        const finalRows=Array.from({length:2},(_,i)=>table.data[(table.triangles-2+i)*16+12]);
        lastRecords[tagged?'taggedFar':'untaggedNear']={prior,updated,priorDrawn:!sameBackground(prior),afterDrawn:!sameBackground(updated),
          tableRows:table.triangles,sourceRows:tagged?table.triangles:clipper.getState().ownerScopedSources[0].triangles,finalRows};
        clipper.releaseObject(mesh);scene.remove(mesh);g.dispose();material.dispose();
      }
      clipper.update([]);const stateAfterRelease=clipper.getState();clipper.dispose();
      const gl=renderer.getContext(),glError=gl.getError(),contextLost=gl.isContextLost(),programs=renderer.info.programs.length;
      target.dispose();renderer.dispose();
      return {variants,actualShadows,guards,lastRecords,stateAfterRelease,glError,contextLost,programs};
    },JSON.parse(fixture));
    for(const variant of Object.values(result.variants)){
      for(const [stage,value] of Object.entries(variant)){
        for(const [pass,{drawn}] of Object.entries(value.passes)){
          assert.deepEqual(drawn,stage==='added'?[false,true,true]:[true,true,true],stage+' '+pass);
        }
      }
      assert.equal(variant.before.triangles,320);
      assert.equal(variant.added.triangles,322);
      assert.equal(variant.added.dense[0].pages,2);
      assert.equal(variant.added.dense[0].maxFeatureSpan,24);
    }
    for(const [variant,shadows] of Object.entries(result.actualShadows))for(const [light,stages] of Object.entries(shadows)){
      assert.deepEqual(stages.old.drawn,[true,true,true],variant+' '+light+' old actual shadow');
      assert.deepEqual(stages.added.drawn,[false,true,true],variant+' '+light+' added actual shadow');
    }
    assert.equal(result.variants.near.added.scoped.triangles,2);
    assert.deepEqual(result.guards,{
      differentOwner:{production:true,global:false,macroWildcard:false,aboveRoof:true,throughRoof:true},
      differentMacro:{production:true,global:false,macroWildcard:true,aboveRoof:true,throughRoof:true},
      sameOwner:{production:false,global:false,macroWildcard:false,aboveRoof:true,throughRoof:false}});
    for(const x of Object.values(result.lastRecords)){
      assert.equal(x.priorDrawn,true);assert.equal(x.afterDrawn,false);
      assert.equal(x.tableRows,324);assert.ok(x.sourceRows>320);assert.deepEqual(x.finalRows,[12000,12000]);
    }
    assert.equal(result.stateAfterRelease.boundMaterials,0);assert.equal(result.stateAfterRelease.sourceObjects,0);
    assert.equal(result.glError,0);assert.equal(result.contextLost,false);assert.deepEqual(errors,[]);
    fs.writeFileSync(out,JSON.stringify({passed:true,checked_at_utc:new Date().toISOString(),browser:browser.version(),base:url.href,
      fixture_sha256:sha(fixture),module_sha256:sha(module),checker_sha256:sha(fs.readFileSync(__filename)),...result},null,2)+'\n');
  } finally {await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
