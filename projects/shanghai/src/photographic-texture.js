/**
 * glTF UVs address the JPEG's stored pixels. Some browsers rotate an embedded
 * JPEG according to EXIF even with imageOrientation:'none'; Blender doesn't.
 * Correct only explicitly documented, non-square EXIF-6 photo maps whose
 * actual decoded dimensions prove that the browser applied that rotation.
 * Original image bytes and the model's stored UVs remain unchanged.
 */
export function correctPhotographicTexture(THREE, material, fallbackSource = null) {
  const texture = material?.map;
  if (!texture || !/^PhotoFacade_/i.test(material.name || '')) return null;
  const source = material.userData?.photographicSource || fallbackSource;
  if (!source) return null;
  if (texture.userData.photographicOrientation) return texture.userData.photographicOrientation;
  const raw = source.rawSize;
  const image = texture.image;
  const width = image?.naturalWidth || image?.width, height = image?.naturalHeight || image?.height;
  const result = {exifOrientation:source.exifOrientation,rawSize:raw,decodedSize:[width,height],corrected:false};
  if (source.uvConvention !== 'stored-pixels' || !Array.isArray(raw) || raw.length !== 2
      || !raw.every(value=>Number.isInteger(value) && value>0)) {
    return {...result,status:'invalid-source-metadata'};
  }
  if (source.exifOrientation === 1) result.status='identity';
  else if (source.exifOrientation !== 6 || raw[0] === raw[1]) return {...result,status:'unsupported-orientation'};
  else if (width === raw[0] && height === raw[1]) result.status='decoder-kept-stored-pixels';
  else if (width === raw[1] && height === raw[0]) {
    // Clockwise EXIF 6: displayed top-left UV = (1 - storedV, storedU).
    // Apply after any pre-existing glTF texture-coordinate transform.
    if (texture.matrixAutoUpdate) texture.updateMatrix();
    texture.matrix.premultiply(new THREE.Matrix3().set(0,-1,1, 1,0,0, 0,0,1));
    texture.matrixAutoUpdate=false;
    result.corrected=true; result.status='decoder-rotation-compensated';
  } else return {...result,status:'unexpected-decoded-size'};
  texture.userData.photographicOrientation=result;
  return result;
}
