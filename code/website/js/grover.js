// Act II console: replays every round of the Grover walk from the logged data.
import { keyOf } from './scene.js';

const fmt = n => Math.round(n).toLocaleString('en-US');
const pct = x => `${(x * 100).toFixed(1)}%`;
const ease = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const easeOut = t => 1 - Math.pow(1 - t, 3);
const clamp01 = t => Math.max(0, Math.min(1, t));
const hash = k => { const s = Math.sin(k * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
export const ICON = {
  play: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M7 4.5v15l12.5-7.5z" fill="currentColor"/></svg>',
  pause: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M6.5 4.5h4v15h-4zM13.5 4.5h4v15h-4z" fill="currentColor"/></svg>',
};
const topoKey = arcs => arcs.map(a => a[0] * 32 + a[1]).sort((a, b) => a - b).join(',');

function sequence(layers) {
  const seq = [['pool', 1.15, 0]];
  for (let l = 0; l < layers; l++) seq.push(['oracle', l ? 0.6 : 0.8, l], ['diffuse', l ? 0.8 : 1.0, l]);
  seq.push(['measure', 1.4, 0], ['route', 1.4, 0], ['move', 1.8, 0]);
  return seq;
}

function setupCanvas(cv) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const r = cv.getBoundingClientRect();
  const w = Math.max(10, r.width), h = Math.max(10, r.height);
  if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) {
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
  }
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

export class GroverConsole {
  constructor(story, scene, hooks) {
    this.story = story;
    this.scene = scene;
    this.hooks = hooks;
    this.rounds = story.walk.rounds;
    this.slack = 18000;
    this.speed = 2.5;
    this.playing = false;
    this.active = false;
    this.visible = false;
    this.started = false;
    this.revealed = 0;
    this.shots = [];

    const states = new Map();
    const reg = (arcs, loads, z) => states.set(topoKey(arcs), { arcs, loads, z });
    reg(story.hand_in.arcs, story.hand_in.loads, story.hand_in.z_lp);
    story.records.forEach(s => reg(s.arcs, s.loads, s.z_lp));
    this.rounds.forEach(r => reg(r.current_arcs, r.current_loads, r.current_lp));
    this.before = this.rounds.map((r, idx) => {
      const prev = idx === 0
        ? { arcs: story.hand_in.arcs, loads: story.hand_in.loads, z: story.hand_in.z_lp, record: story.hand_in.score }
        : { arcs: this.rounds[idx - 1].current_arcs, loads: this.rounds[idx - 1].current_loads, z: this.rounds[idx - 1].current_lp, record: this.rounds[idx - 1].checked_best };
      const after = new Set(r.current_arcs.map(a => keyOf(a[0], a[1])));
      r.step.added.forEach(a => after.delete(keyOf(a[0], a[1])));
      const arcs = [...after].map(k => k.split('-').map(Number)).concat(r.step.removed);
      const found = states.get(topoKey(arcs));
      return found ? { ...found, record: prev.record } : prev;
    });

    const $ = id => document.getElementById(id);
    this.el = {
      round: $('roundNum'), kind: $('moveKind'), text: $('moveText'), card: $('moveCard'),
      caption: $('caption'), k: $('ringK'), v: $('ringV'), s: $('ringS'),
      phases: [...document.querySelectorAll('#phases span')],
      play: $('btnPlay'), tallyU: $('tallyU'), tallyG: $('tallyG'),
      ring: $('ring'), lp: $('lpstrip'), timeline: $('timeline'),
    };
    this.el.play.addEventListener('click', () => this.toggle());
    $('btnPrev').addEventListener('click', () => this.goto(Math.max(0, this.r - (this.ph === 0 && this.pt < 0.3 ? 1 : 0))));
    $('btnNext').addEventListener('click', () => this.nextRecord());
    document.querySelectorAll('.speed .chip').forEach(b => b.addEventListener('click', () => {
      document.querySelectorAll('.speed .chip').forEach(x => x.classList.toggle('on', x === b));
      this.speed = Number(b.dataset.speed);
    }));
    this.el.timeline.addEventListener('click', e => {
      const rect = this.el.timeline.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const { x0, x1 } = this.tlBox || { x0: 56, x1: rect.width - 16 };
      const round = Math.round(((x - x0) / (x1 - x0)) * 52);
      if (round >= 1 && round <= 52) this.goto(round - 1, true);
    });
    // Pool indices are arbitrary labels; a fixed shuffle spreads them around the ring.
    this.slot = this.rounds.map(r => {
      const n = r.pool, perm = [...Array(n).keys()];
      let seed = r.round * 9973;
      for (let i = n - 1; i > 0; i--) { seed = (seed * 16807) % 2147483647; const j = seed % (i + 1); [perm[i], perm[j]] = [perm[j], perm[i]]; }
      return perm;
    });
    this.prepare(0, false);
  }

  /* ---------------------------------------------------------------- control */
  setVisible(v) { this.visible = v; if (!v && this.playing) { this.wasPlaying = true; this.pause(); } else if (v && this.wasPlaying && this.active) { this.wasPlaying = false; this.play(); } }

  enter() {
    this.active = true;
    this.scene.setMode('heat');
    this.scene.setFocus(null);
    this.scene.setBusy(false);
    this.syncScene(0.9);
    this.updateHud();
    if (!this.started) {
      this.started = true;
      clearTimeout(this.autoT);
      this.autoT = setTimeout(() => { if (this.active) this.play(); }, 900);
    }
  }

  leave() { this.active = false; this.wasPlaying = false; clearTimeout(this.autoT); this.pause(); }

  play() {
    if (this.done) { this.done = false; this.goto(0, true); }
    this.playing = true;
    this.el.play.innerHTML = ICON.pause;
    this.el.play.setAttribute('aria-label', 'Pause');
  }
  pause() {
    this.playing = false;
    this.el.play.innerHTML = ICON.play;
    this.el.play.setAttribute('aria-label', 'Play');
  }
  toggle() { this.started = true; (this.playing ? this.pause() : this.play()); }

  goto(idx, play = this.playing) {
    this.done = false;
    this.prepare(idx, true);
    if (play) this.play();
  }

  nextRecord() {
    let idx = this.rounds.findIndex((r, i) => i > this.r && r.moved === 'record');
    if (idx < 0) idx = this.rounds.findIndex(r => r.moved === 'record');
    this.started = true;
    this.goto(idx, true);
  }

  /* ---------------------------------------------------------------- rounds */
  prepare(idx, snap) {
    const R = this.rounds[idx];
    this.r = idx;
    this.R = R;
    this.B = this.before[idx];
    this.seq = sequence(R.layers);
    this.ph = 0;
    this.pt = 0;
    this.shots = [];
    const N = R.pool;
    const order = R.energy.map((e, k) => k).sort((a, b) => R.energy[a] - R.energy[b] || a - b);
    this.rank = new Float32Array(N);
    order.forEach((k, r) => { this.rank[k] = r / N; });
    this.marked = new Uint8Array(N);
    for (let r = 0; r < R.marked; r++) this.marked[order[r]] = 1;
    // Exact two-class amplitudes after each oracle and diffusion.
    const M = R.marked;
    let aM = 1 / Math.sqrt(N), aU = 1 / Math.sqrt(N);
    this.stages = [[aM, aU, 0]];
    for (let l = 0; l < R.layers; l++) {
      aM = -aM;
      this.stages.push([aM, aU, 0]);
      const mean = (M * aM + (N - M) * aU) / N;
      aM = 2 * mean - aM; aU = 2 * mean - aU;
      this.stages.push([aM, aU, mean]);
    }
    this.maxAmp = Math.max(...this.stages.map(s => Math.abs(s[0])));
    this.pFinal = M * aM * aM;
    this.pMarked0 = M / N;
    this.distinct = R.quantum_ids.length;
    // Buckets for drawing: 18 colour bands for unmarked, 1 for marked.
    this.buckets = Array.from({ length: 18 }, () => []);
    this.markedIdx = [];
    for (let k = 0; k < N; k++) {
      if (this.marked[k]) this.markedIdx.push(k);
      else this.buckets[Math.max(0, Math.min(17, Math.floor(((this.rank[k] - 0.12) / 0.88) * 18)))].push(k);
    }
    const lps = R.quantum_ids.map(i => R.lp[i]).filter(v => v !== null);
    this.lpMin = Math.min(...lps, this.B.record);
    this.revealed = idx;
    if (snap) {
      this.syncScene(0.7);
      this.updateHud();
    }
    this.el.round.textContent = String(R.round).padStart(2, '0');
    this.setMoveCard('ready');
    this.enterPhase();
    this.updateTally();
  }

  syncScene(d = 0.9) {
    if (!this.active) return;
    const atMove = this.seq && this.seq[this.ph][0] === 'move';
    const s = atMove && this.R.moved !== 'stay'
      ? { arcs: this.R.current_arcs, loads: this.R.current_loads, z: this.R.current_lp }
      : this.B;
    this.scene.setTopology(s.arcs, s.loads, { duration: d });
  }

  updateHud() {
    const rec = this.revealed > 0 ? this.rounds[this.revealed - 1].checked_best : this.story.hand_in.score;
    this.hooks.hud?.(rec, `Grover walk · round ${this.R.round} of 52`);
  }

  enterPhase() {
    const [name, , layer] = this.seq[this.ph];
    const R = this.R;
    this.el.phases.forEach(sp => {
      const idx = this.seq.findIndex(s => s[0] === sp.dataset.p);
      const cur = sp.dataset.p === name;
      sp.classList.toggle('on', cur);
      const lastIdx = this.seq.map(s => s[0]).lastIndexOf(sp.dataset.p);
      sp.classList.toggle('done', !cur && lastIdx < this.ph && idx >= 0);
    });
    const q = R.index_qubits;
    const cap = this.el.caption;
    if (name === 'pool') {
      cap.innerHTML = R.restart
        ? '<b>Restart.</b> Nineteen rounds without a record, so the walk returns to the best network.'
        : `Permute the heads of 2 to 6 links: <b>${fmt(R.pool)}</b> new degree-preserving rewirings. An index register of <b>${q} qubits</b> holds all of them in uniform superposition.`;
    } else if (name === 'oracle') {
      cap.innerHTML = `<b>Phase oracle${layer ? ' again' : ''}.</b> It flips the sign of the <b>${R.marked}</b> rewirings with the lowest estimated congestion, the best 12% according to cheap shortest-path routings.`;
    } else if (name === 'diffuse') {
      cap.innerHTML = `<b>Diffusion.</b> Every amplitude is reflected about the mean, so the flipped states grow and the rest shrink. Iteration ${layer + 1} of ${R.layers}.`;
    } else if (name === 'measure') {
      cap.innerHTML = `<b>Measure 2,048 shots.</b> ${pct(this.pFinal)} of them land on a marked state. The first <b>${this.distinct}</b> distinct outcomes go on to exact routing.`;
      this.spawnShots();
    } else if (name === 'route') {
      cap.innerHTML = 'Each measured rewiring is scored with the <b>exact multicommodity-flow LP</b>. Greedy and uniform selection get the same budget, for comparison only.';
    } else if (name === 'move') {
      this.applyMove();
    }
  }

  applyMove() {
    const R = this.R;
    const k = R.moved;
    const delta = R.best_lp - this.B.z;
    if (k === 'record') {
      const gain = this.B.record - R.checked_best;
      this.scene.setTopology(R.current_arcs, R.current_loads, { fresh: 'record', duration: 1.25 });
      this.scene.celebrate(R.step.added.map(a => keyOf(a[0], a[1])));
      this.hooks.record?.(R.checked_best, gain);
      this.el.caption.innerHTML = `<b>New checked record: ${fmt(R.checked_best)}</b>, ${fmt(gain)} lower. Integer routing and QOBLIB's checker confirm it. ${R.step.added.length} links rewired.`;
    } else if (k === 'downhill' || k === 'uphill') {
      this.scene.setTopology(R.current_arcs, R.current_loads, { fresh: k === 'uphill' ? 'uphill' : 'down', duration: 1.1 });
      this.el.caption.innerHTML = k === 'uphill'
        ? `<b>Uphill step</b> to ${fmt(R.best_lp)}. With probability 0.35 the walk accepts a slightly worse network to leave the basin.`
        : `<b>Downhill step</b> to ${fmt(R.best_lp)}, better than where the walk stood but not a record.`;
    } else {
      this.scene.ghostMove(R.move.removed, R.move.added, 1.6);
      this.el.caption.innerHTML = `The best measured candidate scores ${R.best_lp === null ? 'above the cutoff' : fmt(R.best_lp)}, which is not good enough. <b>The walk stays</b>, and the candidate's links flash and fade.`;
    }
    this.revealed = this.r + 1;
    this.setMoveCard(k, delta);
    this.updateHud();
    this.updateTally();
  }

  setMoveCard(kind, delta) {
    const R = this.R;
    const card = this.el.card;
    card.className = `move-card ${kind}`;
    const n = R.move.added.length;
    if (kind === 'ready') {
      this.el.kind.textContent = `ROUND ${R.round} · ${fmt(R.pool)} CANDIDATES`;
      this.el.text.textContent = `Record so far: ${fmt(this.B.record)}. The walk stands at ${fmt(this.B.z)}.`;
      return;
    }
    const label = { record: 'NEW RECORD', downhill: 'ACCEPTED · DOWNHILL', uphill: 'ACCEPTED · UPHILL', stay: 'REJECTED' }[kind];
    this.el.kind.textContent = `${label} · ${n} LINKS`;
    const d = delta === undefined || R.best_lp === null ? '' : ` (${delta < 0 ? '−' : '+'}${fmt(Math.abs(delta))})`;
    this.el.text.textContent = kind === 'record'
      ? `${fmt(this.B.record)} → ${fmt(R.checked_best)}. Grover's pick, checked with integer flows.`
      : kind === 'stay'
        ? `Best candidate ${R.best_lp === null ? 'above the cutoff' : fmt(R.best_lp)}${d}. The network stays as it is.`
        : `Walk moves to ${fmt(R.best_lp)}${d}. Record unchanged at ${fmt(R.checked_best)}.`;
  }

  updateTally() {
    const t = { u: [0, 0, 0], g: [0, 0, 0] };
    for (let i = 0; i < this.revealed; i++) {
      const b = this.rounds[i].best;
      for (const [m, key] of [['uniform', 'u'], ['greedy', 'g']]) {
        const q = b.quantum ?? Infinity, o = b[m] ?? Infinity;
        if (q === Infinity && o === Infinity) t[key][1]++;
        else if (q < o - 0.5) t[key][0]++;
        else if (q > o + 0.5) t[key][2]++;
        else t[key][1]++;
      }
    }
    this.el.tallyU.textContent = t.u.join(' · ');
    this.el.tallyG.textContent = t.g.join(' · ');
  }

  spawnShots() {
    const R = this.R;
    this.shots = [];
    for (const [k, c] of Object.entries(R.shots)) {
      for (let s = 0; s < c; s++) this.shots.push({ k: Number(k), d: Math.random() * 0.62, j: Math.random() });
    }
  }

  finishRound() {
    if (this.r < this.rounds.length - 1) this.prepare(this.r + 1, false);
    else {
      this.pause();
      this.done = true;
      this.ph = this.seq.length - 1;
      this.pt = this.seq[this.ph][1];
      this.el.caption.innerHTML = `<b>Walk complete.</b> Five records in 52 rounds: 639,739 → <b>632,319</b>. Press play to watch it again.`;
    }
  }

  /* ---------------------------------------------------------------- frame */
  tick(dt) {
    if (!this.visible) return;
    if (this.playing) {
      this.pt += dt * this.speed;
      let guard = 0;
      while (this.playing && this.pt >= this.seq[this.ph][1] && guard++ < 8) {
        this.pt -= this.seq[this.ph][1];
        this.ph++;
        if (this.ph >= this.seq.length) { this.finishRound(); break; }
        this.enterPhase();
      }
    }
    this.draw();
  }

  /** Displayed amplitudes (marked, unmarked), the reflection mean, and the sweep fraction. */
  amplitudes() {
    const [name, dur, layer] = this.seq[this.ph];
    const p = clamp01(this.pt / dur);
    const S = this.stages;
    if (name === 'pool') return { aM: S[0][0] * easeOut(p), aU: S[0][1] * easeOut(p), sweep: easeOut(clamp01(p * 1.25)), mean: null, p };
    if (name === 'oracle') {
      const from = S[layer * 2], to = S[layer * 2 + 1], e = ease(clamp01(p * 1.5));
      return { aM: from[0] + (to[0] - from[0]) * e, aU: to[1], sweep: 1, mean: null, p };
    }
    if (name === 'diffuse') {
      const from = S[layer * 2 + 1], to = S[layer * 2 + 2], e = ease(clamp01((p - 0.15) / 0.75));
      return { aM: from[0] + (to[0] - from[0]) * e, aU: from[1] + (to[1] - from[1]) * e, sweep: 1, mean: to[2], p };
    }
    const last = S[S.length - 1];
    return { aM: last[0], aU: last[1], sweep: 1, mean: null, p };
  }

  draw() {
    this.drawRing();
    this.drawLP();
    this.drawTimeline();
  }

  drawRing() {
    const { ctx, w, h } = setupCanvas(this.el.ring);
    const R = this.R;
    const N = R.pool;
    const cx = w / 2, cy = h / 2, S = Math.min(w, h);
    const R0 = S * 0.355;
    const L = (S * 0.125) / this.maxAmp;
    const [name] = this.seq[this.ph];
    const A = this.amplitudes();
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';

    // decorative outer dial
    const t = performance.now() / 1000;
    ctx.strokeStyle = 'rgba(94,242,255,0.10)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(cx, cy, S * 0.492, 0, Math.PI * 2); ctx.stroke();
    for (let q = 0; q < R.index_qubits; q++) {
      const a0 = t * 0.15 + (q / R.index_qubits) * Math.PI * 2;
      ctx.strokeStyle = 'rgba(167,139,250,0.35)';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(cx, cy, S * 0.492, a0, a0 + 0.25); ctx.stroke();
    }
    // base ring
    ctx.strokeStyle = 'rgba(150,210,255,0.22)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(cx, cy, R0, 0, Math.PI * 2); ctx.stroke();
    // reflection axis during diffusion
    if (A.mean !== null) {
      const rm = R0 + A.mean * L;
      ctx.setLineDash([3, 5]);
      ctx.strokeStyle = `rgba(196,181,253,${0.75 * Math.sin(Math.PI * clamp01(A.p * 1.1))})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(cx, cy, rm, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);
    }

    const slot = this.slot[this.r];
    const angle = k => -Math.PI / 2 + (slot[k] / N) * Math.PI * 2;
    const sweepMax = A.sweep * N;
    const bar = (k, len, path) => {
      if (slot[k] > sweepMax) return;
      const a = angle(k), c = Math.cos(a), s = Math.sin(a);
      path.moveTo(cx + c * R0, cy + s * R0);
      path.lineTo(cx + c * (R0 + len), cy + s * (R0 + len));
    };
    const lw = Math.max(0.9, ((Math.PI * 2 * R0) / N) * 0.75);
    // unmarked, coloured by estimated congestion rank
    const lenU = A.aU * L;
    for (let b = 0; b < this.buckets.length; b++) {
      const f = b / 17;
      const hue = 205 + f * 70, light = 62 - f * 26;
      ctx.strokeStyle = `hsla(${hue},85%,${light}%,0.85)`;
      ctx.lineWidth = lw;
      ctx.beginPath();
      for (const k of this.buckets[b]) bar(k, lenU, ctx);
      ctx.stroke();
    }
    // marked
    const lenM = A.aM * L;
    const neg = A.aM < 0;
    const glow = clamp01(Math.abs(A.aM) / this.maxAmp);
    for (const pass of [0, 1]) {
      ctx.strokeStyle = neg
        ? `rgba(255,70,130,${pass ? 0.95 : 0.22})`
        : `rgba(${pass ? '235,253,255' : '94,242,255'},${pass ? 0.95 : 0.18 + 0.25 * glow})`;
      ctx.lineWidth = pass ? lw * 1.15 : lw * 4.2;
      ctx.beginPath();
      for (const k of this.markedIdx) bar(k, lenM, ctx);
      ctx.stroke();
    }
    // oracle marks at the base
    if (name !== 'pool') {
      ctx.fillStyle = neg ? 'rgba(255,90,150,0.9)' : 'rgba(191,246,255,0.75)';
      for (const k of this.markedIdx) {
        const a = angle(k);
        ctx.fillRect(cx + Math.cos(a) * (R0 - 5) - 1, cy + Math.sin(a) * (R0 - 5) - 1, 2, 2);
      }
    }
    // measurement: shots fly from the tips to the centre
    if (name === 'measure' || (name === 'route' && this.pt < 0.35)) {
      const p = name === 'measure' ? this.pt / this.seq[this.ph][1] : 1 + this.pt;
      ctx.fillStyle = 'rgba(220,250,255,0.9)';
      let landed = 0;
      for (const sh of this.shots) {
        const local = clamp01((p - sh.d) / 0.32);
        if (local <= 0) continue;
        if (local >= 1) { landed++; continue; }
        const a = angle(sh.k);
        const len = this.marked[sh.k] ? lenM : lenU;
        const r0 = R0 + len, e = easeOut(local);
        const r = r0 * (1 - e) + S * 0.06 * e;
        const sw = (sh.j - 0.5) * 0.6 * Math.sin(Math.PI * local);
        const x = cx + Math.cos(a + sw) * r, y = cy + Math.sin(a + sw) * r;
        ctx.fillRect(x - 1, y - 1, 2.2, 2.2);
      }
      this.landed = landed;
    }
    ctx.globalCompositeOperation = 'source-over';
    this.updateCenter(name, A);
  }

  updateCenter(name, A) {
    const R = this.R;
    let k, v, s;
    if (name === 'pool') { k = 'STATES'; v = fmt(R.pool * A.sweep); s = `${R.index_qubits} qubits · H⊗${R.index_qubits}`; }
    else if (name === 'oracle') { k = 'MARKED'; v = fmt(R.marked); s = 'phase × (−1)'; }
    else if (name === 'diffuse') { k = 'P(MARKED)'; v = pct(R.marked * A.aM * A.aM); s = `Grover iteration ${this.seq[this.ph][2] + 1}/${R.layers}`; }
    else if (name === 'measure') { k = 'SHOTS'; v = fmt(this.landed ?? 0); s = `P(marked) ${pct(this.pFinal)}`; }
    else if (name === 'route') {
      const p = clamp01(this.pt / this.seq[this.ph][1] / 0.8);
      k = 'EXACT LP'; v = fmt(this.distinct * p); s = `${this.distinct} distinct of 2,048 shots`;
    } else {
      const kind = R.moved;
      k = { record: 'NEW RECORD', downhill: 'DOWNHILL', uphill: 'UPHILL', stay: 'BEST CANDIDATE' }[kind];
      v = kind === 'record' ? fmt(R.checked_best) : (R.best_lp === null ? '> cutoff' : fmt(R.best_lp));
      s = kind === 'record' ? `−${fmt(this.B.record - R.checked_best)} vs previous record` : (kind === 'stay' ? 'rejected' : 'accepted');
    }
    if (this.el.k.textContent !== k) this.el.k.textContent = k;
    if (this.el.v.textContent !== v) this.el.v.textContent = v;
    if (this.el.s.textContent !== s) this.el.s.textContent = s;
  }

  drawLP() {
    const { ctx, w, h } = setupCanvas(this.el.lp);
    const R = this.R;
    const [name, dur] = this.seq[this.ph];
    ctx.clearRect(0, 0, w, h);
    const rec = this.B.record, cur = this.B.z;
    const hi = Math.max(rec, cur) + this.slack;
    const lo = Math.min(this.lpMin, rec) - 1800;
    const pad = 14;
    const X = v => pad + ((v - lo) / (hi - lo)) * (w - 2 * pad);
    const axisY = h * 0.6;
    ctx.font = '10px "JetBrains Mono", monospace';
    // axis + ticks
    ctx.strokeStyle = 'rgba(150,210,255,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad, axisY); ctx.lineTo(w - pad, axisY); ctx.stroke();
    ctx.fillStyle = 'rgba(150,180,210,0.55)';
    ctx.textAlign = 'center';
    for (let v = Math.ceil(lo / 5000) * 5000; v <= hi; v += 5000) {
      const x = X(v);
      ctx.fillRect(x, axisY - 2, 1, 4);
      ctx.fillText(`${Math.round(v / 1000)}k`, x, h - 4);
    }
    // record and current
    const line = (v, color, label, dash, up) => {
      const x = X(v);
      ctx.setLineDash(dash ? [3, 3] : []);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x, 8); ctx.lineTo(x, axisY + 8); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = color;
      const right = up && x > ctx.measureText(label).width + pad + 6;
      ctx.textAlign = right ? 'right' : 'left';
      ctx.fillText(label, x + (right ? -4 : 4), 12);
    };
    line(rec, 'rgba(94,242,255,0.9)', `record ${fmt(rec)}`, false, true);
    if (Math.abs(cur - rec) > 300) line(cur, 'rgba(255,255,255,0.55)', 'walk', true, false);
    ctx.textAlign = 'right';
    ctx.fillStyle = 'rgba(150,180,210,0.45)';
    ctx.fillText('cutoff →', w - pad, axisY - 6 - 30);

    const showRoute = name === 'route' || name === 'move';
    if (!showRoute) return;
    const p = name === 'route' ? clamp01(this.pt / dur) : 1;
    const ids = R.quantum_ids;
    ctx.globalCompositeOperation = 'lighter';
    ids.forEach((id, n) => {
      if (n / ids.length > p / 0.75) return;
      const v = R.lp[id];
      const y = axisY - 8 - hash(id) * (axisY - 22);
      if (v === null) {
        ctx.fillStyle = 'rgba(138,160,184,0.35)';
        ctx.fillRect(w - pad - 3 - hash(id + 9) * 8, y, 2, 2);
        return;
      }
      const x = X(v);
      const better = v < rec - 0.5;
      ctx.fillStyle = better ? 'rgba(94,242,255,1)' : (v < cur ? 'rgba(196,181,253,0.95)' : 'rgba(167,139,250,0.55)');
      ctx.beginPath(); ctx.arc(x, y, better ? 3.2 : 2.1, 0, Math.PI * 2); ctx.fill();
      if (better) { ctx.fillStyle = 'rgba(94,242,255,0.22)'; ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2); ctx.fill(); }
    });
    ctx.globalCompositeOperation = 'source-over';
    if (p > 0.8) {
      const a = clamp01((p - 0.8) / 0.2);
      const mark = (v, color, shape) => {
        if (v === null) return;
        const x = X(v), y = axisY + 10;
        ctx.globalAlpha = a;
        ctx.fillStyle = color;
        ctx.beginPath();
        if (shape === 'diamond') { ctx.moveTo(x, y - 5); ctx.lineTo(x + 5, y); ctx.lineTo(x, y + 5); ctx.lineTo(x - 5, y); }
        else if (shape === 'square') ctx.rect(x - 3.5, y - 3.5 + 8, 7, 7);
        else { ctx.arc(x, y - 4, 5, 0, Math.PI * 2); }
        ctx.fill();
        ctx.globalAlpha = 1;
      };
      mark(R.best.uniform, 'rgba(138,160,184,0.9)', 'square');
      mark(R.best.greedy, 'rgba(255,181,71,0.95)', 'diamond');
      if (R.best.quantum !== null) {
        const x = X(R.best.quantum);
        ctx.globalAlpha = a;
        ctx.strokeStyle = '#c4b5fd';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(x, axisY + 6, 6, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.textAlign = x > w * 0.6 ? 'right' : 'left';
        ctx.fillText(`Grover best ${fmt(R.best.quantum)}`, x + (x > w * 0.6 ? -10 : 10), axisY + 20);
        ctx.globalAlpha = 1;
      }
    }
  }

  drawTimeline() {
    const { ctx, w, h } = setupCanvas(this.el.timeline);
    ctx.clearRect(0, 0, w, h);
    const x0 = 56, x1 = w - 18, y0 = 16, y1 = h - 22;
    this.tlBox = { x0, x1 };
    const lo = 630000, hi = 650000;
    const X = r => x0 + (r / 52) * (x1 - x0);
    const Y = v => y1 - ((Math.min(hi, Math.max(lo, v)) - lo) / (hi - lo)) * (y1 - y0);
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    for (let v = lo; v <= hi; v += 5000) {
      const y = Y(v);
      ctx.strokeStyle = 'rgba(150,210,255,0.08)';
      ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
      ctx.fillStyle = 'rgba(150,180,210,0.55)';
      ctx.fillText(`${v / 1000}k`, x0 - 8, y + 3);
    }
    ctx.textAlign = 'center';
    for (let r = 0; r <= 52; r += 4) { ctx.fillStyle = 'rgba(150,180,210,0.4)'; ctx.fillText(String(r), X(r), h - 6); }
    ctx.textAlign = 'right';
    ctx.fillStyle = 'rgba(255,181,71,0.75)';
    ctx.fillText('QOBLIB best known 659,369 ↑ (off the chart)', x1, y0 - 4);

    const rv = this.revealed;
    const rounds = this.rounds;
    // area + record step line
    const pts = [[0, this.story.hand_in.score]];
    for (let i = 0; i < rv; i++) pts.push([i + 1, rounds[i].checked_best]);
    const grad = ctx.createLinearGradient(0, y0, 0, y1);
    grad.addColorStop(0, 'rgba(94,242,255,0.28)');
    grad.addColorStop(1, 'rgba(94,242,255,0)');
    ctx.beginPath();
    ctx.moveTo(X(0), y1);
    pts.forEach(([r, v], i) => { if (i) ctx.lineTo(X(r), Y(pts[i - 1][1])); ctx.lineTo(X(r), Y(v)); });
    ctx.lineTo(X(pts[pts.length - 1][0]), y1);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
    // walk position
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(X(0), Y(this.story.hand_in.z_lp));
    for (let i = 0; i < rv; i++) ctx.lineTo(X(i + 1), Y(rounds[i].current_lp));
    ctx.stroke();
    // per-round best of each selector
    for (let i = 0; i < rv; i++) {
      const b = rounds[i].best, x = X(i + 1);
      if (b.uniform !== null && b.uniform < hi) { ctx.fillStyle = 'rgba(138,160,184,0.5)'; ctx.fillRect(x - 2, Y(b.uniform) - 2, 4, 4); }
      if (b.greedy !== null && b.greedy < hi) {
        ctx.fillStyle = 'rgba(255,181,71,0.75)';
        const y = Y(b.greedy);
        ctx.beginPath(); ctx.moveTo(x, y - 3); ctx.lineTo(x + 3, y); ctx.lineTo(x, y + 3); ctx.lineTo(x - 3, y); ctx.fill();
      }
      if (b.quantum !== null && b.quantum < hi) {
        ctx.fillStyle = 'rgba(196,181,253,0.95)';
        ctx.beginPath(); ctx.arc(x, Y(b.quantum), 2.4, 0, Math.PI * 2); ctx.fill();
      }
    }
    // record line (glow)
    ctx.lineJoin = 'round';
    for (const [lw, col] of [[6, 'rgba(94,242,255,0.18)'], [2.2, 'rgba(160,248,255,1)']]) {
      ctx.strokeStyle = col;
      ctx.lineWidth = lw;
      ctx.beginPath();
      pts.forEach(([r, v], i) => { if (!i) ctx.moveTo(X(r), Y(v)); else { ctx.lineTo(X(r), Y(pts[i - 1][1])); ctx.lineTo(X(r), Y(v)); } });
      ctx.stroke();
    }
    // record stars
    ctx.textAlign = 'center';
    let nrec = 0;
    for (let i = 0; i < rv; i++) {
      if (rounds[i].moved !== 'record') continue;
      const below = nrec++ % 2 === 0;
      const x = X(i + 1), y = Y(rounds[i].checked_best);
      ctx.fillStyle = 'rgba(94,242,255,0.25)';
      ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(220,250,255,0.95)';
      ctx.fillText(fmt(rounds[i].checked_best), x, below ? y + 20 : y - 13);
    }
    // cursor
    const cx = X(this.r + clamp01(this.phaseProgress()));
    ctx.strokeStyle = 'rgba(167,139,250,0.7)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(cx, y0); ctx.lineTo(cx, y1); ctx.stroke();
    ctx.fillStyle = 'rgba(167,139,250,0.9)';
    ctx.beginPath(); ctx.arc(cx, y0, 3, 0, Math.PI * 2); ctx.fill();
  }

  phaseProgress() {
    let total = 0, done = 0;
    this.seq.forEach(([, d], i) => { total += d; if (i < this.ph) done += d; });
    return (done + Math.min(this.pt, this.seq[this.ph][1])) / total;
  }
}
