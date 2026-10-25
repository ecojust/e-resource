/**
 * Generic, metre-scaled facade shading for nearby footprint models.
 * This is a visual aid, not surveyed windows or a source of building heights.
 * The footprint, roof, height and triangle count are unchanged.
 */
export function applyBuildingMaterial(material) {
  if (!material?.isMeshStandardMaterial || !/walls/i.test(material.name) || material.userData.cityFacade) return;
  material.userData.cityFacade = true;
  material.onBeforeCompile = shader => {
    const varyings = '\nvarying vec3 vCityMetres;\nvarying vec3 vCityWallNormal;\n';
    shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>' + varyings)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        // modelMatrix includes the meshopt decode transform and geographic metre offset.
        vCityMetres = (modelMatrix * vec4(transformed, 1.0)).xyz;
        vCityWallNormal = normalize(mat3(modelMatrix) * objectNormal);
      `);
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>' + varyings)
      .replace('#include <color_fragment>', `#include <color_fragment>
        vec3 facadeNormal = normalize(vCityWallNormal);
        vec2 tangent = normalize(vec2(facadeNormal.z, -facadeNormal.x) + vec2(0.00001));
        vec2 facadeUV = vec2(dot(vCityMetres.xz, tangent) / 3.4, vCityMetres.y / 3.2);
        vec2 pixelWidth = max(fwidth(facadeUV), vec2(0.001));
        vec2 cell = abs(fract(facadeUV) - 0.5);
        vec2 windowEdge = vec2(1.0) - smoothstep(vec2(0.27, 0.28) - pixelWidth, vec2(0.27, 0.28) + pixelWidth, cell);
        float resolvable = 1.0 - smoothstep(0.10, 0.35, max(pixelWidth.x, pixelWidth.y));
        float wall = 1.0 - smoothstep(0.1, 0.3, abs(facadeNormal.y));
        float upperFloor = smoothstep(1.8, 2.3, vCityMetres.y);
        float windows = windowEdge.x * windowEdge.y * resolvable * wall * upperFloor;
        diffuseColor.rgb *= mix(vec3(1.0), vec3(0.45, 0.62, 0.66), windows * 0.78);
        // A quiet base course gives a readable street edge without extra geometry.
        float baseCourse = wall * (1.0 - smoothstep(0.35, 0.65, vCityMetres.y));
        diffuseColor.rgb *= 1.0 - 0.12 * baseCourse;
      `);
  };
  material.customProgramCacheKey = () => 'shanghai-generic-facade-v1';
  material.needsUpdate = true;
}
