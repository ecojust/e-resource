import * as THREE from '../vendor/three.module.js';

const finitePoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite)
  && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 85;

export function validSourceSection(row) {
  const cap = row.source_section_caps;
  return Boolean(row.replacement_geometry && row.owner?.macro_id && Number.isInteger(row.owner.feature_local_id)
    && row.owner.feature_local_id > 0 && cap && /^[a-f0-9]{64}$/.test(cap.far_sha256)
    && finitePoint(cap.height_reference) && Number.isFinite(cap.base_m) && Number.isFinite(cap.roof_m)
    && cap.roof_m > cap.base_m && cap.geometry?.type === 'MultiLineString'
    && Array.isArray(cap.geometry.coordinates) && cap.geometry.coordinates.length > 0
    && cap.geometry.coordinates.every(line => Array.isArray(line) && line.length >= 2 && line.every(finitePoint)));
}

function sectionMesh(row, project) {
  const cap = row.source_section_caps;
  const lines = cap.geometry.coordinates;
  const origin = project(...lines[0][0]);
  const bottom = project(...cap.height_reference, cap.base_m).y - origin.y;
  const top = project(...cap.height_reference, cap.roof_m).y - origin.y;
  const positions = [], indices = [];
  for (const line of lines) {
    for (const [i, point] of line.entries()) {
      const {x, z} = project(...point).sub(origin);
      const v = positions.length / 3;
      positions.push(x, bottom, z, x, top, z);
      if (i) indices.push(v - 2, v - 1, v, v, v - 1, v + 1);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  // Same linear RGB and roughness as the ordinary macro wall in prepareCityObject.
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color(.38, .40, .39), roughness: .88, side: THREE.DoubleSide, flatShading: true,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = row.id + ' · coarse source cut';
  mesh.position.copy(origin);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

/** Vertical faces exposed by clipping a retained city block. Source and candidate
 * have separate lifetimes: either disappearing must remove the section as well. */
export class CandidateSourceSections {
  constructor(scene, project) {
    this.scene = scene;
    this.project = project;
    this.sections = new Map();
  }

  sync(activeCandidates, visibleMacros) {
    const wanted = new Set();
    let changed = false;
    for (const row of activeCandidates) {
      if (!row.source_section_caps) continue;
      const source = visibleMacros.find(m => m.id === row.owner.macro_id && m.sha256 === row.source_section_caps.far_sha256
        && m.object?.visible && m.object.parent === this.scene);
      if (!source) continue;
      wanted.add(row.id);
      if (this.sections.has(row.id)) continue;
      const mesh = sectionMesh(row, this.project);
      this.scene.add(mesh);
      this.sections.set(row.id, {row, mesh});
      changed = true;
    }
    for (const id of this.sections.keys()) if (!wanted.has(id)) {
      this.remove(id);
      changed = true;
    }
    return changed;
  }

  remove(id) {
    const {mesh} = this.sections.get(id);
    mesh.removeFromParent();
    mesh.geometry.dispose();
    mesh.material.dispose();
    this.sections.delete(id);
  }

  getState() {
    return [...this.sections.values()].map(({row, mesh}) => ({
      id: row.id, ...row.owner, segments: mesh.geometry.index.count / 6, roof_m: row.source_section_caps.roof_m,
    }));
  }

  dispose() {
    for (const id of this.sections.keys()) this.remove(id);
  }
}
