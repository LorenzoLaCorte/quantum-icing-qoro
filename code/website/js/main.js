import { NetworkScene } from './scene.js';
import { GroverConsole } from './grover.js';

const gsap = window.gsap;
const ScrollTrigger = window.ScrollTrigger;
gsap.registerPlugin(ScrollTrigger);

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const fmt = n => Math.round(n).toLocaleString('en-US');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ------------------------------------------------------------------ loader */
const logEl = $('#loaderLog');
const bar = $('#loaderBar');
const lines = [
  ['> fetch QOBLIB 08 · network23', 'ok'],
  ['> 23 nodes · 506 demands · 506 binary variables', ''],
  ['> replay quantum_congestion.py · seed 73 · 52 rounds', ''],
  ['> allocate index register · 11 qubits', ''],
  ['> |ψ⟩ = H⊗¹¹ |0⟩', 'ok'],
];
let logged = 0;
const typeLine = () => new Promise(res => {
  if (logged >= lines.length) return res();
  const [text, cls] = lines[logged++];
  const span = document.createElement('span');
  if (cls) span.className = cls;
  logEl.appendChild(span);
  let i = 0;
  const step = () => {
    span.textContent = text.slice(0, ++i);
    if (i < text.length) setTimeout(step, reduced ? 0 : 9);
    else { logEl.appendChild(document.createTextNode('\n')); setTimeout(res, reduced ? 0 : 90); }
  };
  step();
});
const progress = v => { bar.style.width = `${Math.round(v * 100)}%`; };

async function boot() {
  progress(0.08);
  const typing = (async () => { for (let i = 0; i < lines.length; i++) { await typeLine(); progress(0.12 + 0.13 * (i + 1)); } })();
  const res = await fetch('data/network23_story.json');
  const story = await res.json();
  progress(0.8);
  await typing;
  const app = new App(story);
  progress(1);
  await new Promise(r => setTimeout(r, reduced ? 0 : 350));
  $('#loader').classList.add('done');
  document.body.classList.remove('is-loading');
  app.intro();
}

/* ------------------------------------------------------------------ helpers */
function scramble(el, duration = 1.1) {
  const text = el.dataset.text || el.textContent;
  el.dataset.text = text;
  if (reduced) { el.textContent = text; return; }
  const glyphs = '01|ψ⟩⊗∑≈◇◆▲▼░▒▓/<>';
  const start = performance.now();
  const tick = now => {
    const p = Math.min(1, (now - start) / (duration * 1000));
    let out = '';
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch === ' ' || i / text.length < p * 1.15 - 0.15) out += ch;
      else out += glyphs[(Math.random() * glyphs.length) | 0];
    }
    el.textContent = out;
    if (p < 1) requestAnimationFrame(tick); else el.textContent = text;
  };
  requestAnimationFrame(tick);
}

function countTo(el, to, { duration = 1.6, dec = 0, prefix = '', suffix = '', from } = {}) {
  const obj = { v: from ?? (Number(el.dataset.cur) || 0) };
  gsap.killTweensOf(el._tw || {});
  el._tw = obj;
  gsap.to(obj, {
    v: to, duration: reduced ? 0 : duration, ease: 'power3.out',
    onUpdate: () => { el.textContent = prefix + (dec ? obj.v.toFixed(dec) : fmt(obj.v)) + suffix; },
    onComplete: () => { el.dataset.cur = String(to); },
  });
}

/* ------------------------------------------------------------------ app */
class App {
  constructor(story) {
    this.story = story;
    this.scene = new NetworkScene($('#gl'), story, { labelsEl: $('#labels') });
    this.hud = { el: $('#hud'), value: $('#hudValue'), gap: $('#hudGap'), stage: $('#hudStage'), meter: $('#hudMeter'), cur: 632319 };
    this.console = new GroverConsole(story, this.scene, {
      hud: v => this.consoleRecord(v),
      record: v => this.record(v),
    });
    this.final = story.records[story.records.length - 1];
    this.step = null;
    this.buildResults();
    this.bindFinal();
    this.scene.onFlick = n => { const el = $('#flickerCount'); if (el) el.textContent = fmt(n); };
    // first frame: hero network
    this.go('hero', true);
    let last = performance.now();
    // adaptive quality: watch the first seconds after the loader, degrade once if slow
    const perf = { t: 0, n: 0, level: 0 };
    const loop = now => {
      const raw = Math.max(0, (now - last) / 1000);
      const dt = Math.min(0.05, raw);
      last = now;
      if (!document.body.classList.contains('is-loading') && perf.level < 2 && !document.hidden) {
        perf.t += raw; perf.n++;
        if (perf.t > 2.5) {
          const fps = perf.n / perf.t;
          if (fps < 22) { perf.level = fps < 14 ? 2 : perf.level + 1; this.scene.degrade(perf.level); }
          else perf.level = 2;
          perf.t = 0; perf.n = 0;
        }
      }
      this.scene.update(dt);
      this.console.tick(dt);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  intro() {
    const n = $('#heroNumber');
    countTo(n, 632319, { from: 659369, duration: 2.6 });
    this.setupScroll();
    $$('.scramble').forEach(el => {
      ScrollTrigger.create({ trigger: el, start: 'top 85%', once: true, onEnter: () => scramble(el) });
    });
  }

  setHud(value, stage, bkv = this.story.bkv) {
    const h = this.hud;
    h.el.classList.add('on');
    h.stage.textContent = stage;
    if (value === null) {
      h.value.textContent = '—';
      h.gap.textContent = 'no links yet';
      h.gap.classList.add('neutral');
      h.meter.style.width = '0%';
      h.cur = null;
      return;
    }
    countTo(h.value, value, { from: h.cur ?? value, duration: 1.2 });
    h.cur = value;
    const gap = (value / bkv - 1) * 100;
    h.gap.classList.remove('neutral');
    h.gap.textContent = `${gap < 0 ? '−' : '+'}${Math.abs(gap).toFixed(2)}% vs QOBLIB best known`;
    h.meter.style.width = `${Math.max(4, Math.min(100, ((value - 620000) / (665000 - 620000)) * 100))}%`;
  }

  hideHud() { this.hud.el.classList.remove('on'); }

  consoleRecord(v) {
    const el = $('#roundRec');
    countTo(el, v, { from: this.recCur ?? v, duration: 1.1 });
    this.recCur = v;
    const gap = (v / this.story.bkv - 1) * 100;
    $('#roundGap').textContent = `${gap < 0 ? '−' : '+'}${Math.abs(gap).toFixed(2)}%`;
  }

  record() {
    const f = $('#flash');
    gsap.fromTo(f, { opacity: 0.55 }, { opacity: 0, duration: 1.2, ease: 'power2.out' });
    const rr = $('.round-rec');
    rr.classList.remove('flash');
    void rr.offsetWidth;
    rr.classList.add('flash');
  }

  /* ---------------------------------------------------------------- director */
  go(step, instant = false) {
    if (step === this.step) return;
    const prev = this.step;
    this.step = step;
    const S = this.scene, st = this.story;
    clearTimeout(this.seqT1); clearTimeout(this.seqT2);
    if (prev === 'console' && step !== 'console') this.console.leave();
    if (step !== 'final') { S.setInteractive(false); S.setFocus(null); S.locked = null; $('#nodeCard').hidden = true; }
    if (step !== 'space') S.setFlicker(false);
    if (step !== 'stuck') S.setProbe(false);
    if (step !== 'demand' && step !== 'rules') S.setWeb(0, 0.8);
    S.setMode('heat');
    const d = instant ? 0.01 : undefined;

    const n24 = st.network24, der = st.derived, hand = st.hand_in, fin = this.final;
    const busy = z => `busiest link · ${fmt(z)}`;
    switch (step) {
      case 'hero':
        S.setView('hero', instant ? 0.01 : 1.6);
        S.setNodeCount(23, !instant);
        S.setNodesVisible(true, 0);
        S.setTopology(fin.arcs, fin.loads, { duration: instant ? 1.6 : 1.1, perSource: fin.per_source, stagger: instant ? 0.02 : 0.006 });
        S.setNeutral(false, d); S.setFlow(1, d); S.setLabels(false); S.setBusy(true, busy(632319));
        this.hideHud();
        break;
      case 'nodes':
        S.setView('story');
        S.setNodeCount(23);
        S.setTopology([], null, { duration: 0.8 });
        if (prev === 'hero' || prev === null) { S.setNodesVisible(false); setTimeout(() => this.step === 'nodes' && S.setNodesVisible(true), 450); }
        else S.setNodesVisible(true, 0.01);
        S.setLabels(true); S.setBusy(false);
        this.setHud(null, '23 nodes · no links');
        break;
      case 'demand':
        S.setView('story');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setTopology([], null, { duration: 0.8 });
        S.setWeb(1); S.setLabels(true); S.setBusy(false);
        this.setHud(null, '506 demands, nothing routed');
        break;
      case 'rules':
        S.setView('story');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setWeb(0.12);
        S.setNeutral(true); S.setFlow(0);
        S.setTopology(hand.arcs, null, { duration: 1.2, stagger: 0.035 });
        S.setLabels(true); S.setBusy(false);
        this.setHud(null, '46 links · not routed yet');
        break;
      case 'route':
      case 'space':
        S.setView('story');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1);
        S.setTopology(hand.arcs, hand.loads, { duration: 1.2 });
        S.setLabels(step === 'route'); S.setBusy(true, busy(hand.score));
        this.setHud(hand.score, 'network23 · routed');
        if (step === 'space') S.setFlicker(!reduced);
        break;
      case 'net24':
        S.setView('story');
        S.setNodesVisible(true, 0.01);
        S.setNodeCount(24);
        S.setNeutral(false); S.setFlow(1);
        S.setTopology(n24.arcs, n24.loads, { duration: 1.2, fresh: 'down' });
        S.setLabels(true); S.setBusy(true, busy(n24.score));
        this.setHud(n24.score, 'network24 hand-in · 24 nodes', st.bkv24);
        break;
      case 'delete':
        S.setView('story');
        S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1);
        if (prev === 'net24') {
          // first the four links of node 24 vanish with the node, then the splice appears
          const node = st.deletion.node;
          const keep = n24.arcs.map((a, i) => [a, n24.loads[i]]).filter(([a]) => a[0] !== node && a[1] !== node);
          S.setTopology(keep.map(x => x[0]), keep.map(x => x[1]), { duration: 0.9 });
          S.setNodeCount(23);
          this.seqT1 = setTimeout(() => {
            if (this.step !== 'delete') return;
            S.setTopology(der.arcs, der.loads, { duration: 1.3, fresh: 'ice' });
            S.setBusy(true, busy(der.score));
            this.setHud(der.score, 'node 24 deleted · links spliced');
          }, 1250);
          S.setBusy(false);
          this.setHud(n24.score, 'deleting node 24…', st.bkv24);
        } else {
          S.setNodeCount(23);
          S.setTopology(der.arcs, der.loads, { duration: 1.1 });
          S.setBusy(true, busy(der.score));
          this.setHud(der.score, 'node 24 deleted · links spliced');
        }
        S.setLabels(true);
        break;
      case 'descent': {
        S.setView('story');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1);
        S.setTopology(der.arcs, der.loads, { duration: 0.8 });
        S.setBusy(true, busy(der.score));
        this.setHud(der.score, '2-exchange descent');
        const [s1, s2] = st.descent;
        this.seqT1 = setTimeout(() => {
          if (this.step !== 'descent') return;
          S.setTopology(s1.arcs, s1.loads, { duration: 1.1, fresh: 'ice' });
          S.setBusy(true, busy(s1.score));
          this.setHud(s1.score, '2-exchange 1 of 2');
        }, 900);
        this.seqT2 = setTimeout(() => {
          if (this.step !== 'descent') return;
          S.setTopology(s2.arcs, s2.loads, { duration: 1.1, fresh: 'ice' });
          S.setBusy(true, busy(s2.score));
          this.setHud(s2.score, '2-exchange 2 of 2 · hand-in');
        }, 2700);
        S.setLabels(true);
        break;
      }
      case 'stuck':
        S.setView('story');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1);
        S.setTopology(hand.arcs, hand.loads, { duration: 1.0 });
        S.setLabels(false); S.setBusy(true, busy(hand.score));
        S.setProbe(!reduced);
        this.setHud(hand.score, 'certified radius-3 local optimum');
        break;
      case 'console':
        S.setView('console');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1); S.setLabels(false);
        this.hideHud();
        this.console.enter();
        break;
      case 'final':
        S.setView('final');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setNeutral(false); S.setFlow(1);
        S.setTopology(fin.arcs, fin.loads, { duration: 1.2, perSource: fin.per_source });
        S.setMode('source');
        S.setLabels(true); S.setBusy(true, busy(632319));
        S.setInteractive(true);
        this.setHud(632319, 'network23 · final · checked');
        countTo($('#finalNumber'), 632319, { from: 639739, duration: 2 });
        $$('#ladder .rung').forEach((r, i) => {
          const v = Number(r.dataset.v);
          setTimeout(() => r.style.setProperty('--w', String(Math.max(0.04, (v - 450000) / (663688 - 450000)))), 120 * i);
        });
        break;
      case 'honest':
      case 'results':
        S.setView('results');
        S.setNodeCount(23); S.setNodesVisible(true, 0.01);
        S.setTopology(fin.arcs, fin.loads, { duration: 1.2, perSource: fin.per_source });
        S.setMode('source');
        S.setNeutral(false); S.setFlow(1); S.setLabels(false); S.setBusy(false);
        this.hideHud();
        break;
    }
  }

  setupScroll() {
    $$('[data-step]').forEach(el => {
      const step = el.dataset.step;
      const isStep = el.classList.contains('step');
      const cfg = {
        hero: { start: 'top top', end: 'bottom 45%' },
        console: { start: 'top 55%', end: 'bottom 45%' },
        final: { start: 'top 60%', end: 'bottom 50%' },
        honest: { start: 'top 60%', end: 'bottom 50%' },
        results: { start: 'top 60%', end: 'bottom top' },
      }[step] || { start: 'top 65%', end: 'bottom 35%' };
      ScrollTrigger.create({
        trigger: el, ...cfg,
        onToggle: self => {
          if (isStep) el.classList.toggle('active', self.isActive);
          if (self.isActive) this.go(step);
        },
      });
    });
    // console canvases only draw while on screen
    ScrollTrigger.create({ trigger: '#console', start: 'top bottom', end: 'bottom top', onToggle: s => this.console.setVisible(s.isActive) });
    // progress bar + nav highlight
    gsap.to('#progress span', { scaleX: 1, ease: 'none', scrollTrigger: { trigger: document.documentElement, start: 'top top', end: 'bottom bottom', scrub: 0.3 } });
    const nav = $$('.topnav a');
    nav.forEach(a => {
      const target = $(a.getAttribute('href'));
      ScrollTrigger.create({ trigger: target, start: 'top 50%', end: 'bottom 50%', onToggle: s => a.classList.toggle('on', s.isActive) });
    });
    // results reveal
    ScrollTrigger.create({
      trigger: '#resNetwork', start: 'top 80%', once: true,
      onEnter: () => $$('#resNetwork .bar i').forEach((b, i) => setTimeout(() => { b.style.transform = `scaleX(${b.dataset.w})`; }, 90 * i)),
    });
    $$('.count').forEach(el => ScrollTrigger.create({
      trigger: el, start: 'top 88%', once: true,
      onEnter: () => countTo(el, Number(el.dataset.to), { dec: Number(el.dataset.dec || 0), prefix: el.dataset.prefix || '', suffix: el.dataset.suffix || '', from: 0, duration: 1.8 }),
    }));
    gsap.utils.toArray('.h-card, .pf-card').forEach(el => gsap.from(el, { y: 40, opacity: 0, duration: 0.9, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 90%' } }));
    ScrollTrigger.refresh();
  }

  /* ---------------------------------------------------------------- final */
  bindFinal() {
    const card = $('#nodeCard');
    const D = this.story.demand, k1000 = this.story.intscale;
    this.scene.onHover = k => {
      this.scene.setFocus(k);
      if (k === null) { card.hidden = true; return; }
      const out = D[k].reduce((a, b) => a + b, 0) * k1000;
      const inn = D.reduce((a, r) => a + r[k], 0) * k1000;
      $('#ncId').textContent = String(k + 1);
      $('#ncOut').textContent = fmt(out);
      $('#ncIn').textContent = fmt(inn);
      $('#ncLinks').textContent = `${this.scene.sourceLinks(k).length} / 46`;
      card.hidden = false;
    };
  }

  /* ---------------------------------------------------------------- results */
  buildResults() {
    const rows = [
      ['network05', 65500, 65500, 'proven optimal · all 216 networks scored', true],
      ['network18', 469000, 473375, 'certified-radius ILS from the hybrid chain'],
      ['network19', 486579, 492924, 'Grover walk'],
      ['network20', 516397, 528528, 'Grover walk'],
      ['network21', 562362, 569273, 'hybrid chain · Divi QAOA + exact LP'],
      ['network22', 604229, 618135, 'Grover walk'],
      ['network23', 632319, 659369, 'Grover walk · this page', false, true],
      ['network24', 657121, 663688, 'parallel tempering → ILS → PT'],
    ];
    const max = 4.2;
    const html = ['<div class="res-row head"><span>INSTANCE</span><span>GAP VS BEST KNOWN</span><span class="num">OURS</span><span class="num qob">QOBLIB</span><span class="num">GAP</span><span class="meth">METHOD</span></div>'];
    for (const [name, ours, qob, meth, opt, star] of rows) {
      const gap = (ours / qob - 1) * 100;
      const w = opt ? 1 : Math.abs(gap) / max;
      html.push(`<div class="res-row${star ? ' star' : ''}">
        <span class="inst">${name}</span>
        <span class="bar${opt ? ' opt' : ''}"><i data-w="${w.toFixed(3)}"></i></span>
        <span class="num ours">${fmt(ours)}</span>
        <span class="num qob">${fmt(qob)}</span>
        <span class="gap${opt ? ' zero' : ''}">${opt ? 'optimal' : `${gap < 0 ? '−' : '+'}${Math.abs(gap).toFixed(2)}%`}</span>
        <span class="meth">${meth}</span>
      </div>`);
    }
    $('#resNetwork').innerHTML = html.join('');
  }
}

boot().catch(err => {
  console.error(err);
  $('#loaderLog').textContent += `\n> error: ${err.message}\n> serve this folder over HTTP (python3 -m http.server)`;
});
