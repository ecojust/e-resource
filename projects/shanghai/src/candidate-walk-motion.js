// Local model inspection only. No geographic coordinates or city ownership.
export const BODY_RADIUS = .35;
export const WALK_LIMIT = 46;

export function blockedAt(x, z, box, radius = BODY_RADIUS) {
  return Math.abs(x) > WALK_LIMIT || Math.abs(z) > WALK_LIMIT ||
    (x > box.minX - radius && x < box.maxX + radius &&
     z > box.minZ - radius && z < box.maxZ + radius);
}

export function moveOutside(position, dx, dz, box) {
  // Substeps prevent crossing thin facade components even after a slow frame.
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dz) / .12));
  let {x, z} = position;
  for (let i = 0; i < steps; i++) {
    const nx = x + dx / steps, nz = z + dz / steps;
    if (!blockedAt(nx, nz, box)) { x = nx; z = nz; }
    else {
      if (!blockedAt(nx, z, box)) x = nx;
      if (!blockedAt(x, nz, box)) z = nz;
    }
  }
  return {x, z};
}

export function cameraFraction(start, end, box) {
  let enter = 0, exit = 1;
  for (const [axis, lo, hi] of [['x', box.minX - .15, box.maxX + .15], ['z', box.minZ - .15, box.maxZ + .15]]) {
    const delta = end[axis] - start[axis];
    if (Math.abs(delta) < 1e-9) {
      if (start[axis] < lo || start[axis] > hi) return 1;
    } else {
      const a = (lo - start[axis]) / delta, b = (hi - start[axis]) / delta;
      enter = Math.max(enter, Math.min(a, b)); exit = Math.min(exit, Math.max(a, b));
      if (enter > exit) return 1;
    }
  }
  return Math.max(0, Math.min(1, enter - .02));
}
