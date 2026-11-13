(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- nav ---------- */
  const nav = $('.nav'), menuBtn = $('#menuBtn'), links = $('#navlinks');
  const onScroll = () => nav.classList.toggle('scrolled', scrollY > 30);
  addEventListener('scroll', onScroll, { passive: true }); onScroll();
  const setMenu = open => { links.classList.toggle('open', open); menuBtn.setAttribute('aria-expanded', open); document.body.style.overflow = open ? 'hidden' : ''; };
  menuBtn.addEventListener('click', () => setMenu(!links.classList.contains('open')));
  $$('a', links).forEach(a => a.addEventListener('click', () => setMenu(false)));

  /* ---------- hero: books rotate like product reveals ---------- */
  const HERO = [
    { img: 'becoming', ar: 600 / 900, kicker: 'Self-help · Cover & interior', title: 'The Art of Becoming Unshakeable' },
    { img: 'lost-letter', ar: 590 / 900, kicker: "Children's mystery · Cover & interior", title: 'The Lost Letter Project' },
    { img: 'silk', ar: 600 / 900, kicker: 'Lifestyle guide · Cover & interior', title: 'Silk & Sunshine' },
    { img: 'truth-ai', ar: 600 / 900, kicker: 'Nonfiction · Cover & interior', title: 'Truth in the Era of AI' },
    { img: 'clinical', ar: 637 / 900, kicker: 'Medical · English edition', title: 'Clinical Nutrition in Dentistry' },
    { img: 'beauty', ar: 696 / 900, kicker: 'Workbook · Cover & interior', title: 'Beauty Blueprint Workbook' },
  ];
  const DUR = 4200;
  const booksEl = $('#books'), dotsEl = $('#dots'), heroBg = $('#heroBg');
  const cap = $('.stage-caption'), capK = $('#capKicker'), capT = $('#capTitle');
  const bookEls = HERO.map((b, i) => {
    const el = document.createElement('div');
    el.className = 'book is-hidden';
    el.style.setProperty('--ar', b.ar);
    el.innerHTML = `<div class="front"><img src="assets/covers/${b.img}.webp" alt="${b.title} book cover" ${i > 1 ? 'loading="lazy"' : ''}></div><div class="pages"></div>`;
    booksEl.appendChild(el);
    const d = document.createElement('button');
    d.setAttribute('role', 'tab'); d.setAttribute('aria-label', b.title); d.innerHTML = '<i></i>';
    d.style.setProperty('--dur', DUR + 'ms');
    d.addEventListener('click', () => { go(i); restart(); });
    dotsEl.appendChild(d);
    return el;
  });
  let cur = -1, timer;
  function go(i) {
    const n = HERO.length;
    cur = (i + n) % n;
    bookEls.forEach((el, k) => {
      el.className = 'book ' + (k === cur ? 'is-active' : k === (cur + 1) % n ? 'is-next' : k === (cur - 1 + n) % n ? 'is-prev' : 'is-hidden');
    });
    $$('button', dotsEl).forEach((d, k) => { d.classList.remove('on'); void d.offsetWidth; d.classList.toggle('on', k === cur); d.setAttribute('aria-selected', k === cur); });
    cap.classList.add('swap');
    setTimeout(() => { capK.textContent = HERO[cur].kicker; capT.textContent = HERO[cur].title; cap.classList.remove('swap'); }, 380);
    heroBg.style.backgroundImage = `url(assets/covers/${HERO[cur].img}.webp)`;
  }
  // With reduced motion the books still change, but as a gentle cross-fade (see CSS)
  const restart = () => { clearInterval(timer); timer = setInterval(() => go(cur + 1), reduce ? DUR * 1.5 : DUR); };
  go(0); restart();
  const stage = $('#stage');
  stage.addEventListener('mouseenter', () => clearInterval(timer));
  stage.addEventListener('mouseleave', restart);
  // swipe on touch
  let sx = null;
  stage.addEventListener('touchstart', e => { sx = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend', e => { if (sx === null) return; const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 40) { go(cur + (dx < 0 ? 1 : -1)); restart(); } sx = null; });
  document.addEventListener('visibilitychange', () => document.hidden ? clearInterval(timer) : restart());

  /* ---------- before / after ---------- */
  const cmp = $('#compare'), rng = $('#compareRange');
  rng.addEventListener('input', () => cmp.style.setProperty('--pos', rng.value + '%'));
  const ai = $('img', cmp);
  const setAr = () => ai.naturalWidth && cmp.style.setProperty('--car', ai.naturalWidth / ai.naturalHeight);
  ai.complete ? setAr() : ai.addEventListener('load', setAr);

  /* ---------- work grid + viewer ---------- */
  /* cards are in the HTML (good for search engines); read their data from it */
  const grid = $('#grid');
  const WORK = $$('.card', grid).map(c => ({
    id: c.dataset.id, n: +c.dataset.n, pdf: c.dataset.pdf,
    t: $('h3', c).textContent, k: $('.k', c).textContent, d: $('.meta p', c).textContent,
  }));
  $$('.card', grid).forEach((c, i) => $('.thumb', c).addEventListener('click', e => openViewer(i, e.currentTarget)));
  $$('#filters button').forEach(btn => btn.addEventListener('click', () => {
    $$('#filters button').forEach(x => x.classList.toggle('on', x === btn));
    const f = btn.dataset.f;
    $$('.card', grid).forEach(c => c.classList.toggle('hide', f !== 'all' && !c.dataset.f.split(' ').includes(f)));
  }));

  const viewer = $('#viewer'), vImg = $('#vImg');
  let vw = null, vs = 0, lastFocus = null;
  function show() {
    // all slides of a case live in one tall image; show one slice of it
    const src = `assets/work/${vw.id}-slides.webp`;
    if (vImg.dataset.src !== src) {
      vImg.classList.add('load'); vImg.dataset.src = src;
      const pre = new Image(); pre.onload = () => { vImg.style.backgroundImage = `url(${src})`; vImg.classList.remove('load'); }; pre.src = src;
    }
    vImg.style.backgroundPosition = `0 ${vw.n > 1 ? (vs / (vw.n - 1)) * 100 : 0}%`;
    vImg.setAttribute('aria-label', `${vw.t}, slide ${vs + 1} of ${vw.n}`);
    $('#vCount').textContent = `${String(vs + 1).padStart(2, '0')} / ${String(vw.n).padStart(2, '0')}`;
  }
  function openViewer(i, from) {
    vw = WORK[i]; vs = 0; lastFocus = from;
    $('#vTitle').textContent = vw.t; $('#vKicker').textContent = `${vw.k} · ${vw.d}`;
    $('#vPdf').href = 'case-studies/' + vw.pdf;
    viewer.hidden = false; document.body.style.overflow = 'hidden'; show(); $('#vClose').focus();
  }
  function closeViewer() { viewer.hidden = true; document.body.style.overflow = ''; lastFocus && lastFocus.focus(); }
  const step = d => { vs = (vs + d + vw.n) % vw.n; show(); };
  $('#vClose').addEventListener('click', closeViewer);
  $('#vPrev').addEventListener('click', () => step(-1));
  $('#vNext').addEventListener('click', () => step(1));
  viewer.addEventListener('click', e => { if (e.target === viewer || e.target.classList.contains('v-stage')) closeViewer(); });
  addEventListener('keydown', e => {
    if (viewer.hidden) return;
    if (e.key === 'Escape') closeViewer();
    if (e.key === 'ArrowRight') step(1);
    if (e.key === 'ArrowLeft') step(-1);
    if (e.key === 'Tab') { const f = $$('a,button', viewer); const a = f[0], z = f[f.length - 1]; if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } }
  });
  let vx = null;
  viewer.addEventListener('touchstart', e => { vx = e.touches[0].clientX; }, { passive: true });
  viewer.addEventListener('touchend', e => { if (vx === null) return; const dx = e.changedTouches[0].clientX - vx; if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1); vx = null; });

  /* ---------- reveal on scroll + counters ---------- */
  const countUp = el => {
    const to = +el.dataset.count, dec = +(el.dataset.dec || 0), suf = el.dataset.suffix || '';
    if (reduce) { el.textContent = to.toFixed(dec) + suf; return; }
    const t0 = performance.now(), d = 1600;
    const tick = t => { const p = Math.min((t - t0) / d, 1), e = 1 - Math.pow(1 - p, 3); el.textContent = (to * e).toFixed(dec) + suf; if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target;
    const sibs = el.parentElement ? $$(':scope > .reveal', el.parentElement) : [];
    el.style.transitionDelay = Math.min(sibs.indexOf(el), 6) * 80 + 'ms';
    el.classList.add('in');
    $$('[data-count]', el).forEach(countUp);
    io.unobserve(el);
  }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  $$('.reveal').forEach(el => io.observe(el));

  /* ---------- quote form → WhatsApp or email ---------- */
  const form = $('#quoteForm'), err = $('#formErr');
  let via = 'wa';
  $$('button[type=submit]', form).forEach(b => b.addEventListener('click', () => { via = b.dataset.via; }));
  form.name.addEventListener('input', () => { err.textContent = ''; });
  form.addEventListener('submit', e => {
    e.preventDefault();
    const fd = new FormData(form);
    const name = (fd.get('name') || '').trim();
    if (!name) { err.textContent = 'Please add your name first.'; form.name.focus(); return; }
    const fmts = fd.getAll('fmt').join(', ') || 'Not sure';
    const lines = [
      `Hi Khadijat, I'd like a quote.`, ``,
      `Name: ${name}`,
      fd.get('title') ? `Book: ${fd.get('title')}` : '',
      `Service: ${fd.get('service')}`,
      fd.get('words') ? `Word count: ${fd.get('words')}` : '',
      `Formats: ${fmts}`,
      fd.get('msg') ? `\n${fd.get('msg')}` : '',
    ].filter(Boolean).join('\n');
    const url = via === 'wa'
      ? 'https://wa.me/2349021651449?text=' + encodeURIComponent(lines)
      : 'mailto:khadijahismail525@gmail.com?subject=' + encodeURIComponent('Book project quote: ' + (fd.get('title') || name)) + '&body=' + encodeURIComponent(lines);
    window.open(url, '_blank', 'noopener');
  });

  $('#yr').textContent = new Date().getFullYear();
})();
