import {registerHooks} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
const main = '/workspace/shanghai_project/';
const fixed = pathToFileURL(path.join(root, 'payload/src/realistic-lighting.js')).href;
const original = pathToFileURL(main + 'src/realistic-lighting.js').href;
const mainURL = value => pathToFileURL(main + value).href;

registerHooks({resolve(specifier, context, next) {
  if (specifier === 'three') return {url: mainURL('vendor/three.module.js'), shortCircuit: true};
  if (context.parentURL === fixed) {
    if (specifier === '../vendor/HDRLoader.js') return {url: mainURL('vendor/HDRLoader.js'), shortCircuit: true};
    if (specifier === './photographic-glass.js') return {url: mainURL('src/photographic-glass.js'), shortCircuit: true};
  }
  if (process.env.SHADOW_FIX_REDIRECT === '1' && context.parentURL
      && new URL(specifier, context.parentURL).href === original) {
    return {url: fixed, shortCircuit: true};
  }
  return next(specifier, context);
}});
