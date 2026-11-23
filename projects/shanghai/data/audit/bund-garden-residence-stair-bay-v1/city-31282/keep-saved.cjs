const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
if (process.argv[1] === '/tmp/shaoxing9-347/handoff/six-view-download.cjs') {
  const [model, output] = process.argv.slice(2);
  const root = process.env.MODEL_FROZEN_ROOT;
  const manifest = JSON.parse(fs.readFileSync(path.join(root,'assets/models/candidates',model,'manifest.json')));
  const verified = new Map(Object.values(manifest.assets).map(i => [path.join(output,'saved-'+i.file), i]));
  const unlink = fs.unlinkSync;
  fs.unlinkSync = function(file) {
    const asset = verified.get(file);
    if (asset) {
      const body = fs.readFileSync(file);
      assert.equal(body.length, asset.bytes);
      assert.equal(createHash('sha256').update(body).digest('hex'), asset.sha256);
      const saved = path.join(output,'saved',asset.file);
      fs.mkdirSync(path.dirname(saved),{recursive:true});
      fs.copyFileSync(file,saved,fs.constants.COPYFILE_EXCL);
      assert.deepEqual(fs.readFileSync(saved),body);
    }
    return unlink.call(fs,file);
  };
}
