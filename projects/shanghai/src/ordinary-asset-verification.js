// Only the verified-byte ordinary loader creates receipts. GLB extras alone
// cannot authorize collision/source changes, even if they use the same key.
const receipts = new WeakMap();
const KEY = '__ordinaryVerifiedAsset';
let serial = 0;

export function markVerifiedOrdinaryAsset(scene, {modelId, variant, asset}) {
  if (!scene || typeof scene !== 'object') throw Error('Ordinary GLB has no scene');
  const receipt = Object.freeze({modelId, variant, sha256: asset.sha256,
    file: asset.file, bytes: asset.bytes, serial: ++serial});
  scene.userData ||= {};
  Object.defineProperty(scene.userData, KEY, {value: receipt, enumerable: true, configurable: true, writable: false});
  receipts.set(scene, receipt);
  return receipt;
}

export function getVerifiedOrdinaryAsset(scene) {
  const receipt = scene && receipts.get(scene);
  return receipt && scene.userData?.[KEY] === receipt ? receipt : null;
}
