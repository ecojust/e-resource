id => {
  const app=window.__SHANGHAI_APP__, c=app.controller, map=app.scene.map;
  const position=typeof c.getPosition==='function'?c.getPosition():{...c.position};
  const asset=window.__BUILDING_PROBE__.assetState(id);
  const root=window.__BUILDING_PROBE__.sceneRoot;
  const avatar=root?.getObjectByName('Visitor · original procedural character');
  let effectiveVisible=Boolean(avatar);for(let p=avatar;p;p=p.parent)effectiveVisible=effectiveVisible&&p.visible;
  const eye=map.transform?.getCameraLngLat?.(), screen=map.project([position.lng,position.lat]);
  return {at:performance.now(),mode:app.mode,position_api:typeof c.getPosition==='function'?'controller.getPosition()':'controller.position read-only',
    position:{lng:position.lng,lat:position.lat},controller:{mode:c.mode,enabled:c.enabled,distance:c.distance,speed:c.speed,
      heading:c.heading,bearing:c.bearing,keys:[...c.keys],moveVector:{...c.moveVector},manualRun:c.manualRun,
      cameraDistance:c.cameraDistance,spawnGeneration:c._spawnGeneration},
    ground:{height:c.groundHeight,surfaceId:c.groundSurface?.id??null,atPosition:app.scene.groundAt?.(position.lng,position.lat)??null,
      loadedSourceCollision:app.scene.collisionAt?.(position.lng,position.lat)??null,
      localCollision:app.scene.sweepLocalCollision?.(position,position,{radius:.38,height:1.75})??null,sourceState:app.scene.getCollisionState()},
    camera:{center:map.getCenter().toArray(),zoom:map.getZoom(),pitch:map.getPitch(),bearing:map.getBearing(),
      actualMapEye:eye?{lng:eye.lng,lat:eye.lat,alt:map.transform.getCameraAltitude?.()??null}:null,
      playerGroundScreen:[screen.x,screen.y],
      lastControllerRequest:c._lastCameraRequest?JSON.parse(JSON.stringify(c._lastCameraRequest)):null},
    avatar:avatar?{found:true,name:avatar.name,uuid:avatar.uuid,visible:avatar.visible,effectiveVisible,
      position:avatar.position.toArray(),rotation:avatar.rotation.toArray(),scale:avatar.scale.toArray()}: {found:false},
    asset,landmark:app.scene.getLandmarkState().find(r=>r.id===id)??null,
    document:{hidden:document.hidden,focused:document.hasFocus(),activeTag:document.activeElement?.tagName},
    keyboardEvents:(window.__KEYBOARD_SMOKE_EVENTS__||[]).slice(),
    sourceReadiness:window.__BUILDING_PROBE__?.sourceReadiness()??null};
}
