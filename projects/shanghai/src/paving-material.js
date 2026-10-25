// Metre-sized paving joints fade out with pixel coverage instead of flickering
// in distant views. Curbs, openings and railings remain real GLB geometry.
export function applyPavingMaterial(material) {
  if (!material || !/BundStonePaving/.test(material.name)) return;
  material.onBeforeCompile = shader => {
    shader.vertexShader=shader.vertexShader
      .replace('#include <common>','#include <common>\nvarying vec3 vPavingWorld;')
      .replace('#include <begin_vertex>','#include <begin_vertex>\nvPavingWorld=(modelMatrix*vec4(position,1.0)).xyz;');
    shader.fragmentShader=shader.fragmentShader
      .replace('#include <common>','#include <common>\nvarying vec3 vPavingWorld;')
      .replace('#include <color_fragment>',`#include <color_fragment>
        vec2 paving=vPavingWorld.xz/vec2(.80,.42);
        paving.x+=mod(floor(paving.y),2.0)*.5;
        vec2 cell=fract(paving);
        vec2 pixel=max(fwidth(paving),vec2(.001));
        vec2 edge=min(cell,1.0-cell);
        vec2 joint=1.0-smoothstep(vec2(.009),vec2(.009)+pixel,edge);
        float nearCoverage=1.0-smoothstep(.10,.6,max(pixel.x,pixel.y));
        float variation=fract(sin(dot(floor(paving),vec2(12.9898,78.233)))*43758.5453);
        diffuseColor.rgb*=mix(1.0,.96+.08*variation,nearCoverage);
        diffuseColor.rgb*=1.0-max(joint.x,joint.y)*.24*nearCoverage;
      `);
  };
  material.customProgramCacheKey=()=> 'bund-paving-v1';
  material.needsUpdate=true;
}
