// WebGL network: glowing directed links, traffic particles, node implosions, shockwaves.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const gsap = window.gsap;
const R = 9;            // layout radius, world units
const SEG = 64;         // samples along each link
const RAD = 7;          // tube sides
const PSLOTS = 16;      // traffic particles per link
const PCAP = 1400;

const HEAT = [[0, '#1d2b8f'], [0.4, '#1b7cff'], [0.75, '#2fd4ff'], [0.94, '#8cf2ff'], [1, '#ffc978']]
  .map(([t, c]) => [t, new THREE.Color(c)]);
export function heat(t, out = new THREE.Color()) {
  t = Math.min(1, Math.max(0, t));
  for (let i = 1; i < HEAT.length; i++) {
    if (t <= HEAT[i][0]) {
      const [t0, c0] = HEAT[i - 1], [t1, c1] = HEAT[i];
      return out.copy(c0).lerp(c1, (t - t0) / (t1 - t0));
    }
  }
  return out.copy(HEAT[HEAT.length - 1][1]);
}
export function sourceColor(k, out = new THREE.Color()) {
  return out.setHSL((0.53 + k * 0.618034) % 1, 0.9, 0.62);
}
export const keyOf = (i, j) => `${i}-${j}`;
/** Load ratio (load / busiest) to colour position: routed networks keep every link above ~0.55. */
const level = r => Math.min(1, Math.max(0, (r - 0.5) / 0.5));

const ARC_VERT = /* glsl */`
attribute vec3 center;
attribute vec3 nrm;
attribute float u;
uniform float thickness;
varying float vU;
varying vec3 vN;
varying vec3 vV;
void main() {
  float taper = 0.55 + 0.45 * smoothstep(0.0, 0.14, u) * (1.0 - smoothstep(0.86, 1.0, u));
  vec3 p = center + nrm * thickness * taper;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vU = u;
  vN = normalize(normalMatrix * nrm);
  vV = normalize(-mv.xyz);
  gl_Position = projectionMatrix * mv;
}`;

const ARC_FRAG = /* glsl */`
uniform vec3 color;
uniform vec3 flashColor;
uniform float opacity;
uniform float grow;
uniform float time;
uniform float speed;
uniform float flow;
uniform float flash;
uniform float dissolve;
uniform float pulse;
uniform float ghost;
uniform float seed;
varying float vU;
varying vec3 vN;
varying vec3 vV;
float hash(float n) { return fract(sin(n * 12.9898 + seed * 78.233) * 43758.5453); }
void main() {
  if (vU > grow) discard;
  if (dissolve > 0.0 && hash(floor(vU * 70.0)) < dissolve) discard;
  float facing = abs(dot(vN, vV));
  float rim = pow(1.0 - facing, 1.7);
  float core = pow(facing, 2.0);
  float dash = pow(max(0.0, sin((vU * 6.0 - time * speed) * 6.2831853)), 12.0);
  float front = grow < 0.999 ? smoothstep(grow - 0.09, grow, vU) : 0.0;
  vec3 c = color * (0.42 + 0.7 * core + 0.45 * rim);
  c += mix(color, vec3(1.0), 0.35) * dash * flow * 1.7;
  c = mix(c, flashColor * 2.4, clamp(flash, 0.0, 1.0));
  c = mix(c, vec3(1.0, 0.16, 0.36) * 1.6, dissolve * 0.85);
  c += vec3(0.9, 1.0, 1.0) * front * 2.6;
  c *= 1.0 + pulse;
  float a = opacity * (0.32 + 0.34 * core + 0.3 * rim + 0.5 * dash * flow + front);
  if (ghost > 0.0) a *= mix(1.0, step(0.45, fract(vU * 22.0 - time * 1.8)), ghost);
  gl_FragColor = vec4(c, clamp(a, 0.0, 1.0));
}`;

const NODE_VERT = /* glsl */`
varying vec3 vN;
varying vec3 vV;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vN = normalize(normalMatrix * normal);
  vV = normalize(-mv.xyz);
  gl_Position = projectionMatrix * mv;
}`;
const NODE_FRAG = /* glsl */`
uniform vec3 color;
uniform float glow;
uniform float opacity;
varying vec3 vN;
varying vec3 vV;
void main() {
  float f = abs(dot(vN, vV));
  float rim = pow(1.0 - f, 2.2);
  vec3 c = mix(color * 0.8, vec3(1.0), 0.45 * pow(f, 3.0)) * (0.55 + 0.5 * f) + color * rim * 1.1;
  gl_FragColor = vec4(c * (1.0 + glow), opacity);
}`;

const POINT_VERT = /* glsl */`
attribute float size;
attribute vec3 pcolor;
uniform float pr;
uniform float time;
varying vec3 vC;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = min(size * pr * (170.0 / max(1.0, -mv.z)), 13.0 * pr);
  vC = pcolor;
  gl_Position = projectionMatrix * mv;
}`;
const POINT_FRAG = /* glsl */`
varying vec3 vC;
void main() {
  vec2 d = gl_PointCoord - 0.5;
  float r = length(d);
  if (r > 0.5) discard;
  float a = 1.0 - smoothstep(0.0, 0.5, r);
  gl_FragColor = vec4(vC * (0.35 + 1.1 * a * a), a);
}`;
const STAR_VERT = /* glsl */`
attribute float size;
attribute float phase;
attribute vec3 pcolor;
uniform float pr;
uniform float time;
varying vec3 vC;
varying float vA;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  float tw = 0.55 + 0.45 * sin(time * (0.6 + phase) + phase * 40.0);
  gl_PointSize = min(size * pr * tw * (120.0 / max(1.0, -mv.z)), 3.2 * pr);
  vC = pcolor; vA = tw;
  gl_Position = projectionMatrix * mv;
}`;
const STAR_FRAG = /* glsl */`
varying vec3 vC;
varying float vA;
void main() {
  float r = length(gl_PointCoord - 0.5);
  if (r > 0.5) discard;
  gl_FragColor = vec4(vC * (1.0 - smoothstep(0.0, 0.5, r)) * vA, 1.0);
}`;

function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, 'rgba(255,255,255,1)');
  grd.addColorStop(0.18, 'rgba(255,255,255,0.55)');
  grd.addColorStop(0.45, 'rgba(255,255,255,0.12)');
  grd.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function tubeGeometry(curve) {
  const frames = curve.computeFrenetFrames(SEG, false);
  const n = (SEG + 1) * (RAD + 1);
  const center = new Float32Array(n * 3), nrm = new Float32Array(n * 3), u = new Float32Array(n);
  const P = new THREE.Vector3();
  let v = 0;
  for (let i = 0; i <= SEG; i++) {
    curve.getPointAt(i / SEG, P);
    const N = frames.normals[i], B = frames.binormals[i];
    for (let j = 0; j <= RAD; j++, v++) {
      const a = (j / RAD) * Math.PI * 2, s = Math.sin(a), c = -Math.cos(a);
      center.set([P.x, P.y, P.z], v * 3);
      nrm.set([c * N.x + s * B.x, c * N.y + s * B.y, c * N.z + s * B.z], v * 3);
      u[v] = i / SEG;
    }
  }
  const idx = [];
  for (let i = 0; i < SEG; i++) {
    for (let j = 0; j < RAD; j++) {
      const a = i * (RAD + 1) + j, b = (i + 1) * (RAD + 1) + j, c = b + 1, d = a + 1;
      idx.push(a, b, d, b, c, d);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(center.slice(), 3));
  g.setAttribute('center', new THREE.BufferAttribute(center, 3));
  g.setAttribute('nrm', new THREE.BufferAttribute(nrm, 3));
  g.setAttribute('u', new THREE.BufferAttribute(u, 1));
  g.setIndex(idx);
  return g;
}

const VIEWS = {
  hero: { pos: [0, 3.2, 27], shift: 0.21, rot: 0.06 },
  story: { pos: [0, 2.6, 28], shift: 0.19, shiftY: 0.02, rot: 0.035 },
  console: { pos: [0, 2.2, 29], shift: -0.21, shiftY: 0.07, rot: 0.02 },
  final: { pos: [0, 1.8, 26], shift: 0.18, rot: 0.03 },
  results: { pos: [0, 9, 36], shift: 0, rot: 0.05 },
};

export class NetworkScene {
  constructor(canvas, story, { labelsEl } = {}) {
    this.story = story;
    this.canvas = canvas;
    this.labelsEl = labelsEl;
    this.time = 0;
    this.flow = 1;
    this.neutral = 0;
    this.webAlpha = 0;
    this.mode = 'heat';
    this.focus = null;
    this.interactive = false;
    this.labelsOn = 0;
    this.arcs = new Map();
    this.ghosts = new Set();
    this.bursts = [];
    this.shocks = [];
    this.shift = 0;
    this.shiftY = 0;
    this.rotSpeed = 0.05;
    this.drag = { on: false, x: 0, y: 0, vx: 0, vy: 0 };
    this.busy = { on: false, text: '' };
    this.mobile = matchMedia('(max-width: 900px)').matches;
    this.reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setClearColor(0x02050c, 1);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.mobile ? 1.5 : 1.75));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    this.renderer = renderer;

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x02050c, 0.012);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 400);
    this.camera.position.set(0, 3.2, 25);
    this.camTarget = new THREE.Vector3(0, 0, 0);

    this.group = new THREE.Group();
    this.group.rotation.x = 0.18;
    this.scene.add(this.group);

    this.composer = new EffectComposer(renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomBase = 0.62;
    this.bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), this.bloomBase, 0.3, 0.55);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());

    this.glowTex = glowTexture();
    this.positions = story.layout.map(p => new THREE.Vector3(p[0] * R, p[1] * R, p[2] * R));
    this.buildStars();
    this.buildShell();
    this.buildNodes();
    this.buildParticles();
    this.buildWeb();
    this.buildFlicker();
    this.buildLabels();
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2(9, 9);
    this.bindPointer();
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  /* ---------------------------------------------------------------- build */
  buildStars() {
    const n = this.mobile ? 900 : 1800;
    const pos = new Float32Array(n * 3), size = new Float32Array(n), phase = new Float32Array(n), col = new Float32Array(n * 3);
    const c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      const r = i < n * 0.22 ? 30 + Math.random() * 14 : 55 + Math.random() * 110;
      const th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1);
      pos.set([r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph) * 0.7, r * Math.sin(ph) * Math.sin(th)], i * 3);
      size[i] = i < n * 0.22 ? 0.5 + Math.random() * 0.7 : 0.8 + Math.random() * 2.2;
      phase[i] = Math.random();
      c.setHSL(Math.random() < 0.85 ? 0.52 + Math.random() * 0.1 : 0.7 + Math.random() * 0.05, 0.6, 0.35 + Math.random() * 0.35);
      col.set([c.r, c.g, c.b], i * 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('size', new THREE.BufferAttribute(size, 1));
    g.setAttribute('phase', new THREE.BufferAttribute(phase, 1));
    g.setAttribute('pcolor', new THREE.BufferAttribute(col, 3));
    this.starMat = new THREE.ShaderMaterial({
      uniforms: { pr: { value: 1 }, time: { value: 0 } }, vertexShader: STAR_VERT, fragmentShader: STAR_FRAG,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.stars = new THREE.Points(g, this.starMat);
    this.stars.frustumCulled = false;
    this.scene.add(this.stars);
  }

  buildShell() {
    const mk = (r, d, op) => {
      const g = new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(r, d));
      const m = new THREE.LineBasicMaterial({ color: 0x5ef2ff, transparent: true, opacity: op, blending: THREE.AdditiveBlending, depthWrite: false });
      return new THREE.LineSegments(g, m);
    };
    this.shell = mk(15.5, 1, 0.045);
    this.shell2 = mk(24, 0, 0.03);
    this.scene.add(this.shell, this.shell2);
  }

  buildNodes() {
    const d = this.story.demand24;
    const tot = d.map((row, i) => row.reduce((a, b) => a + b, 0) + d.reduce((a, r) => a + r[i], 0));
    const max = Math.max(...tot);
    const geo = new THREE.IcosahedronGeometry(1, 3);
    this.nodes = this.positions.map((p, i) => {
      const color = new THREE.Color(i === 23 ? '#b9a6ff' : '#8fe9ff');
      const mat = new THREE.ShaderMaterial({
        uniforms: { color: { value: color }, glow: { value: 0 }, opacity: { value: 1 } },
        vertexShader: NODE_VERT, fragmentShader: NODE_FRAG, transparent: true,
      });
      const mesh = new THREE.Mesh(geo, mat);
      const size = 0.13 + 0.2 * Math.sqrt(tot[i] / max);
      mesh.position.copy(p);
      mesh.userData.index = i;
      const halo = new THREE.Sprite(new THREE.SpriteMaterial({
        map: this.glowTex, color: color.clone(), transparent: true, opacity: 0.3,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }));
      halo.position.copy(p);
      this.group.add(mesh, halo);
      return { mesh, halo, mat, color, size, vis: i === 23 ? 0 : 1, glow: 0, base: color.clone() };
    });
    this.nodeCount = 23;
  }

  buildParticles() {
    const g = new THREE.BufferGeometry();
    this.pPos = new Float32Array(PCAP * 3);
    this.pCol = new Float32Array(PCAP * 3);
    this.pSize = new Float32Array(PCAP);
    g.setAttribute('position', new THREE.BufferAttribute(this.pPos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('pcolor', new THREE.BufferAttribute(this.pCol, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('size', new THREE.BufferAttribute(this.pSize, 1).setUsage(THREE.DynamicDrawUsage));
    this.pointMat = new THREE.ShaderMaterial({
      uniforms: { pr: { value: 1 }, time: { value: 0 } }, vertexShader: POINT_VERT, fragmentShader: POINT_FRAG,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.particles = new THREE.Points(g, this.pointMat);
    this.particles.frustumCulled = false;
    this.group.add(this.particles);

    // bursts share one buffer
    const bg = new THREE.BufferGeometry();
    this.bCap = 900;
    this.bPos = new Float32Array(this.bCap * 3);
    this.bCol = new Float32Array(this.bCap * 3);
    this.bSize = new Float32Array(this.bCap);
    bg.setAttribute('position', new THREE.BufferAttribute(this.bPos, 3).setUsage(THREE.DynamicDrawUsage));
    bg.setAttribute('pcolor', new THREE.BufferAttribute(this.bCol, 3).setUsage(THREE.DynamicDrawUsage));
    bg.setAttribute('size', new THREE.BufferAttribute(this.bSize, 1).setUsage(THREE.DynamicDrawUsage));
    this.burstPts = new THREE.Points(bg, this.pointMat);
    this.burstPts.frustumCulled = false;
    this.group.add(this.burstPts);
  }

  buildWeb() {
    const d = this.story.demand;
    const n = d.length;
    let max = 0;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) max = Math.max(max, d[i][j] + d[j][i]);
    const S = 14, pos = [], col = [];
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const w = (d[i][j] + d[j][i]) / max;
        if (w <= 0) continue;
        const pi = this.positions[i], pj = this.positions[j];
        const ctrl = pi.clone().add(pj).multiplyScalar(0.22);
        const curve = new THREE.QuadraticBezierCurve3(pi, ctrl, pj);
        heat(0.3 + 0.45 * Math.pow(w, 0.6), c).multiplyScalar(0.08 + 0.55 * Math.pow(w, 0.8));
        for (let s = 0; s < S; s++) {
          curve.getPoint(s / S, a); curve.getPoint((s + 1) / S, b);
          pos.push(a.x, a.y, a.z, b.x, b.y, b.z);
          col.push(c.r, c.g, c.b, c.r, c.g, c.b);
        }
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    this.webMat = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
    this.web = new THREE.LineSegments(g, this.webMat);
    this.web.visible = false;
    this.group.add(this.web);
  }

  buildFlicker() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(46 * 2 * 3), 3).setUsage(THREE.DynamicDrawUsage));
    this.flickMat = new THREE.LineBasicMaterial({ color: 0xa78bfa, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
    this.flick = new THREE.LineSegments(g, this.flickMat);
    this.flick.visible = false;
    this.group.add(this.flick);
    this.flickOn = false;
    this.flickClock = 0;
    this.flickCount = 0;
    this.onFlick = null;
    this.probeOn = false;
    this.probeClock = 0;
  }

  buildLabels() {
    this.labels = this.positions.map((_, i) => {
      const el = document.createElement('div');
      el.className = 'node-label';
      el.textContent = String(i + 1);
      el.style.opacity = '0';
      this.labelsEl?.appendChild(el);
      return el;
    });
    this.busyEl = document.createElement('div');
    this.busyEl.className = 'arc-label';
    this.busyEl.style.opacity = '0';
    this.labelsEl?.appendChild(this.busyEl);
  }

  /* ---------------------------------------------------------------- links */
  curveFor(i, j) {
    const pi = this.positions[i], pj = this.positions[j];
    const mid = pi.clone().add(pj).multiplyScalar(0.5);
    const d = pj.clone().sub(pi);
    const len = d.length();
    const ref = mid.lengthSq() > 1e-3 ? mid.clone() : new THREE.Vector3(0, 1, 0);
    const side = new THREE.Vector3().crossVectors(d, ref).normalize();
    const out = ref.normalize();
    const ctrl = mid.clone().addScaledVector(side, len * 0.13).addScaledVector(out, len * 0.12);
    return new THREE.QuadraticBezierCurve3(pi.clone(), ctrl, pj.clone());
  }

  makeArc(i, j) {
    const curve = this.curveFor(i, j);
    const pts = new Float32Array((SEG + 1) * 3);
    const P = new THREE.Vector3();
    for (let s = 0; s <= SEG; s++) { curve.getPointAt(s / SEG, P); pts.set([P.x, P.y, P.z], s * 3); }
    const uniforms = {
      color: { value: new THREE.Color() }, flashColor: { value: new THREE.Color('#e8fbff') },
      opacity: { value: 0 }, grow: { value: 0 }, time: { value: 0 }, speed: { value: 0.4 }, flow: { value: 1 },
      flash: { value: 0 }, dissolve: { value: 0 }, pulse: { value: 0 }, ghost: { value: 0 }, thickness: { value: 0.05 },
      seed: { value: Math.random() * 10 },
    };
    const mat = new THREE.ShaderMaterial({
      uniforms, vertexShader: ARC_VERT, fragmentShader: ARC_FRAG,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const mesh = new THREE.Mesh(tubeGeometry(curve), mat);
    mesh.frustumCulled = false;
    this.group.add(mesh);
    return {
      key: keyOf(i, j), i, j, curve, pts, mesh, mat, u: uniforms,
      t: 0.4, load: 0, alpha: 0, grow: 0, dissolve: 0, flash: 0, ghost: 0, removing: false,
      seed: Math.random(), src: null, busy: false, color: new THREE.Color(), fx: 1,
    };
  }

  disposeArc(arc) {
    this.group.remove(arc.mesh);
    arc.mesh.geometry.dispose();
    arc.mat.dispose();
  }

  removeArc(arc, dur = 0.9, color = '#ff2e63') {
    arc.removing = true;
    gsap.killTweensOf(arc);
    arc.u.flashColor.value.set(color);
    arc.flash = 0.9;
    gsap.to(arc, { flash: 0, duration: dur * 0.5 });
    gsap.to(arc, {
      dissolve: 1, alpha: 0, duration: dur, ease: 'power2.in',
      onComplete: () => { if (arc.removing) { this.disposeArc(arc); this.arcs.delete(arc.key); } },
    });
  }

  /**
   * Morph to a topology. arcs: [[i,j]], loads aligned or null.
   * fresh: highlight colour for links that appear ('record', 'uphill', 'down', 'ice').
   */
  setTopology(arcs, loads, o = {}) {
    const dur = o.duration ?? 1.1;
    const stagger = o.stagger ?? 0.008;
    const max = loads ? Math.max(...loads) : 1;
    const target = new Map();
    arcs.forEach((a, idx) => target.set(keyOf(a[0], a[1]), {
      i: a[0], j: a[1], t: loads ? loads[idx] / max : 0.45, load: loads ? loads[idx] : 0,
      src: o.perSource ? o.perSource[idx] : null,
    }));
    for (const arc of [...this.arcs.values()]) {
      if (!target.has(arc.key) && !arc.removing) this.removeArc(arc, dur * 0.85, o.removeColor);
    }
    const freshColor = { record: '#ffffff', uphill: '#ffb547', down: '#c4b5fd', ice: '#bff6ff' }[o.fresh] || '#e8fbff';
    let n = 0;
    this.busyArc = null;
    for (const [key, t] of target) {
      let arc = this.arcs.get(key);
      if (arc && arc.removing) {
        gsap.killTweensOf(arc);
        arc.removing = false;
        gsap.to(arc, { dissolve: 0, alpha: 1, flash: 0, duration: 0.4 });
      }
      if (!arc) {
        arc = this.makeArc(t.i, t.j);
        this.arcs.set(key, arc);
        arc.t = t.t;
        const delay = (o.delay ?? 0) + stagger * n++;
        gsap.to(arc, { alpha: 1, duration: 0.35, delay });
        gsap.to(arc, { grow: 1, duration: dur, delay, ease: 'power3.out' });
        if (o.fresh) {
          arc.u.flashColor.value.set(freshColor);
          arc.flash = 1;
          gsap.to(arc, { flash: 0, duration: o.fresh === 'record' ? 3.2 : 2.4, delay: delay + dur * 0.7, ease: 'power2.out' });
        }
      } else {
        gsap.to(arc, { t: t.t, duration: dur, ease: 'power2.inOut' });
      }
      arc.load = t.load;
      arc.src = t.src;
      arc.busy = !!loads && t.load === max;
      if (arc.busy) this.busyArc = arc;
    }
    this.maxLoad = max;
  }

  /** Flash a rejected candidate: links it would remove turn red, links it would add appear as ghosts. */
  ghostMove(removed, added, dur = 1.4, color = '#a78bfa') {
    for (const [i, j] of removed) {
      const arc = this.arcs.get(keyOf(i, j));
      if (!arc || arc.removing) continue;
      arc.u.flashColor.value.set('#ff2e63');
      gsap.fromTo(arc, { flash: 0.85 }, { flash: 0, duration: dur, ease: 'power2.in' });
    }
    for (const [i, j] of added) {
      if (this.arcs.has(keyOf(i, j))) continue;
      const g = this.makeArc(i, j);
      g.t = 0.5;
      g.ghost = 1;
      g.ghostColor = new THREE.Color(color);
      this.ghosts.add(g);
      gsap.to(g, { alpha: 0.9, duration: 0.2 });
      gsap.to(g, { grow: 1, duration: dur * 0.35, ease: 'power2.out' });
      gsap.to(g, { alpha: 0, dissolve: 1, duration: dur * 0.45, delay: dur * 0.55, ease: 'power2.in', onComplete: () => { this.ghosts.delete(g); this.disposeArc(g); } });
    }
  }

  /* ---------------------------------------------------------------- nodes */
  setNodeCount(n, animate = true) {
    if (n === this.nodeCount) return;
    const node = this.nodes[23];
    const p = node.mesh.position;
    gsap.killTweensOf(node);
    if (n === 24) {
      gsap.to(node, { vis: 1, duration: animate ? 1.1 : 0, ease: 'back.out(2)' });
      node.glow = 2;
      gsap.to(node, { glow: 0, duration: 1.6 });
      if (animate) { this.burst(p, '#c4b5fd', 70, 1); this.shock(p, '#c4b5fd', 4); }
    } else {
      if (animate) {
        node.color.set('#ff2e63');
        gsap.timeline()
          .to(node, { glow: 2.5, vis: 1.7, duration: 0.45, ease: 'power2.out' })
          .to(node, { vis: 0, glow: 0, duration: 0.35, ease: 'power3.in', onComplete: () => node.color.copy(node.base) });
        this.burst(p, '#ff2e63', 110, -1, 0.45);
        gsap.delayedCall(0.8, () => this.shock(p, '#ff6b9a', 7));
      } else node.vis = 0;
    }
    this.nodeCount = n;
  }

  pulseNodes(color = '#ffffff') {
    this.nodes.forEach((nd, i) => {
      if (i === 23 && this.nodeCount < 24) return;
      gsap.fromTo(nd, { glow: 1.6 }, { glow: 0, duration: 1.4, delay: i * 0.015, ease: 'power2.out' });
    });
  }

  setNodesVisible(on, stagger = 0.04) {
    this.nodes.forEach((nd, i) => {
      if (i === 23) return;
      gsap.to(nd, { vis: on ? 1 : 0, duration: on ? 0.9 : 0.4, delay: on ? i * stagger : 0, ease: on ? 'back.out(2.2)' : 'power2.in' });
    });
  }

  /* ---------------------------------------------------------------- effects */
  burst(center, color, count = 80, dir = 1, life = 1.1) {
    const c = new THREE.Color(color);
    for (let k = 0; k < count; k++) {
      const v = new THREE.Vector3().randomDirection();
      const speed = 2 + Math.random() * 5;
      const start = dir > 0 ? center.clone() : center.clone().addScaledVector(v, 2.2 + Math.random() * 2.5);
      this.bursts.push({ p: start, v: v.multiplyScalar(dir > 0 ? speed : -speed * 1.25), age: 0, life: life * (0.6 + Math.random() * 0.6), c, s: 0.25 + Math.random() * 0.35, target: center.clone(), dir });
    }
  }

  shock(center, color = '#5ef2ff', size = 10) {
    const geo = new THREE.RingGeometry(0.9, 1, 96);
    const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    const m = new THREE.Mesh(geo, mat);
    m.position.copy(center);
    m.scale.setScalar(0.2);
    this.group.add(m);
    const s = { k: 0.2, o: 0.9 };
    this.shocks.push(m);
    gsap.to(s, {
      k: size, o: 0, duration: 1.4, ease: 'power2.out',
      onUpdate: () => { m.scale.setScalar(s.k); mat.opacity = s.o; },
      onComplete: () => { this.group.remove(m); geo.dispose(); mat.dispose(); this.shocks.splice(this.shocks.indexOf(m), 1); },
    });
  }

  celebrate(keys = []) {
    this.shock(new THREE.Vector3(), '#bff6ff', 22);
    gsap.delayedCall(0.18, () => this.shock(new THREE.Vector3(), '#a78bfa', 15));
    this.pulseNodes();
    for (const k of keys) {
      const arc = this.arcs.get(k);
      if (!arc) continue;
      const P = new THREE.Vector3().fromArray(arc.pts, (SEG / 2) * 3);
      this.burst(P, '#e8fbff', 26, 1, 0.9);
    }
    gsap.fromTo(this.bloom, { strength: 1.7, threshold: 0.25 }, { strength: this.bloomBase, threshold: 0.55, duration: 1.8, ease: 'power2.out' });
  }

  /* ---------------------------------------------------------------- state */
  setFlow(v, d = 0.8) { gsap.to(this, { flow: v, duration: d }); }
  setNeutral(v, d = 0.8) { gsap.to(this, { neutral: v ? 1 : 0, duration: d }); }
  setWeb(v, d = 1.2) {
    if (v > 0) this.web.visible = true;
    gsap.to(this, { webAlpha: v, duration: d, onComplete: () => { if (v === 0) this.web.visible = false; } });
  }
  setFlicker(on) {
    this.flickOn = on;
    this.flick.visible = true;
    gsap.to(this.flickMat, { opacity: on ? 0.32 : 0, duration: 0.5, onComplete: () => { if (!on) this.flick.visible = false; } });
  }
  setProbe(on) { this.probeOn = on; }
  setLabels(v) { gsap.to(this, { labelsOn: v ? 1 : 0, duration: 0.6 }); }
  setBusy(on, text = '') { this.busy.on = on; if (text) this.busyEl.textContent = text; }
  setMode(mode) { this.mode = mode; }
  setFocus(k) {
    this.focus = k;
    if (k === null) return;
    let m = 0;
    for (const a of this.arcs.values()) m = Math.max(m, a.src?.find(s => s[0] === k)?.[1] ?? 0);
    this.focusMax = m || 1;
  }
  /** Links carrying traffic from source k, with that traffic. */
  sourceLinks(k) {
    const out = [];
    for (const a of this.arcs.values()) {
      const f = a.src?.find(s => s[0] === k)?.[1] ?? 0;
      if (f > 0 && !a.removing) out.push([a.i, a.j, f]);
    }
    return out;
  }
  setInteractive(on) { this.interactive = on; this.canvas.style.cursor = on ? 'grab' : ''; if (!on) this.hover = null; }

  setView(name, d = 1.6) {
    const v = VIEWS[name] || VIEWS.story;
    this.viewName = name;
    const aspect = window.innerWidth / window.innerHeight;
    const need = 11.5 / (Math.tan(THREE.MathUtils.degToRad(22.5)) * Math.max(aspect, 0.3));
    const base = new THREE.Vector3(...v.pos);
    const dist = Math.max(base.length(), need);
    base.setLength(dist);
    const shift = this.mobile ? 0 : v.shift;
    gsap.to(this.camera.position, { x: base.x, y: base.y, z: base.z, duration: d, ease: 'power3.inOut' });
    gsap.to(this, { shift, shiftY: this.mobile ? 0 : (v.shiftY || 0), rotSpeed: this.reduced ? 0 : v.rot, duration: d, ease: 'power3.inOut' });
  }

  /** Lower the cost on slow GPUs: 1 = pixel ratio 1, 2 = no bloom. */
  degrade(level) {
    if (level >= 1) {
      this.renderer.setPixelRatio(1);
      this.composer.setPixelRatio(1);
      this.composer.setSize(window.innerWidth, window.innerHeight);
      this.pointMat.uniforms.pr.value = 1;
      this.starMat.uniforms.pr.value = 1;
    }
    if (level >= 2) { this.bloom.enabled = false; this.renderer.toneMappingExposure = 1.25; }
  }

  /* ---------------------------------------------------------------- input */
  bindPointer() {
    const el = this.canvas;
    const toNdc = e => {
      this.pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.pointer.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    el.addEventListener('pointerdown', e => {
      if (!this.interactive) return;
      this.drag.on = true; this.drag.moved = 0;
      this.drag.x = e.clientX; this.drag.y = e.clientY;
      el.style.cursor = 'grabbing';
      toNdc(e);
    });
    window.addEventListener('pointerup', e => {
      if (!this.drag.on) return;
      this.drag.on = false;
      el.style.cursor = this.interactive ? 'grab' : '';
      if (this.drag.moved < 6) { toNdc(e); this.pick(true); }
    });
    window.addEventListener('pointermove', e => {
      toNdc(e);
      if (this.drag.on) {
        const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y;
        this.drag.moved += Math.abs(dx) + Math.abs(dy);
        this.drag.vx = dx * 0.005; this.drag.vy = dy * 0.004;
        this.group.rotation.y += this.drag.vx;
        this.group.rotation.x = THREE.MathUtils.clamp(this.group.rotation.x + this.drag.vy, -0.9, 0.9);
        this.drag.x = e.clientX; this.drag.y = e.clientY;
      }
    });
    el.addEventListener('pointerleave', () => { this.pointer.set(9, 9); });
  }

  pick(click = false) {
    if (!this.interactive) return;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const meshes = this.nodes.filter((nd, i) => nd.vis > 0.5 && i < 23).map(nd => nd.mesh);
    const hit = this.raycaster.intersectObjects(meshes, false)[0];
    const k = hit ? hit.object.userData.index : null;
    if (click) { this.locked = k === this.locked ? null : k; }
    const show = this.locked ?? k;
    if (show !== this.hover) {
      this.hover = show;
      this.onHover?.(show);
    }
  }

  /* ---------------------------------------------------------------- frame */
  resize() {
    const w = window.innerWidth, h = window.innerHeight;
    this.mobile = matchMedia('(max-width: 900px)').matches;
    this.renderer.setSize(w, h, false);
    this.composer.setSize(w, h);
    this.bloom.setSize(Math.round(w / 2), Math.round(h / 2));
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    const pr = this.renderer.getPixelRatio();
    this.pointMat.uniforms.pr.value = pr;
    this.starMat.uniforms.pr.value = pr;
    if (this.viewName) this.setView(this.viewName, 0.01);
  }

  update(dt) {
    this.time += dt;
    const t = this.time;
    const w = window.innerWidth, h = window.innerHeight;
    this.camera.setViewOffset(w, h, -this.shift * w, -this.shiftY * h, w, h);
    this.camera.lookAt(this.camTarget);

    if (!this.drag.on) {
      this.group.rotation.y += dt * this.rotSpeed + this.drag.vx;
      this.drag.vx *= 0.93;
      this.drag.vy *= 0.9;
    }
    this.stars.rotation.y += dt * 0.004;
    this.shell.rotation.y -= dt * 0.02; this.shell.rotation.x += dt * 0.006;
    this.shell2.rotation.y += dt * 0.008;
    this.starMat.uniforms.time.value = t;

    // nodes
    for (let i = 0; i < this.nodes.length; i++) {
      const nd = this.nodes[i];
      const s = nd.size * Math.max(0, nd.vis);
      nd.mesh.scale.setScalar(Math.max(1e-4, s));
      nd.mesh.visible = nd.vis > 0.01;
      nd.halo.visible = nd.vis > 0.01;
      const focusDim = this.focus !== null && this.focus !== i ? 0.45 : 1;
      nd.halo.scale.setScalar(s * (3.4 + nd.glow * 3));
      nd.halo.material.opacity = Math.min(1, 0.26 + nd.glow * 0.4) * Math.min(1, nd.vis) * focusDim;
      nd.mat.uniforms.glow.value = nd.glow + (this.focus === i ? 1.2 + 0.4 * Math.sin(t * 5) : 0);
      nd.mat.uniforms.color.value.copy(this.focus === i ? sourceColor(i) : nd.color);
      nd.halo.material.color.copy(this.focus === i ? sourceColor(i) : nd.color);
    }

    // links
    const tmp = new THREE.Color(), ice = new THREE.Color('#7fdcff');
    const focus = this.focus;
    const all = [...this.arcs.values(), ...this.ghosts];
    for (const arc of all) {
      let tt = level(arc.t);
      let col = heat(tt, arc.color);
      if (this.mode === 'source' && focus === null && arc.src && arc.src.length) {
        // dominant commodity tint
        let best = arc.src[0];
        for (const s of arc.src) if (s[1] > best[1]) best = s;
        col = heat(tt, arc.color).lerp(sourceColor(best[0], tmp), 0.6);
      }
      let fx = 1;
      if (focus !== null) {
        const f = arc.src ? (arc.src.find(s => s[0] === focus)?.[1] ?? 0) : 0;
        if (f > 0) { col = sourceColor(focus, arc.color); tt = Math.max(0.35, f / (this.focusMax || 1)); fx = 1; }
        else fx = 0.1;
      }
      if (arc.ghostColor) col = arc.color.copy(arc.ghostColor);
      col.lerp(ice, this.neutral * 0.85);
      arc.fx += (fx - arc.fx) * Math.min(1, dt * 8);
      const u = arc.u;
      u.color.value.copy(col);
      u.time.value = t;
      u.grow.value = arc.grow;
      u.opacity.value = arc.alpha * arc.fx;
      u.flash.value = arc.flash;
      u.dissolve.value = arc.dissolve;
      u.ghost.value = arc.ghost;
      u.flow.value = this.flow * (1 - this.neutral);
      u.speed.value = 0.2 + 0.45 * tt;
      const thick = (0.028 + 0.075 * Math.pow(tt, 1.6)) * (1 - this.neutral) + 0.032 * this.neutral;
      u.thickness.value = thick * (arc.busy && this.busy.on ? 1.25 : 1);
      u.pulse.value = arc.busy && this.busy.on ? 0.35 + 0.35 * Math.sin(t * 6) : 0;
    }

    this.updateParticles(dt);
    this.updateBursts(dt);
    this.updateFlicker(dt);
    this.webMat.opacity = this.webAlpha * (0.75 + 0.25 * Math.sin(t * 1.3));
    for (const m of this.shocks) m.quaternion.copy(this.camera.quaternion);

    this.group.updateMatrixWorld();
    this.updateLabels();
    if (this.interactive && !this.drag.on && this.locked == null) this.pick(false);
    this.composer.render();
  }

  updateParticles() {
    let p = 0;
    const t = this.time;
    const pos = this.pPos, col = this.pCol, size = this.pSize;
    const c = new THREE.Color();
    const flow = this.flow * (1 - this.neutral);
    if (flow > 0.02) {
      for (const arc of this.arcs.values()) {
        const vis = arc.alpha * flow * (1 - arc.dissolve) * arc.fx;
        if (vis < 0.03 || arc.grow < 0.05) continue;
        let tt = level(arc.t), onlyK = null, n;
        if (this.focus !== null) {
          const f = arc.src ? (arc.src.find(s => s[0] === this.focus)?.[1] ?? 0) : 0;
          if (f <= 0) continue;
          onlyK = this.focus;
          tt = f / (this.focusMax || 1);
        }
        n = Math.min(PSLOTS, Math.round(2 + tt * 13));
        const speed = 0.16 + 0.32 * tt;
        let total = 0;
        if (this.mode === 'source' && arc.src && onlyK === null) total = arc.src.reduce((a, s) => a + s[1], 0);
        for (let s = 0; s < n && p < PCAP; s++) {
          const uu = (((s / n + arc.seed + t * speed) % 1) + 1) % 1;
          if (uu > arc.grow) continue;
          const f = uu * SEG, i0 = Math.floor(f), fr = f - i0, i1 = Math.min(SEG, i0 + 1);
          const a = i0 * 3, b = i1 * 3;
          pos[p * 3] = arc.pts[a] + (arc.pts[b] - arc.pts[a]) * fr;
          pos[p * 3 + 1] = arc.pts[a + 1] + (arc.pts[b + 1] - arc.pts[a + 1]) * fr;
          pos[p * 3 + 2] = arc.pts[a + 2] + (arc.pts[b + 2] - arc.pts[a + 2]) * fr;
          if (onlyK !== null) sourceColor(onlyK, c);
          else if (total > 0) {
            let acc = 0;
            const target = ((s + 0.5) / n) * total;
            let k = arc.src[0][0];
            for (const sk of arc.src) { acc += sk[1]; if (acc >= target) { k = sk[0]; break; } }
            sourceColor(k, c);
          } else heat(Math.min(0.97, tt + 0.1), c);
          col[p * 3] = c.r; col[p * 3 + 1] = c.g; col[p * 3 + 2] = c.b;
          size[p] = (0.55 + 0.6 * tt) * vis * (this.mobile ? 1.2 : 1);
          p++;
        }
      }
    }
    const g = this.particles.geometry;
    g.setDrawRange(0, p);
    g.attributes.position.needsUpdate = true;
    g.attributes.pcolor.needsUpdate = true;
    g.attributes.size.needsUpdate = true;
  }

  updateBursts(dt) {
    let p = 0;
    for (let k = this.bursts.length - 1; k >= 0; k--) {
      const b = this.bursts[k];
      b.age += dt;
      if (b.age > b.life) { this.bursts.splice(k, 1); continue; }
      if (b.dir > 0) { b.p.addScaledVector(b.v, dt); b.v.multiplyScalar(0.94); }
      else b.p.lerp(b.target, Math.min(1, dt * 4.5));
      if (p >= this.bCap) continue;
      const life = 1 - b.age / b.life;
      this.bPos.set([b.p.x, b.p.y, b.p.z], p * 3);
      this.bCol.set([b.c.r * life, b.c.g * life, b.c.b * life], p * 3);
      this.bSize[p] = b.s * (0.4 + life);
      p++;
    }
    const g = this.burstPts.geometry;
    g.setDrawRange(0, p);
    g.attributes.position.needsUpdate = true;
    g.attributes.pcolor.needsUpdate = true;
    g.attributes.size.needsUpdate = true;
  }

  randomTopology(n = 23) {
    for (;;) {
      const p1 = [...Array(n).keys()].sort(() => Math.random() - 0.5);
      const p2 = [...Array(n).keys()].sort(() => Math.random() - 0.5);
      let ok = true;
      for (let i = 0; i < n; i++) if (p1[i] === i || p2[i] === i || p1[i] === p2[i]) { ok = false; break; }
      if (ok) return [...p1.map((j, i) => [i, j]), ...p2.map((j, i) => [i, j])];
    }
  }

  updateFlicker(dt) {
    if (this.flickOn) {
      this.flickClock -= dt;
      if (this.flickClock <= 0) {
        this.flickClock = 0.07;
        const arr = this.flick.geometry.attributes.position.array;
        this.randomTopology().forEach(([i, j], k) => {
          const a = this.positions[i], b = this.positions[j];
          arr.set([a.x, a.y, a.z, b.x, b.y, b.z], k * 6);
        });
        this.flick.geometry.attributes.position.needsUpdate = true;
        this.flickCount++;
        this.onFlick?.(this.flickCount);
      }
    }
    if (this.probeOn) {
      this.probeClock -= dt;
      if (this.probeClock <= 0) {
        this.probeClock = 0.16;
        const live = [...this.arcs.values()].filter(a => !a.removing);
        if (live.length > 4) {
          const k = Math.random() < 0.5 ? 2 : 3;
          const pick = [];
          while (pick.length < k) { const a = live[Math.floor(Math.random() * live.length)]; if (!pick.includes(a)) pick.push(a); }
          const heads = pick.map(a => a.j);
          const rot = heads.slice(1).concat(heads[0]);
          const added = pick.map((a, idx) => [a.i, rot[idx]]).filter(([i, j]) => i !== j);
          this.ghostMove(pick.map(a => [a.i, a.j]), added, 0.55, '#ff2e63');
        }
      }
    }
  }

  updateLabels() {
    const w = window.innerWidth, h = window.innerHeight;
    const v = new THREE.Vector3();
    for (let i = 0; i < this.labels.length; i++) {
      const nd = this.nodes[i], el = this.labels[i];
      const vis = Math.min(1, nd.vis) * this.labelsOn;
      if (vis < 0.02) { if (el.style.opacity !== '0') el.style.opacity = '0'; continue; }
      v.copy(nd.mesh.position).applyMatrix4(this.group.matrixWorld).project(this.camera);
      if (v.z > 1) { el.style.opacity = '0'; continue; }
      const x = (v.x * 0.5 + 0.5) * w, y = (-v.y * 0.5 + 0.5) * h;
      el.style.transform = `translate(${x + 9}px, ${y - 20}px)`;
      const dim = this.focus !== null && this.focus !== i ? 0.35 : 1;
      el.style.opacity = String(vis * dim * (v.z > 0.995 ? 0.4 : 1));
      el.classList.toggle('focus', this.focus === i);
    }
    const arc = this.busyArc;
    const show = this.busy.on && arc && !arc.removing && arc.grow > 0.9 && this.focus === null;
    if (show) {
      v.fromArray(arc.pts, (SEG / 2) * 3).applyMatrix4(this.group.matrixWorld).project(this.camera);
      const x = (v.x * 0.5 + 0.5) * w, y = (-v.y * 0.5 + 0.5) * h;
      this.busyEl.style.transform = `translate(${x + 14}px, ${y - 14}px)`;
      this.busyEl.style.opacity = v.z < 1 ? '1' : '0';
    } else this.busyEl.style.opacity = '0';
  }
}
