/** Select the footprint used against a queried vector source. Detailed city GLBs use the primary geometry. */
export function candidateVectorGeometry(clip, sourceName) {
  return sourceName === 'overture-buildings' ? clip.geometry : clip.osm_replacement_geometry ?? clip.geometry;
}
