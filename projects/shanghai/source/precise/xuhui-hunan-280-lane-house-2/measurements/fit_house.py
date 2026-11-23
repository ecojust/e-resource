"""Joint survey of the south street windows and four corner-window jambs in eight photographs."""
from pathlib import Path
import json, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
W = Path(__file__).resolve().parent

def solve(data):
    """Jointly adjust shared facade edges, the door and the curved window to surveyed camera locations.

    Pixel residuals are divided by the recorded edge uncertainty. Camera position, orientation and
    floor dimensions have soft priors; the street positions fix the metric scale. The door and
    corner-window directions are free in plan, independent of the flat south wall.
    """
    origin = np.array([121.43449, 31.21039])
    conv = np.array([111320 * np.cos(np.radians(origin[1])), 110860.0])
    st = data['stations']
    obs = data['observations']
    corner = data['curved_seed']
    s0 = []
    prior = []
    ss = []
    rows = {}
    lower = []
    upper = []

    def var(key, val, scale=np.inf, lo=-np.inf, hi=np.inf):
        a = np.atleast_1d(np.array(val, float))
        n = len(s0)
        s0.extend(a)
        prior.extend(a)
        ss.extend(np.broadcast_to(scale, a.shape))
        lower.extend(np.broadcast_to(lo, a.shape))
        upper.extend(np.broadcast_to(hi, a.shape))
        rows[key] = slice(n, n + len(a))
    var('anchor', [89.0, 0.0, -4.05], [8.0, 5.0, 5.0])
    var('span', [2.05, 3.4, 4.12, 5.95, 9.55, 11.6, 14.7], [0.8, 1.2, 1.2, 1.8, 1.8, 2.1, 2.1])
    for i in range(1, 6):
        var('z' + str(i), [1.22 + 3.24 * (i - 1), 3.27 + 3.24 * (i - 1), 1.58 + 3.24 * (i - 1), 2.62 + 3.24 * (i - 1)], [1.0, 1.0, 1.2, 1.2])
    var('ground_x', np.zeros(8), [0.25, 0.55, 0.44, 0.45, 0.45, 0.45, 0.45, 0.45])
    var('cz', np.zeros(10), np.full(10, 0.39))
    var('ez', np.zeros(10), np.full(10, 0.45))
    var('depth', [-0.18, -0.55, 0.0, -0.18], [0.65, 0.85, 0.7, 0.8])
    var('curve', [-5.5, 0.76, 4.5, 0.87, -45.0], [2.4, 2.0, 1.4, 0.26, 23.0], [-15, -6, 2.5, 0.48, -87], [1.8, 13.0, 7.5, 1.4, -3])
    var('door', [-5.8, 1.2, -5.2, 0.51, 0.07, 2.45], [2.5, 2.4, 2.4, 2.5, 0.12, 0.36])
    camkeys = list(st)

    def axes(az, pit, roll):
        a, e, r = np.radians([az, pit, roll])
        front = np.array([np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)])
        right = np.array([np.cos(a), -np.sin(a), 0])
        down = np.cross(front, right)
        return np.array([right * np.cos(r) + down * np.sin(r), down * np.cos(r) - right * np.sin(r), front])

    def rot_angle(a):
        a = np.radians(a)
        return np.array([[np.cos(a), -np.sin(a), 0.0], [np.sin(a), np.cos(a), 0.0], [0.0, 0.0, 1.0]])
    for k in camkeys:
        station = st[k]
        if k in ['84', '86']:
            c = corner['cameras'][['84', '86'].index(k)]
            orientation = rot_angle(-45)
            C = np.array([-5.5, 0.76, 4.5]) + 0.87 * orientation @ c['centre']
            R = np.array(c['R']) @ orientation.T
            var('C' + k, C, [8, 8, 0.6])
            prior[rows['C' + k].start + 2] = 1.59
            var('R' + k, Rotation.from_matrix(R).as_rotvec(), [np.inf] * 3)
            var('F' + k, [c['f_px']], [58], 500, 950)
        else:
            center = np.r_[(np.array(station['wgs84']) - origin) * conv, station['height_m']]
            var('C' + k, center, [0.3, 0.3, 0.19])
            var('R' + k, [station['az'], station['pitch'], 0.0], [1.35, 1.55, 0.85])
    s0 = np.array(s0)
    prior = np.array(prior)
    ss = np.array(ss)
    active = np.isfinite(ss)
    ids = sorted(set((k for group in obs.values() for k in group)))
    idx = {k: i for i, k in enumerate(ids)}
    picks = {k: np.array([idx[i] for i in rec], dtype=int) for k, rec in obs.items()}
    uv = {k: np.array([v['pixel'] for v in rec.values()]).reshape(-1, 2) for k, rec in obs.items()}
    unc = {k: np.array([v['sigma'] for v in rec.values()])[:, None] for k, rec in obs.items()}

    def scene(s):
        a, ox, oy = s[rows['anchor']]
        en = rot_angle(90 - a)
        o = np.array([ox, oy, 0.0])
        x = s[rows['span']]
        d = s[rows['depth']]
        xs = {'A': (0, x[0]), 'B': (x[1], x[2]), 'C': (x[3], x[4]), 'E': (x[5], x[6])}
        g = s[rows['curve']]
        cr = rot_angle(g[4])
        cp = np.array(corner['four_jambs_local_xy'])
        dz = np.array(corner['opening_heights'])
        sz = np.array(corner['sill_z'])
        door = s[rows['door']]
        pts = {}
        for key in ids:
            if key.startswith('j'):
                l, bar, t = map(int, key[1:].split('_'))
                pts[key] = g[:3] + g[3] * cr @ [*cp[bar], sz[l - 2] + t * dz[l - 2]]
            elif key.startswith('door'):
                left = key.endswith('L')
                top = key[-2] == 'T'
                pts[key] = [*(door[:2] if left else door[2:4]), door[5] if top else door[4]]
            elif key == 'Aground':
                pts[key] = [0, 0, 0]
            else:
                b = key[0]
                l = int(key[1])
                z = s[rows['z' + str(l)]]
                y = 0 if b in 'AB' else d[(0 if b == 'C' else 2) + (l > 1)]
                side = int(key[-1] == 'R')
                upper = int(key[-2] == 'T')
                xx = xs[b][side] + (s[rows['ground_x']][2 * 'ABCE'.index(b) + side] if l == 1 else 0.0)
                zz = z[(2 if b == 'B' else 0) + upper] + (s[rows[b.lower() + 'z']][2 * (l - 1) + upper] if b in 'CE' else 0.0)
                pts[key] = [xx, y, zz]
        cs = {}
        for k, station in st.items():
            C = s[rows['C' + k]]
            r = s[rows['R' + k]]
            if k in ['84', '86']:
                R = Rotation.from_rotvec(r).as_matrix()
                f = s[rows['F' + k]][0]
                w, h = station['size']
            else:
                C = en.T @ (C - o)
                R = axes(*r) @ en
                w, h = (station['width'], station['height'])
                f = w / (2 * np.tan(np.radians(station['hfov'] / 2)))
            K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])
            P = K @ np.column_stack((R, -R @ C))
            cs[k] = (C, R, K, P, [w, h])
        return (cs, pts)

    def residual(s, details=False):
        cs, pts = scene(s)
        pp = np.array([pts[n] for n in ids])
        r = []
        errors = {}
        for k, selection in picks.items():
            C, R, K, _, _ = cs[k]
            h = (pp[selection] - C) @ R.T @ K.T
            err = h[:, :2] / h[:, 2, None] - uv[k]
            errors[k] = {name: v.tolist() for name, v in zip(obs[k], err)}
            r.extend((err / unc[k]).ravel())
        if details:
            return errors
        r.extend((s[active] - prior[active]) / ss[active])
        return np.array(r)
    fit = least_squares(residual, s0, bounds=(np.array(lower), np.array(upper)), loss='soft_l1', max_nfev=180, x_scale='jac', ftol=1e-08, xtol=1e-08)
    s = fit.x
    cs, ps = scene(s)
    err = residual(s, True)
    a, ox, oy = s[rows['anchor']]
    g = s[rows['curve']]
    out = {'origin_wgs': (origin + np.array([ox, oy]) / conv).tolist(), 'x_azimuth_deg': a, 'axes': 'X eastward along Hunan Road, Y north into the house, Z above street. Authoring origin at ground under western jamb of the first (A) window on the straight south wall; corner pipe offsets are independently measured.', 'parameters': {k: s[v].tolist() for k, v in rows.items() if not k[0] in 'CRF'}, 'cameras': {k: {'C': v[0].tolist(), 'R': v[1].tolist(), 'K': v[2].tolist(), 'P': v[3].tolist(), 'size': v[4]} for k, v in cs.items()}, 'points': {k: np.array(v).tolist() for k, v in ps.items()}, 'residual_xy_px': err, 'median_error_px': {k: float(np.median(np.linalg.norm(list(e.values()), axis=1))) for k, e in err.items() if e}, 'evaluations': fit.nfev}
    return out
if __name__ == '__main__':
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else W / 'house-camera-observations.json'
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else W / 'house-cameras.json'
    j = solve(json.loads(source.read_bytes()))
    output.write_text(json.dumps(j, indent=2) + '\n')
    print(j['origin_wgs'], j['x_azimuth_deg'], j['median_error_px'], j['parameters']['curve'], flush=True)
