import * as THREE from '../vendor/three.module.js';
import { GLTFLoader } from '../vendor/GLTFLoader.js';
import { MeshoptDecoder } from '../vendor/meshopt_decoder.module.js';
import { applyBuildingMaterial } from './building-material.js';
import { applyPavingMaterial } from './paving-material.js';
import { applyStreetWidths, applyStreetColors } from './road-width.js';
import { FeatureStateSuppressor, LocalModelStreamer } from './local-model-streamer.js';

const DEG = Math.PI / 180;
const EARTH = 6378137;
const ORIGIN = [121.4737, 31.2304];
const BUILDINGS = 'shanghai-buildings-3d';
const BUILDING_PARTS = 'shanghai-building-parts-3d';
const OSM_BUILDINGS = 'shanghai-osm-buildings-fallback';
const OVERTURE_SOURCE = 'overture-buildings';
const CUSTOM = 'shanghai-landmarks-and-walker';
const BOUNDARY_SOURCE = 'shanghai-district-boundaries';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function distanceMetres(a, b) {
  const x = (a.lng - b.lng) * DEG * EARTH * Math.cos((a.lat + b.lat) * DEG / 2);
  const z = (a.lat - b.lat) * DEG * EARTH;
  return Math.hypot(x, z);
}
function offsetLngLat(p, east, north) {
  return {lng: p.lng + east / (EARTH * Math.cos(p.lat * DEG)) / DEG,
    lat: p.lat + north / EARTH / DEG};
}
function ringContains(ring, lng, lat) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[i], [bx, by] = ring[j];
    if ((ay > lat) !== (by > lat) && lng < (bx - ax) * (lat - ay) / (by - ay) + ax) inside = !inside;
  }
  return inside;
}
function polygonContains(rings, lng, lat) {
  return rings.length && ringContains(rings[0], lng, lat)
    && !rings.slice(1).some(ring => ringContains(ring, lng, lat));
}
function geometryContains(geometry, lng, lat) {
  if (geometry.type === 'Polygon') return polygonContains(geometry.coordinates, lng, lat);
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.some(r => polygonContains(r, lng, lat));
  return false;
}
function boundsOf(geometry) {
  const bounds = [Infinity, Infinity, -Infinity, -Infinity];
  function visit(c) {
    if (typeof c[0] === 'number') {
      bounds[0] = Math.min(bounds[0], c[0]); bounds[1] = Math.min(bounds[1], c[1]);
      bounds[2] = Math.max(bounds[2], c[0]); bounds[3] = Math.max(bounds[3], c[1]);
    } else for (const item of c) visit(item);
  }
  visit(geometry.coordinates);
  return bounds;
}
function nearestOnLine(point, coordinates) {
  const sx = Math.cos(point.lat * DEG) * DEG * EARTH, sy = DEG * EARTH;
  let best = null;
  for (let i = 1; i < coordinates.length; i++) {
    const a = coordinates[i - 1], b = coordinates[i];
    const ax = (a[0] - point.lng) * sx, ay = (a[1] - point.lat) * sy;
    const bx = (b[0] - point.lng) * sx, by = (b[1] - point.lat) * sy;
    const dx = bx - ax, dy = by - ay, len2 = dx * dx + dy * dy;
    const t = len2 ? clamp(-(ax * dx + ay * dy) / len2, 0, 1) : 0;
    const x = ax + t * dx, y = ay + t * dy, distance = Math.hypot(x, y);
    if (!best || distance < best.distance) best = {lng: point.lng + x / sx, lat: point.lat + y / sy, distance};
  }
  return best;
}
function configureStyle(style) {
  style = structuredClone(style);
  style.name = 'Shanghai · city walk';
  style.projection = {type: 'mercator'};
  // City-scale PMTiles and high camera pitches can expose thousands of POI
  // icons in one overzoomed tile. Keep street/place/water names, but omit the
  // generic POI symbol buckets: they obscure the model and exceed old GL limits.
  style.layers = style.layers.filter(layer => layer.type !== 'fill-extrusion'
    && !(layer.type === 'symbol' && layer['source-layer'] === 'poi')
    && !layer.id.includes('one_way_arrow'));
  for (const layer of style.layers) {
    applyStreetWidths(layer);
    if (layer.type === 'symbol') layer.maxzoom = Math.min(layer.maxzoom ?? 24, 19.5);
    if (layer.id === 'road_area_pattern') {
      delete layer.paint['fill-pattern'];
      layer.paint['fill-color'] = '#cdd2d0';
      layer.paint['fill-antialias'] = false;
    }
    if (['road_path_pedestrian', 'bridge_path_pedestrian'].includes(layer.id)) {
      delete layer.paint['line-dasharray'];
      layer.paint['line-color'] = '#aeb8b4';
    }
    applyStreetColors(layer);
    if (layer.id === 'background') layer.paint = {...layer.paint, 'background-color': '#eceee8'};
    if (layer['source-layer'] === 'water' && layer.type === 'fill') layer.paint = {...layer.paint, 'fill-color': '#8bbbc8'};
    if (layer['source-layer'] === 'park' && layer.type === 'fill') layer.paint = {...layer.paint, 'fill-color': '#c4d6b8'};
    if (layer.type === 'symbol' && layer.layout?.['text-field'] && !layer.id.includes('shield')) {
      layer.layout['text-field'] = ['coalesce', ['get', 'name:zh'], ['get', 'name:nonlatin'], ['get', 'name'], ['get', 'name:en'], ''];
    }
    if (layer['source-layer'] === 'poi' && layer.type === 'symbol') {
      layer.minzoom = Math.max(layer.minzoom || 0, layer.id === 'poi_transit' ? 16 : 17);
    }
  }
  return style;
}

function makeWalker() {
  const walker = new THREE.Group();
  walker.name = 'Third-person walker';
  const orange = new THREE.MeshStandardMaterial({color: '#e7783c', roughness: .83});
  const dark = new THREE.MeshStandardMaterial({color: '#28394a', roughness: .92});
  const skin = new THREE.MeshStandardMaterial({color: '#d7ac88', roughness: .82});
  const shoe = new THREE.MeshStandardMaterial({color: '#26333b', roughness: .92});
  const hair = new THREE.MeshStandardMaterial({color: '#342b26', roughness: .95});
  const add = (geometry, material, parent, x, y, z) => {
    const mesh = new THREE.Mesh(geometry, material); mesh.position.set(x, y, z); parent.add(mesh); return mesh;
  };
  add(new THREE.CapsuleGeometry(.21, .33, 4, 12), orange, walker, 0, 1.20, 0);
  add(new THREE.SphereGeometry(.145, 16, 12), skin, walker, 0, 1.66, -.012);
  add(new THREE.SphereGeometry(.151, 16, 8, 0, Math.PI * 2, 0, Math.PI * .56), hair, walker, 0, 1.68, -.006);
  add(new THREE.BoxGeometry(.28, .34, .15), dark, walker, 0, 1.23, .20);
  const legs = [], arms = [];
  for (const side of [-1, 1]) {
    const leg = new THREE.Group(); leg.position.set(side * .12, .92, 0); walker.add(leg);
    add(new THREE.CapsuleGeometry(.083, .55, 4, 10), dark, leg, 0, -.35, 0);
    add(new THREE.BoxGeometry(.17, .12, .29), shoe, leg, 0, -.81, -.07); legs.push(leg);
    const arm = new THREE.Group(); arm.position.set(side * .27, 1.41, 0); walker.add(arm);
    add(new THREE.CapsuleGeometry(.065, .34, 4, 10), orange, arm, 0, -.23, 0);
    add(new THREE.SphereGeometry(.07, 10, 8), skin, arm, 0, -.47, 0); arms.push(arm);
    add(new THREE.BoxGeometry(.035, .36, .02), dark, walker, side * .14, 1.25, -.20);
  }
  const shadow = add(new THREE.CircleGeometry(.38, 28),
    new THREE.MeshBasicMaterial({color: '#213b40', transparent: true, opacity: .20, depthWrite: false}), walker, 0, .052, 0);
  shadow.rotation.x = -Math.PI / 2;
  walker.traverse(o => { if (o.isMesh) o.frustumCulled = false; });
  return {group: walker, animate(speed, time) {
    const amount = clamp(speed / 3.5, 0, 1), stride = Math.sin(time * 9.5) * .47 * amount;
    legs[0].rotation.x = stride; legs[1].rotation.x = -stride;
    arms[0].rotation.x = -stride * .75; arms[1].rotation.x = stride * .75;
    walker.position.y = .03 + Math.abs(Math.sin(time * 9.5)) * .025 * amount;
  }};
}

/** Geographic rendering: WGS84 coordinates, metres, heading clockwise from north. */
export async function createShanghaiScene(options = {}) {
  const {container, onStatus = () => {}, onLoadError = () => {}} = options;
  const maplibregl = window.maplibregl;
  if (!maplibregl) throw new Error('MapLibre 未加载，请检查本地 vendor 文件。');
  const start = {lng: 121.4896, lat: 31.2390, bearing: 90, ...options.start};
  const [response, landmarkExclusions] = await Promise.all([
    fetch(new URL('../data/map-style.json', import.meta.url)),
    options.landmarkExclusions ? Promise.resolve(options.landmarkExclusions)
      : fetch(new URL('../data/landmark-exclusions.json', import.meta.url))
        .then(result => result.ok ? result.json() : {}).catch(() => ({}))]);
  if (!response.ok) throw new Error(`地图样式读取失败 (${response.status})`);
  const landmarkBoundaries = new Map((landmarkExclusions.landmark_sources || [])
    .map(item => [item.landmark_id, item]));
  const landmarkReplacementIds = {
    building: new Set(landmarkExclusions.building_ids || []),
    building_part: new Set(landmarkExclusions.building_part_ids || [])};
  const style = configureStyle(await response.json());
  const map = new maplibregl.Map({container, style, center: [start.lng, start.lat],
    zoom: options.zoom ?? 20.5, bearing: start.bearing, pitch: 72, maxPitch: 85, maxZoom: 22.5,
    minZoom: 8, renderWorldCopies: false, antialias: true, attributionControl: false,
    maxBounds: [[120.65, 30.55], [122.3, 32.0]],
    canvasContextAttributes: {antialias: true, preserveDrawingBuffer: false}});
  map.addControl(new maplibregl.AttributionControl({compact: true}), 'bottom-right');
  map.dragRotate.disable(); map.keyboard.disable(); map.touchZoomRotate.disableRotation();
  map.getCanvas().setAttribute('aria-label', '上海三维地图，使用漫游控制操作');
  let destroyed = false, mapErrorTime = 0, loadedStyle = false;
  map.on('error', event => {
    if (event.sourceId === OVERTURE_SOURCE) recoverBuildingSource(event.error);
    const now = performance.now();
    if (now - mapErrorTime > 12000) {
      mapErrorTime = now;
      const error = event.error instanceof Error ? event.error : new Error('地图数据暂时无法连接');
      onLoadError(error);
    }
  });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('地图样式加载超时，请检查网络连接。')), 25000);
    map.once('style.load', () => { clearTimeout(timer); loadedStyle = true; resolve(); });
  });
  map.setLight({anchor: 'map', position: [1.5, 120, 40], color: '#fff2d7', intensity: .48});
  if (map.setSky) map.setSky({'sky-color': '#c8e0e7', 'horizon-color': '#e7f0ed',
    'fog-color': '#e7efed', 'sky-horizon-blend': .5, 'horizon-fog-blend': .7, 'fog-ground-blend': .8});
  const sourceId = style.sources.openmaptiles ? 'openmaptiles'
    : Object.keys(style.sources).find(key => style.sources[key].type === 'vector');
  const firstSymbol = map.getStyle().layers.find(layer => layer.type === 'symbol')?.id;
  let buildingSourceId = sourceId, buildingMode = 'osm', recoveryAttempted = false, recoveryInProgress = false;
  let overtureURL = '', overtureRelease = '';
  const baseHeight = ['max', 0, ['to-number', ['coalesce', ['get', 'min_height'], ['get', 'render_min_height'], 0], 0]];
  const overtureHeight = ['case', ['>', ['to-number', ['get', 'height'], 0], 0],
    ['to-number', ['get', 'height'], 12], ['>', ['to-number', ['get', 'num_floors'], 0], 0],
    ['*', ['to-number', ['get', 'num_floors'], 3], 3.2], 12];
  const osmHeight = ['max', 3, ['to-number', ['get', 'render_height'], ['get', 'height'], 12]];
  const buildingBaseFilters = new Map();
  function addBuildingLayer(id, source, sourceLayer, height, visible = true, filter = null) {
    buildingBaseFilters.set(id, filter);
    map.addLayer({id, type: 'fill-extrusion', source, 'source-layer': sourceLayer, minzoom: 13,
      ...(filter ? {filter} : {}), layout: {visibility: visible ? 'visible' : 'none'},
      paint: {'fill-extrusion-color': ['interpolate', ['linear'], height,
        0, '#d7d9d3', 25, '#d3d8d4', 80, '#b7cbd0', 200, '#8baebc'],
      'fill-extrusion-height': ['case', ['boolean', ['feature-state', 'localModel'], false], 0, ['max', ['+', baseHeight, 3], height]],
      'fill-extrusion-base': ['case', ['boolean', ['feature-state', 'localModel'], false], 0, baseHeight],
      'fill-extrusion-opacity': 1, 'fill-extrusion-vertical-gradient': true}}, firstSymbol);
  }
  try {
    const configResponse = await fetch(new URL('../data/buildings-source.json', import.meta.url));
    const config = configResponse.ok ? await configResponse.json() : {};
    overtureRelease = config.release || config.version || '2026-10-21.0';
    overtureURL = config.url || config.pmtiles || `https://tiles.overturemaps.org/${overtureRelease}/buildings.pmtiles`;
    if (typeof overtureURL !== 'string') overtureURL = `https://tiles.overturemaps.org/${overtureRelease}/buildings.pmtiles`;
    overtureURL = overtureURL.replace(/^pmtiles:\/\//, '');
    if (!window.pmtiles?.Protocol) throw new Error('PMTiles 本地运行库未加载');
    if (!window.__shanghaiPMTilesProtocol) {
      window.__shanghaiPMTilesProtocol = new window.pmtiles.Protocol({metadata: true});
      maplibregl.addProtocol('pmtiles', window.__shanghaiPMTilesProtocol.tile);
    }
    map.addSource(OVERTURE_SOURCE, {type: 'vector', url: `pmtiles://${overtureURL}`,
      promoteId: {building: 'id', building_part: 'id'},
      attribution: '© <a href="https://overturemaps.org/" target="_blank">Overture Maps</a> · <a href="https://docs.overturemaps.org/attribution/" target="_blank">建筑数据来源</a>'});
    buildingSourceId = OVERTURE_SOURCE; buildingMode = 'overture';
    addBuildingLayer(BUILDINGS, OVERTURE_SOURCE, 'building', overtureHeight, true,
      ['all', ['!=', ['get', 'is_underground'], true], ['!=', ['get', 'has_parts'], true]]);
    addBuildingLayer(BUILDING_PARTS, OVERTURE_SOURCE, 'building_part', overtureHeight, true,
      ['!=', ['get', 'is_underground'], true]);
    addBuildingLayer(OSM_BUILDINGS, sourceId, 'building', osmHeight, false);
    onStatus({kind: 'building-source', message: 'Overture 建筑轮廓', source: 'overture', release: overtureRelease});
  } catch (error) {
    buildingSourceId = sourceId; buildingMode = 'osm';
    addBuildingLayer(BUILDINGS, sourceId, 'building', osmHeight);
    onStatus({kind: 'building-source', message: '使用 OpenStreetMap 建筑数据', source: 'osm', fallback: true});
    onLoadError(error);
  }
  function useOSMFallback(error) {
    buildingSourceId = sourceId; buildingMode = 'osm';
    for (const id of [BUILDINGS, BUILDING_PARTS]) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', 'none');
    if (map.getLayer(OSM_BUILDINGS)) map.setLayoutProperty(OSM_BUILDINGS, 'visibility', 'visible');
    collisionDirty = true;
    onStatus({kind: 'building-source', message: '建筑服务暂不可用，已切换 OSM', source: 'osm', fallback: true});
    if (error) onLoadError(error);
  }
  async function recoverBuildingSource(error) {
    if (recoveryInProgress || buildingMode !== 'overture') return;
    if (recoveryAttempted) {useOSMFallback(error); return;}
    recoveryAttempted = true; recoveryInProgress = true;
    // Releases have a retention window. Resolve a replacement only when the
    // pinned, reproducible snapshot stops working; ordinary visits need no STAC.
    try {
      const response = await fetch('https://stac.overturemaps.org/catalog.json', {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error('Overture 版本目录暂不可用');
      const catalog = await response.json(), latest = catalog.latest;
      if (!/^\d{4}-\d{2}-\d{2}\.\d+$/.test(latest || '') || latest === overtureRelease) throw error || new Error('Overture 建筑服务暂不可用');
      overtureRelease = latest; overtureURL = `https://tiles.overturemaps.org/${latest}/buildings.pmtiles`;
      map.getSource(OVERTURE_SOURCE).setUrl(`pmtiles://${overtureURL}`);
      onStatus({kind: 'building-source', message: '已自动连接当前建筑数据版本', source: 'overture', release: latest});
    } catch (failure) {useOSMFallback(failure);}
    finally {recoveryInProgress = false;}
  }

  const mercatorOrigin = maplibregl.MercatorCoordinate.fromLngLat(ORIGIN, 0);
  const metreScale = mercatorOrigin.meterInMercatorCoordinateUnits();
  const worldToMercator = new THREE.Matrix4().makeTranslation(mercatorOrigin.x, mercatorOrigin.y, 0)
    .multiply(new THREE.Matrix4().makeScale(metreScale, -metreScale, metreScale))
    .multiply(new THREE.Matrix4().makeRotationX(Math.PI / 2));
  function geographicPosition(lng, lat, altitude = 0) {
    const p = maplibregl.MercatorCoordinate.fromLngLat([lng, lat], altitude);
    return new THREE.Vector3((p.x - mercatorOrigin.x) / metreScale, p.z / metreScale,
      (p.y - mercatorOrigin.y) / metreScale);
  }
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight('#eef6ff', '#a8b4a1', 1.3));
  const sun = new THREE.DirectionalLight('#fff0d5', 2.8); sun.position.set(420, 580, 240); scene.add(sun);
  const fill = new THREE.DirectionalLight('#b6d8ed', .4); fill.position.set(-200, 180, -400); scene.add(fill);
  const walker = makeWalker(); scene.add(walker.group);
  const camera = new THREE.Camera(); camera.matrixAutoUpdate = false;
  let renderer, animationTime = 0, speed = 0, current = {lng: start.lng, lat: start.lat};
  let explicitCamera = null, customLayerReady = false;
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const landmarkRecords = new Map();
  let localDataKind = 'city', streamingSignature = '', streamNoticeTime = 0, streamErrorTime = 0;
  const tileSuppression = new FeatureStateSuppressor(map, OVERTURE_SOURCE);
  // Separate owners keep local tile replacement independent of successful
  // landmark loading. Replaced landmark IDs are excluded from tile ownership.
  const landmarkSuppression = new FeatureStateSuppressor(map, OVERTURE_SOURCE);
  const lowMemory = typeof navigator !== 'undefined' && navigator.deviceMemory && navigator.deviceMemory <= 4;
  const localStreamer = new LocalModelStreamer({scene, loader, suppression:tileSuppression,
    prepareObject:prepareCityObject, disposeObject:disposeModel,
    prepareFeatureIds(ids) {
      return Object.fromEntries(['building','building_part'].map(layer=>
        [layer,(ids[layer] || []).filter(id=>!landmarkReplacementIds[layer].has(id))]));
    },
    maxVisible:lowMemory ? 4 : 6, maxCache:lowMemory ? 6 : 8, concurrency:2,
    memoryBudget:(lowMemory ? 64 : 128)*1024*1024, triangleBudget:lowMemory ? 650000 : 1200000,
    onChange:handleStreamingChange,
    onError(error) {
      if (performance.now()-streamErrorTime > 12000) {streamErrorTime=performance.now();onLoadError(error);}
    }});
  const renderMetrics = {fps:0,drawCalls:0,triangles:0,geometries:0,textures:0};
  let renderFrameCount=0, renderPeriodStart=performance.now();

  const customLayer = {id: CUSTOM, type: 'custom', renderingMode: '3d',
    onAdd(_map, gl) {
      renderer = new THREE.WebGLRenderer({canvas: map.getCanvas(), context: gl, antialias: true, alpha: true});
      renderer.autoClear = false; renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
      customLayerReady = true;
    },
    render(_gl, args) {
      if (!renderer || destroyed) return;
      const matrix = args.defaultProjectionData?.mainMatrix || args;
      const combined = new THREE.Matrix4().fromArray(matrix).multiply(worldToMercator);
      // A translated Three camera gives glTF materials a correct view direction.
      let eye = explicitCamera;
      if (!eye && map.transform?.getCameraLngLat && map.transform?.getCameraAltitude) {
        const p = map.transform.getCameraLngLat();
        eye = {lng: p.lng, lat: p.lat, alt: map.transform.getCameraAltitude()};
      }
      if (eye) {
        camera.position.copy(geographicPosition(eye.lng, eye.lat, eye.alt));
        camera.matrixWorld.makeTranslation(camera.position.x, camera.position.y, camera.position.z);
        camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
        camera.projectionMatrix.copy(combined).multiply(camera.matrixWorld);
      } else {
        camera.matrixWorld.identity(); camera.matrixWorldInverse.identity(); camera.projectionMatrix.copy(combined);
      }
      camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
      renderer.resetState(); renderer.render(scene, camera);
      renderMetrics.drawCalls=renderer.info.render.calls;
      renderMetrics.triangles=renderer.info.render.triangles;
      renderMetrics.geometries=renderer.info.memory.geometries;
      renderMetrics.textures=renderer.info.memory.textures;
      renderFrameCount++;
      const period=performance.now()-renderPeriodStart;
      if (period>=1000) {renderMetrics.fps=renderFrameCount*1000/period;renderFrameCount=0;renderPeriodStart=performance.now();}
      renderer.resetState();
    },
    onRemove() {
      scene.traverse(obj => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) for (const m of Array.isArray(obj.material) ? obj.material : [obj.material]) m.dispose();
      });
      renderer?.dispose();
    }};
  map.addLayer(customLayer);

  function reportLandmarks() {
    const records = [...landmarkRecords.values()];
    onStatus({kind: 'models', message: '地标模型', loaded: records.filter(r => r.status === 'loaded').length,
      total: records.length, failed: records.filter(r => r.status === 'error').length});
  }
  async function loadLandmark(record) {
    if (record.status !== 'idle') return;
    record.status = 'loading'; reportLandmarks();
    try {
      const data = await loader.loadAsync(record.url);
      if (destroyed) {disposeModel(data.scene);return;}
      const group = data.scene; group.name = record.name || record.id;
      group.position.copy(geographicPosition(record.lng, record.lat, record.altitude || 0));
      const latitudeScale = maplibregl.MercatorCoordinate.fromLngLat([record.lng, record.lat]).meterInMercatorCoordinateUnits() / metreScale;
      group.scale.multiplyScalar(latitudeScale * (record.scale || 1));
      group.rotation.y = -(record.heading || 0) * DEG;
      group.traverse(obj => {
        if (obj.isMesh) {
          obj.frustumCulled = true;
          obj.geometry?.computeBoundingSphere();
          if (obj.material) {
            const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
            for (const m of mats) {
              m.envMapIntensity = .55;
              if (m.metalness > .7) m.metalness = .55;
              applyPavingMaterial(m);
            }
          }
        }
      });
      scene.add(group); record.object = group; record.status = 'loaded';
      updateLandmarkVisibility(); reportLandmarks(); map.triggerRepaint();
    } catch (error) {
      record.status = 'error'; reportLandmarks(); onLoadError(new Error(`${record.name || record.id} 模型加载失败：${error.message}`));
    } finally {
      if (!destroyed) updateLandmarkVisibility();
    }
  }
  function updateLandmarkVisibility(force = false) {
    let changed = false;
    const center = map.getCenter(), target = walker.group.visible ? current : {lng: center.lng, lat: center.lat};
    const pending=[];
    for (const record of landmarkRecords.values()) {
      const distance = distanceMetres(target, record);
      const nearby = force || distance < (record.maxDistance || (map.getZoom() < 16 ? 12000 : 3200));
      if (nearby && record.status === 'idle') pending.push({record,distance});
      if (record.object) {
        if (record.object.visible !== nearby) changed = true;
        record.object.visible = nearby;
      }
      const active=record.status==='loaded' && Boolean(record.object?.visible);
      if(active!==record.exclusionActive) {
        record.exclusionActive=active;
        const exact=landmarkBoundaries.get(record.id);
        const ids=active && exact ? {building:exact.building_ids,building_part:exact.building_part_ids} : null;
        landmarkSuppression.setOwner(record.id,ids).then(()=>{if(!destroyed)map.triggerRepaint();});
      }
    }
    // Detailed facades contain substantially more geometry than city blocks.
    // Start the nearest three first and keep decoding/fetch pressure bounded.
    const available=3-[...landmarkRecords.values()].filter(record=>record.status==='loading').length;
    for (const {record} of pending.sort((a,b)=>a.distance-b.distance).slice(0,Math.max(0,available))) loadLandmark(record);
    if (changed) updateBuildingExclusions();
    updateLocalModels();
  }
  function updateBuildingExclusions() {
    for (const id of [BUILDINGS, BUILDING_PARTS, OSM_BUILDINGS]) {
      if (!map.getLayer(id)) continue;
      const base = buildingBaseFilters.get(id), filter = base ? ['all', base] : ['all'];
      // Near GLBs suppress Overture by promoted GERS feature-state, never by
      // a growing city-wide UUID expression. Only the emergency OSM fallback
      // needs a few active tile bounding boxes (there are at most six).
      if (map.getLayer(id).source !== OVERTURE_SOURCE) {
        // Emergency OSM fallback uses confirmed footprints, never a radius
        // that could erase neighboring buildings around a landmark.
        for(const record of landmarkRecords.values()) {
          const boundary=landmarkBoundaries.get(record.id)?.confirmed_boundary;
          if(boundary && record.status==='loaded' && record.object?.visible)filter.push(['!', ['within',boundary]]);
        }
        for (const record of localStreamer.getVisible()) {
          const [west,south,east,north]=record.geometryBounds || record.bounds;
          const polygon={type:'Polygon',coordinates:[[[west,south],[east,south],[east,north],[west,north],[west,south]]]};
          filter.push(['!', ['within', polygon]]);
        }
      }
      map.setFilter(id, filter.length > 1 ? filter : null);
    }
  }
  function setLandmarks(items) {
    const array = Array.isArray(items) ? items : items?.landmarks || items?.features || [];
    for (const item of array) {
      const p = item.properties ? {...item.properties, lng: item.geometry.coordinates[0], lat: item.geometry.coordinates[1]} : item;
      const lng = Number(p.lng ?? p.longitude ?? p.lon), lat = Number(p.lat ?? p.latitude);
      if (!Number.isFinite(lng) || !Number.isFinite(lat) || !p.id || landmarkRecords.has(p.id)) continue;
      const path = p.url || p.model || `../assets/models/${p.id}.glb`;
      const url = /^(https?:|data:)/.test(path) ? path : new URL(path.startsWith('../') ? path : `../${path}`, import.meta.url).href;
      landmarkRecords.set(p.id, {...p, lng, lat, url, status: 'idle'});
    }
    updateLandmarkVisibility(); reportLandmarks();
  }
  function disposeModel(object) {
    if (!object) return;
    const geometries=new Set(), materials=new Set(), textures=new Set();
    object.traverse(child=>{
      if(child.geometry)geometries.add(child.geometry);
      for(const material of child.material ? (Array.isArray(child.material)?child.material:[child.material]) : []) {
        materials.add(material);
        for(const value of Object.values(material))if(value?.isTexture)textures.add(value);
      }
    });
    scene.remove(object);
    for(const geometry of geometries)geometry.dispose();
    for(const material of materials)material.dispose();
    for(const texture of textures){texture.dispose();texture.source?.data?.close?.();}
  }
  function prepareCityObject(group, record) {
    group.name=`${record.name} · mapped city tile`;
    group.position.copy(geographicPosition(record.lng,record.lat,0));
    const scale=maplibregl.MercatorCoordinate.fromLngLat([record.lng,record.lat]).meterInMercatorCoordinateUnits()/metreScale;
    group.scale.multiplyScalar(scale);
    group.traverse(object=>{
      if(!object.isMesh)return;
      // The map projection already supplies the full view transform, so normal
      // Three frustum culling remains valid for the local metre coordinates.
      object.frustumCulled=true;
      object.geometry.computeBoundingSphere();
      for(const material of Array.isArray(object.material)?object.material:[object.material]) {
        if(!material?.color)continue;
        if(/walls/i.test(material.name))material.color.setRGB(.38,.37,.30);
        else material.color.setRGB(.40,.39,.31);
        material.roughness=.88;material.metalness=0;
        applyBuildingMaterial(material);
      }
    });
  }
  function handleStreamingChange(state) {
    const signature=state.active.filter(record=>record.visible).map(record=>record.id).sort().join('|');
    const changed=signature!==streamingSignature;
    if(changed){streamingSignature=signature;updateBuildingExclusions();map.triggerRepaint();}
    const time=performance.now();
    if(changed || time-streamNoticeTime>250) {
      streamNoticeTime=time;
      onStatus({kind:localDataKind==='legacy'?'neighborhoods':'streaming',message:'附近建筑分块',...state});
    }
  }
  function updateLocalModels(force=false) {
    const center=map.getCenter(), walking=walker.group.visible;
    const target=walking?current:{lng:center.lng,lat:center.lat};
    localStreamer.update({...target,zoom:map.getZoom(),bearing:map.getBearing(),mode:walking?'walk':'overview'},force);
  }
  async function setCityManifest(input, settings={}) {
    localDataKind='city';
    try {
      let manifest=input, baseURL=settings.baseURL;
      if(typeof input==='string' || input instanceof URL) {
        const url=new URL(input,document.baseURI);
        const response=await fetch(url,{signal:AbortSignal.timeout(25000)});
        if(!response.ok)throw new Error(`建筑目录读取失败 (${response.status})`);
        manifest=await response.json();baseURL ||= new URL('.',url).href;
      }
      baseURL ||= new URL('../assets/city/',import.meta.url).href;
      await localStreamer.setManifest(manifest,{baseURL});
      updateLocalModels(true);
      return localStreamer.getState();
    } catch(error) {
      onLoadError(new Error(`本地建筑目录暂不可用，继续使用在线地图：${error.message}`));
      return {...localStreamer.getState(),fallback:true,error:error.message};
    }
  }
  async function setNeighborhoods(metadata) {
    // Compatibility for previous per-district releases; it uses the same bounded
    // scheduler and state cleanup rather than a second, unbounded loading path.
    localDataKind='legacy';
    const entries=(Array.isArray(metadata)?metadata:metadata?.models || []).map(item=>({...item,
      id:String(item.district_id || item.id),file:item.url || `assets/districts/${item.file || `${item.district_id}.glb`}`}));
    await localStreamer.setManifest({tiles:entries},{baseURL:new URL('../',import.meta.url).href});
    updateLocalModels(true);
    return localStreamer.getState();
  }
  // Update exclusions only on successful loading, rather than on every frame.
  const originalReport = reportLandmarks;
  reportLandmarks = function () { originalReport(); updateBuildingExclusions(); };

  let collisionDirty = true, collisionUpdated = 0, polygons = [], largePolygons = [], grid = new Map(), roadLines = [];
  map.on('sourcedata', () => { collisionDirty = true; });
  map.on('moveend', () => { collisionDirty = true; updateLandmarkVisibility(); updateLocalModels(true); });
  map.on('move', () => updateLocalModels());
  function sourceFeatures(layer, source = sourceId) {
    try { return map.querySourceFeatures(source, {sourceLayer: layer}); } catch { return []; }
  }
  function rebuildCollisionCache(force = false) {
    const now = performance.now();
    if (!force && (!collisionDirty || now - collisionUpdated < 850)) return;
    if (map.getZoom() < 14) return;
    collisionUpdated = now; collisionDirty = false; polygons = []; largePolygons = []; grid = new Map(); roadLines = [];
    const seen = new Set();
    const inputs = buildingMode === 'overture'
      ? [['building', 'building', buildingSourceId], ['building_part', 'building', buildingSourceId], ['water', 'water', sourceId]]
      : [['building', 'building', sourceId], ['water', 'water', sourceId]];
    for (const [layer, kind, source] of inputs) {
      for (const f of sourceFeatures(layer, source)) {
        if (f.properties?.is_underground === true) continue;
        if (!['Polygon', 'MultiPolygon'].includes(f.geometry.type)) continue;
        const box = boundsOf(f.geometry), key = `${kind}:${box.join(',')}:${f.id || ''}`;
        if (seen.has(key)) continue; seen.add(key);
        const record = {box, geometry: f.geometry, kind}; polygons.push(record);
        const x0 = Math.floor(box[0] * 1000), x1 = Math.floor(box[2] * 1000);
        const y0 = Math.floor(box[1] * 1000), y1 = Math.floor(box[3] * 1000);
        if ((x1-x0+1)*(y1-y0+1) > 120) {largePolygons.push(record); continue;}
        for (let x=x0; x<=x1; x++) for (let y=y0; y<=y1; y++) {
          const key = `${x}:${y}`; if (!grid.has(key)) grid.set(key, []); grid.get(key).push(record);
        }
      }
    }
    for (const f of sourceFeatures('transportation')) {
      const properties = f.properties || {}, type = properties.class || '';
      if (['rail', 'aerialway', 'ferry'].includes(type)) continue;
      const lines = f.geometry.type === 'LineString' ? [f.geometry.coordinates]
        : f.geometry.type === 'MultiLineString' ? f.geometry.coordinates : [];
      for (const coordinates of lines) roadLines.push({coordinates, bridge: properties.brunnel === 'bridge',
        width: ['motorway','trunk','primary','secondary'].includes(type) ? 13 : 6});
    }
  }
  function onBridge(lng, lat) {
    return roadLines.some(road => road.bridge && (nearestOnLine({lng, lat}, road.coordinates)?.distance ?? Infinity) < road.width);
  }
  function collisionAt(lng, lat) {
    rebuildCollisionCache();
    const candidates = [...(grid.get(`${Math.floor(lng*1000)}:${Math.floor(lat*1000)}`) || []), ...largePolygons];
    let water = false;
    for (const record of candidates) {
      const [x0,y0,x1,y1] = record.box;
      if (lng < x0 || lng > x1 || lat < y0 || lat > y1 || !geometryContains(record.geometry,lng,lat)) continue;
      if (record.kind === 'building') return 'building';
      water = true;
    }
    return water && !onBridge(lng,lat) ? 'water' : null;
  }
  async function waitForData(timeout = 8000) {
    // Let a preceding camera teleport schedule its new vector tile requests.
    await sleep(180);
    const end = performance.now()+timeout;
    while (!destroyed && performance.now()<end) {
      if (map.areTilesLoaded()) {rebuildCollisionCache(true); return true;}
      await sleep(150);
    }
    rebuildCollisionCache(true); return false;
  }
  async function findSafePosition({lng,lat,timeout=8000}) {
    const loaded = await waitForData(timeout); rebuildCollisionCache(true);
    if (!collisionAt(lng,lat)) return {lng,lat,adjusted:false,verified:loaded && polygons.length>0};
    const candidates = roadLines.map(road => nearestOnLine({lng,lat},road.coordinates))
      .filter(p=>p && p.distance<250).sort((a,b)=>a.distance-b.distance);
    for (const p of candidates) if (!collisionAt(p.lng,p.lat)) return {...p,adjusted:true,verified:loaded};
    for (let radius=3;radius<=120;radius+=3) for(let i=0;i<16;i++) {
      const p=offsetLngLat({lng,lat},Math.sin(i*Math.PI/8)*radius,Math.cos(i*Math.PI/8)*radius);
      if(!collisionAt(p.lng,p.lat))return {...p,adjusted:true,verified:loaded};
    }
    return {lng,lat,adjusted:false,verified:false};
  }
  function setPlayer(lng,lat,heading=0,playerSpeed=0,dt=.016) {
    current={lng,lat}; speed=playerSpeed; animationTime+=clamp(dt,0,.1);
    const position=geographicPosition(lng,lat,0); walker.group.position.copy(position);
    walker.group.rotation.y=-heading*DEG; walker.animate(speed,animationTime);
    updateLandmarkVisibility(); map.triggerRepaint();
  }
  function setCamera({lng,lat,bearing,pitch=72,zoom=20.5,altitude=0}) {
    explicitCamera=null;
    map.jumpTo({center:[lng,lat],bearing,pitch:clamp(pitch,0,85),zoom:clamp(zoom,8,22.5),elevation:altitude});
  }
  function setCameraFromTo({from,to}) {
    explicitCamera={...from,alt:from.alt??from.altitude??8};
    const opts=map.calculateCameraOptionsFromTo([from.lng,from.lat],explicitCamera.alt,[to.lng,to.lat],to.alt??to.altitude??1.2);
    map.jumpTo({...opts,pitch:clamp(opts.pitch,0,85),zoom:clamp(opts.zoom,8,22.5)});
  }
  function setDistricts(geojson) {
    if(map.getSource(BOUNDARY_SOURCE)){map.getSource(BOUNDARY_SOURCE).setData(geojson);return;}
    map.addSource(BOUNDARY_SOURCE,{type:'geojson',data:geojson});
    map.addLayer({id:'shanghai-district-fill',type:'fill',source:BOUNDARY_SOURCE,maxzoom:13,
      paint:{'fill-color':'#277e83','fill-opacity':.035}},firstSymbol);
    map.addLayer({id:'shanghai-district-line',type:'line',source:BOUNDARY_SOURCE,
      paint:{'line-color':'#36868a','line-width':['interpolate',['linear'],['zoom'],8,1.2,14,2.2,20,.7],
      'line-opacity':['interpolate',['linear'],['zoom'],10,.8,16,.20,19,0],'line-dasharray':[3,2]}},firstSymbol);
  }
  const overviewLabelVisibility = new Map();
  let walkLabelsHidden = false;
  function setWalkModeLabels(hidden) {
    if (walkLabelsHidden === hidden) return;
    walkLabelsHidden = hidden;
    for (const layer of map.getStyle().layers) {
      if (layer.type !== 'symbol') continue;
      const placement = layer.layout?.['symbol-placement'];
      const isLine = typeof placement === 'string' ? placement.includes('line')
        : Array.isArray(placement) && JSON.stringify(placement).includes('line');
      if (!isLine && layer['source-layer'] !== 'transportation_name') continue;
      if (!overviewLabelVisibility.has(layer.id)) overviewLabelVisibility.set(layer.id, map.getLayoutProperty(layer.id, 'visibility') || 'visible');
      map.setLayoutProperty(layer.id, 'visibility', hidden ? 'none' : overviewLabelVisibility.get(layer.id));
    }
  }
  function setDistrictVisibility(visible) {
    for(const id of ['shanghai-district-fill','shanghai-district-line'])if(map.getLayer(id))map.setLayoutProperty(id,'visibility',visible?'visible':'none');
  }
  setPlayer(start.lng,start.lat,start.bearing,0,0);
  setLandmarks(options.landmarks||[]);
  if(options.cityManifest)await setCityManifest(options.cityManifest,options.cityManifestOptions || {});
  else if(options.neighborhoods)await setNeighborhoods(options.neighborhoods);
  onStatus({kind:'ready',message:'三维地图已就绪',loaded:1,total:1});
  return {map,ready:loadedStyle,sourceId,setPlayer,setCamera,setCameraFromTo,collisionAt,findSafePosition,waitForData,
    setLandmarks,setCityManifest,setNeighborhoods,setDistricts,setDistrictVisibility,setWalkModeLabels,showDistricts:setDistrictVisibility,
    setAvatarVisible(visible){setWalkModeLabels(visible);walker.group.visible=visible;updateLocalModels(true);map.triggerRepaint();},
    loadLandmarks(){updateLandmarkVisibility(true);},
    getNeighborhoodState(){return localStreamer.getRecords();},
    getStreamingState(){return {...localStreamer.getState(),renderer:{...renderMetrics}};},
    getLandmarkState(){return [...landmarkRecords.values()].map(({id,name,status})=>({id,name,status}));},
    getLandmarkExclusionState(){return landmarkSuppression.getState();},
    getCollisionState(){rebuildCollisionCache();return {polygons:polygons.length,roads:roadLines.length,updated:collisionUpdated,buildingSource:buildingMode,release:overtureRelease};},
    resize(){map.resize();},
    destroy(){destroyed=true;localStreamer.destroy();landmarkSuppression.destroy({clearMap:true});map.remove();}};
}
