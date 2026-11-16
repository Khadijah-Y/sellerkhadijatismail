/* Website admin dashboard: real numbers from the site's content files and its GitHub change history. */
(() => {
  'use strict';
  const REPO = 'Khadijah-Y/sellerkhadijatismail', BRANCH = 'main', USER_KEY = 'decap-cms-user';
  const LOCAL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const NS = 'http://www.w3.org/2000/svg';
  const C = { accent: '#F15A22', yellow: '#F5B82E', green: '#22A55B', brown: '#8B5E3C', grey: '#CFC8C1' };

  const ROUTES = {
    portfolio: ['Portfolio', 'collections/portfolio/entries/portfolio'],
    reviews: ['Reviews', 'collections/reviews/entries/reviews'],
    home: ['Home page', 'collections/home/entries/home'],
    services: ['Services', 'collections/services/entries/services'],
    service_pages: ['Service pages', 'collections/service_pages/entries/service_pages'],
    faq: ['FAQ', 'collections/faq/entries/faq'],
    media: ['Media', 'media'],
    settings: ['Settings', 'collections/settings/entries/settings'],
  };
  const CATS = [['nonfiction', 'Self-help & nonfiction', C.accent], ['workbook', 'Workbooks', C.yellow], ['guide', 'Cookbooks & guides', C.green], ['fiction', "Fiction & children's", C.brown]];

  /* ---------------- sign in (shares the login with the editor) ---------------- */
  const user = () => { try { const u = JSON.parse(localStorage.getItem(USER_KEY) || 'null'); return u && u.token && u.backendName === 'github' ? u : null; } catch (e) { return null; } };
  function login() {
    const err = $('#loginErr'); err.textContent = '';
    const w = 600, h = 700;
    const popup = window.open(`/api/auth?provider=github&scope=repo&site_id=${location.host}`, 'decap-login',
      `width=${w},height=${h},top=${(screen.height - h) / 2},left=${(screen.width - w) / 2}`);
    const onMsg = async e => {
      if (e.origin !== location.origin || typeof e.data !== 'string') return;
      if (e.data === 'authorizing:github') { popup && popup.postMessage(e.data, e.origin); return; }
      const m = e.data.match(/^authorization:github:(success|error):(.*)$/s);
      if (!m) return;
      removeEventListener('message', onMsg);
      const data = JSON.parse(m[2]);
      if (m[1] !== 'success') { err.textContent = data.message || 'Login failed.'; return; }
      try {
        const u = await fetch('https://api.github.com/user', { headers: { Authorization: 'token ' + data.token } }).then(r => r.json());
        localStorage.setItem(USER_KEY, JSON.stringify({ token: data.token, backendName: 'github', login: u.login, name: u.name, avatar_url: u.avatar_url }));
      } catch (x) {
        localStorage.setItem(USER_KEY, JSON.stringify({ token: data.token, backendName: 'github' }));
      }
      start();
    };
    addEventListener('message', onMsg);
  }
  $('#loginBtn').addEventListener('click', login);
  $('#pwToggle').addEventListener('click', () => {
    const p = $('#lp'), show = p.type === 'password';
    p.type = show ? 'text' : 'password'; $('#pwToggle').textContent = show ? 'Hide' : 'Show';
  });
  $('#loginForm').addEventListener('submit', async e => {
    e.preventDefault();
    const err = $('#loginErr'), btn = $('#loginSubmit'), username = $('#lu').value.trim(), password = $('#lp').value;
    if (!username || !password) { err.textContent = 'Please enter your username and password.'; return; }
    err.textContent = ''; btn.disabled = true; btn.textContent = 'Logging in…';
    try {
      const r = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
      const data = await r.json().catch(() => ({}));
      if (!r.ok || !data.token) throw new Error(data.error || 'Login failed. Please try again.');
      localStorage.setItem(USER_KEY, JSON.stringify({ token: data.token, backendName: 'github', name: username }));
      $('#lp').value = '';
      start();
    } catch (x) {
      err.textContent = x.message === 'Failed to fetch' ? 'No connection. Please try again.' : x.message;
    } finally { btn.disabled = false; btn.textContent = 'Log in'; }
  });
  $('#logout').addEventListener('click', () => { try { localStorage.removeItem(USER_KEY); } catch (e) {} location.hash = ''; location.reload(); });

  /* ---------------- data ---------------- */
  const gh = (path, raw) => {
    const u = user(), headers = { Accept: raw ? 'application/vnd.github.raw+json' : 'application/vnd.github+json' };
    if (u && u.token) headers.Authorization = 'token ' + u.token;
    return fetch('https://api.github.com/repos/' + REPO + path, { headers, cache: 'no-store' }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
  };
  const content = name => (user() && user().token)
    ? gh(`/contents/content/${name}.json?ref=${BRANCH}&t=${Date.now()}`, true)
    : fetch(`dev-content/${name}.json?t=${Date.now()}`).then(r => r.json());

  let D = null, RANGE = 'week';
  async function loadData() {
    const [settings, portfolio, reviews, pages, faq] = await Promise.all(['settings', 'portfolio', 'reviews', 'service_pages', 'faq'].map(content));
    let commits = [], commitsOk = true;
    try {
      const since = new Date(Date.now() - 31 * 864e5).toISOString();
      commits = (await gh(`/commits?sha=${BRANCH}&since=${since}&per_page=100`)).map(c => ({
        date: new Date(c.commit.author.date), msg: c.commit.message.split('\n')[0], admin: /\(admin\)/.test(c.commit.message),
      }));
    } catch (e) { commitsOk = false; }
    D = { settings, items: portfolio.items || [], reviews: reviews.reviews || [], popups: reviews.popups || [], pages: pages.pages || [], faq: faq.questions || [], commits, commitsOk };
  }

  /* ---------------- helpers ---------------- */
  const startOfDay = d => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; };
  const DAY = 864e5;
  const fmtDate = d => d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  const ago = d => {
    const s = (Date.now() - d) / 1000;
    if (s < 60) return 'just now'; if (s < 3600) return Math.round(s / 60) + ' min ago';
    if (s < 86400) return Math.round(s / 3600) + ' h ago'; if (s < 86400 * 2) return 'yesterday';
    return Math.round(s / 86400) + ' days ago';
  };
  const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent && parent.appendChild(e); return e; };
  const primaryCat = it => (it.filters || []).find(f => CATS.some(c => c[0] === f)) || 'other';

  function buckets(range) {
    const now = new Date(), out = [];
    if (range === 'today') {
      const d0 = startOfDay(now);
      for (let i = 0; i < 12; i++) {
        const a = new Date(+d0 + i * 2 * 3600e3), h = a.getHours();
        out.push({ a, b: new Date(+a + 2 * 3600e3), label: (h % 12 || 12) + (h < 12 ? ' AM' : ' PM'), full: a.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) + ' – ' + new Date(+a + 2 * 3600e3).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) });
      }
    } else {
      const n = range === 'week' ? 7 : 30, d0 = startOfDay(now);
      for (let i = n - 1; i >= 0; i--) {
        const a = new Date(+d0 - i * DAY);
        out.push({ a, b: new Date(+a + DAY), label: n === 7 ? a.toLocaleDateString('en-GB', { weekday: 'short' }) : (i % 5 === 0 ? a.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : ''), full: a.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }) });
      }
    }
    out.forEach(bk => {
      const cs = D.commits.filter(c => c.date >= bk.a && c.date < bk.b);
      bk.all = cs.length; bk.admin = cs.filter(c => c.admin).length;
    });
    return out;
  }

  /* ---------------- dashboard ---------------- */
  function renderDashboard() {
    const S = D.settings, items = D.items, revs = D.reviews;
    const first = (S.name || 'Khadijat').split(' ')[0];
    const h = new Date().getHours();
    $('#greeting').textContent = `${h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'}, ${first}! 👋`;
    $('#userName').textContent = S.name || first;
    $('#today').textContent = fmtDate(new Date());

    // stat cards
    const counts = CATS.map(c => items.filter(it => primaryCat(it) === c[0]).length);
    $('#stCases').textContent = items.length;
    $('#stCasesSub').innerHTML = `<i>${items.filter(i => i.new).length}</i> marked New`;
    const mx = Math.max(1, ...counts);
    $('#miniCases').innerHTML = counts.map((n, i) => `<span title="${esc(CATS[i][1])}: ${n}" style="height:${8 + 30 * n / mx}px"></span>`).join('');
    $('#stReviews').textContent = revs.length;
    $('#stReviewsSub').innerHTML = `<i>+${D.popups.length}</i> review pop-ups`;
    $('#miniReviews').textContent = '★★★★★';
    const avg = revs.length ? revs.reduce((s, r) => s + (+r.rating || 5), 0) / revs.length : 0;
    $('#stRating').textContent = avg.toFixed(1);
    $('#stRatingSub').innerHTML = `across <i>${revs.length}</i> reviews`;
    $('#miniRating').textContent = '★'.repeat(Math.round(avg)) + '☆'.repeat(5 - Math.round(avg));
    const now = Date.now();
    const week = D.commits.filter(c => now - c.date < 7 * DAY).length;
    $('#stUpdates').textContent = D.commitsOk ? D.commits.filter(c => now - c.date < 30 * DAY).length : '–';
    $('#stUpdatesSub').innerHTML = D.commitsOk ? `<i>${week}</i> this week` : 'sign in to see';
    const days = [...Array(14)].map((_, i) => { const a = +startOfDay(new Date()) - (13 - i) * DAY; return D.commits.filter(c => c.date >= a && c.date < a + DAY).length; });
    const sm = Math.max(1, ...days), sp = $('#spark'); sp.innerHTML = '';
    const pts = days.map((v, i) => [i * 100 / 13, 31 - v / sm * 27]);
    el('path', { d: smooth(pts) + ' L100 34 L0 34 Z', fill: 'rgba(245,184,46,.15)', stroke: 'none' }, sp);
    el('path', { d: smooth(pts), fill: 'none', stroke: C.yellow, 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke' }, sp);

    renderChart();

    // chart footer
    const t0 = +startOfDay(new Date());
    $('#cfToday').textContent = D.commits.filter(c => c.date >= t0).length;
    $('#cfWeek').textContent = week;
    $('#cfLast').textContent = D.commits[0] ? ago(D.commits[0].date) : '–';
    const wk = buckets('month').filter(b => b.all);
    const busy = wk.sort((a, b) => b.all - a.all)[0];
    $('#cfBusy').textContent = busy ? `${busy.a.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} · ${busy.all}` : '–';

    // donut
    const other = items.length - counts.reduce((a, b) => a + b, 0);
    const parts = CATS.map((c, i) => ({ label: c[1], n: counts[i], color: c[2] })).concat(other ? [{ label: 'Other', n: other, color: C.grey }] : []).filter(p => p.n);
    const dn = $('#donut'); dn.innerHTML = '';
    const R = 46, L = 2 * Math.PI * R; let off = 0;
    el('circle', { cx: 60, cy: 60, r: R, fill: 'none', stroke: '#F3EFEA', 'stroke-width': 18 }, dn);
    parts.forEach(p => {
      const len = L * p.n / items.length;
      const c = el('circle', { cx: 60, cy: 60, r: R, fill: 'none', stroke: p.color, 'stroke-width': 18, 'stroke-dasharray': `${Math.max(len - 1.5, 0)} ${L}`, 'stroke-dashoffset': -off, transform: 'rotate(-90 60 60)' }, dn);
      el('title', {}, c).textContent = `${p.label}: ${p.n}`;
      off += len;
    });
    el('circle', { cx: 60, cy: 60, r: 33, fill: '#fff', stroke: '#F3EFEA' }, dn);
    const tt = el('text', { x: 60, y: 61, 'font-size': 17, 'font-weight': 600, fill: '#1F1A17' }, dn); tt.textContent = items.length;
    const ts = el('text', { x: 60, y: 73, 'font-size': 6, fill: '#7A726B', 'letter-spacing': .5 }, dn); ts.textContent = 'PROJECTS';
    $('#donutLegend').innerHTML = parts.map(p => `<li><i style="background:${p.color}"></i><span>${esc(p.label)}<small>${p.n} project${p.n === 1 ? '' : 's'}</small></span><b>${Math.round(p.n / items.length * 100)}%</b></li>`).join('');
    const top = parts.slice().sort((a, b) => b.n - a.n)[0];
    $('#topCat').innerHTML = top ? `<b style="display:inline;color:inherit;font-size:inherit">${esc(top.label)}</b> is your biggest portfolio category.` : '';

    // latest projects
    $('#latest').innerHTML = items.slice(0, 5).map((it, i) => {
      const tag = it.new ? '<em>New</em>' : it.collaboration ? '<em class="collab">Collab</em>' : it.show_in_hero ? '<em>In hero</em>' : '';
      return `<li><span class="n">${i + 1}</span><img src="${esc(it.thumbnail)}" alt="" loading="lazy"><span><b>${esc(it.title)}</b><small>${esc(it.category)}</small></span>${tag}</li>`;
    }).join('');

    // gauge
    const collab = items.filter(i => i.collaboration).length;
    const hero = items.filter(i => !i.collaboration && i.show_in_hero).length;
    const grid = items.length - collab - hero;
    const segs = [{ n: hero, color: C.green }, { n: grid, color: C.yellow }, { n: collab, color: C.accent }];
    const g = $('#gauge'); g.innerHTML = '';
    const arc = (a0, a1, r) => { const p = a => [100 + r * Math.cos(Math.PI * (1 - a)), 100 - r * Math.sin(Math.PI * (1 - a))]; const [x0, y0] = p(a0), [x1, y1] = p(a1); return `M${x0} ${y0} A${r} ${r} 0 0 1 ${x1} ${y1}`; };
    el('path', { d: arc(0, 1, 78), fill: 'none', stroke: '#F3EFEA', 'stroke-width': 22 }, g);
    let a = 0;
    segs.forEach(s => { if (!s.n) return; const b = a + s.n / items.length; el('path', { d: arc(a + .004, b - .004, 78), fill: 'none', stroke: s.color, 'stroke-width': 22 }, g); a = b; });
    const gt = el('text', { x: 100, y: 92, 'font-size': 24, 'font-weight': 600, fill: '#1F1A17' }, g); gt.textContent = items.length;
    const gs = el('text', { x: 100, y: 106, 'font-size': 9, fill: '#7A726B' }, g); gs.textContent = 'projects live';
    const pct = n => Math.round(n / Math.max(items.length, 1) * 100) + '%';
    const newN = items.filter(i => i.new).length;
    $('#statusBoxes').innerHTML = [
      ['In hero', hero, 'var(--green-soft)', 'var(--green)'], ['Grid only', grid, 'var(--yellow-soft)', '#D99A0B'],
      ['Collabs', collab, 'var(--accent-soft)', 'var(--accent)'], ['New badge', newN, '#F3EFEA', '#5A514A'],
    ].map(([l, n, bg, fg]) => `<div><span style="background:${bg};color:${fg}">${pct(n)}</span><b>${n}</b><small>${l}</small></div>`).join('');

    // insights
    const feat = revs.find(r => r.featured) || revs[0] || {};
    const newest = items[0] || {};
    const heroFirst = items.filter(i => i.show_in_hero && i.cover).sort((x, y) => ((+x.hero_order || 999) - (+y.hero_order || 999)))[0] || {};
    $('#insights').innerHTML = `
      <div><small>Newest project</small><b>${esc(newest.title || '–')}</b><p>${esc(newest.category || '')}</p></div>
      <div><small>First book in the hero</small><b>${esc(heroFirst.title || '–')}</b><p>${esc(heroFirst.hero_caption || '')}</p></div>
      <div><small>Featured review</small><b>${esc(feat.name || '–')}</b><p>${'★'.repeat(+feat.rating || 5)}</p></div>
      <div><small>Pages on your site</small><b>${1 + D.pages.length} pages</b><p><i>${D.faq.length}</i> FAQs on the home page</p></div>`;
    $('#cheer').textContent = week ? `Nice! You updated your website ${week} time${week === 1 ? '' : 's'} this week. 🎉` : 'Keep going! Your portfolio is looking great. 🎉';
    $('#dataNote').textContent = D.commitsOk ? '' : 'Website activity appears after you sign in.';

    // bell
    const recent = D.commits.filter(c => now - c.date < DAY);
    $('#bellCount').hidden = !recent.length; $('#bellCount').textContent = recent.length;
    $('#bellList').innerHTML = D.commits.slice(0, 6).map(c => `<li>${esc(c.msg.replace(/\s*\(admin\)$/, ''))}<small>${ago(c.date)}</small></li>`).join('') || '<li>No updates in the last 30 days.</li>';
  }

  /* smooth line through points */
  function smooth(p) {
    if (!p.length) return '';
    let d = `M${p[0][0]} ${p[0][1]}`;
    for (let i = 0; i < p.length - 1; i++) {
      const p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C${c1[0]} ${Math.min(c1[1], Math.max(p1[1], p2[1]))} ${c2[0]} ${Math.min(c2[1], Math.max(p1[1], p2[1]))} ${p2[0]} ${p2[1]}`;
    }
    return d;
  }

  function renderChart() {
    const box = $('#chart'), B = buckets(RANGE);
    const W = Math.max(box.clientWidth, 280), H = box.clientHeight, pl = 28, pr = 10, pt = 26, pb = 26;
    const max = Math.max(4, Math.ceil(Math.max(...B.map(b => b.all)) / 4) * 4);
    const X = i => pl + (W - pl - pr) * (B.length === 1 ? .5 : i / (B.length - 1)), Y = v => pt + (H - pt - pb) * (1 - v / max);
    box.innerHTML = '';
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}` }, box);
    const defs = el('defs', {}, svg);
    [['gO', C.accent], ['gG', C.green]].forEach(([id, col]) => {
      const lg = el('linearGradient', { id, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      el('stop', { offset: 0, 'stop-color': col, 'stop-opacity': .22 }, lg); el('stop', { offset: 1, 'stop-color': col, 'stop-opacity': 0 }, lg);
    });
    for (let k = 0; k <= 4; k++) {
      const v = max * k / 4, y = Y(v);
      el('line', { x1: pl, x2: W - pr, y1: y, y2: y, stroke: '#F0ECE7', 'stroke-dasharray': k ? '3 4' : '' }, svg);
      el('text', { x: pl - 8, y: y + 3.5, 'text-anchor': 'end' }, svg).textContent = v;
    }
    B.forEach((b, i) => { if (b.label) el('text', { x: X(i), y: H - 6, 'text-anchor': 'middle' }, svg).textContent = b.label; });
    [['all', C.accent, 'gO'], ['admin', C.green, 'gG']].forEach(([k, col, gid]) => {
      const pts = B.map((b, i) => [X(i), Y(b[k])]);
      el('path', { d: smooth(pts) + ` L${X(B.length - 1)} ${Y(0)} L${X(0)} ${Y(0)} Z`, fill: `url(#${gid})` }, svg);
      el('path', { d: smooth(pts), fill: 'none', stroke: col, 'stroke-width': 2.5, 'stroke-linecap': 'round' }, svg);
    });
    // peak marker, like the template's price pill
    const peak = B.reduce((m, b, i) => b.all > B[m].all ? i : m, 0);
    if (B[peak].all) {
      const x = X(peak), y = Y(B[peak].all), label = `${B[peak].all} update${B[peak].all === 1 ? '' : 's'}`, w = label.length * 6 + 14;
      el('line', { x1: x, x2: x, y1: y, y2: Y(0), stroke: C.accent, 'stroke-dasharray': '3 3', opacity: .5 }, svg);
      el('rect', { x: x - w / 2, y: y - 25, width: w, height: 18, rx: 9, fill: C.accent }, svg);
      const t = el('text', { x, y: y - 12.5, 'text-anchor': 'middle', fill: '#fff', style: 'fill:#fff;font-weight:600;font-size:10.5px' }, svg); t.textContent = label;
      el('circle', { cx: x, cy: y, r: 4.5, fill: '#fff', stroke: C.accent, 'stroke-width': 2.5 }, svg);
    }
    // hover
    const guide = el('line', { y1: pt, y2: Y(0), stroke: '#CFC8C1', 'stroke-dasharray': '3 3', opacity: 0 }, svg);
    const dots = [C.accent, C.green].map(c => el('circle', { r: 4.5, fill: '#fff', stroke: c, 'stroke-width': 2.5, opacity: 0 }, svg));
    const tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; box.appendChild(tip);
    const hit = el('rect', { x: pl, y: 0, width: W - pl - pr, height: H, fill: 'transparent' }, svg);
    const move = e => {
      const r = svg.getBoundingClientRect(), mx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
      const i = Math.max(0, Math.min(B.length - 1, Math.round((mx * W / r.width - pl) / ((W - pl - pr) / Math.max(B.length - 1, 1)))));
      const x = X(i);
      guide.setAttribute('x1', x); guide.setAttribute('x2', x); guide.setAttribute('opacity', 1);
      dots[0].setAttribute('cx', x); dots[0].setAttribute('cy', Y(B[i].all)); dots[1].setAttribute('cx', x); dots[1].setAttribute('cy', Y(B[i].admin));
      dots.forEach(d => d.setAttribute('opacity', 1));
      tip.hidden = false; tip.style.left = (x * r.width / W) + 'px'; tip.style.top = (Y(B[i].all) * r.height / H) + 'px';
      tip.innerHTML = `<b>${esc(B[i].full)}</b><i style="background:${C.accent}"></i>${B[i].all} updates<br><i style="background:${C.green}"></i>${B[i].admin} in admin`;
    };
    const leave = () => { tip.hidden = true; guide.setAttribute('opacity', 0); dots.forEach(d => d.setAttribute('opacity', 0)); };
    hit.addEventListener('mousemove', move); hit.addEventListener('touchstart', move, { passive: true }); hit.addEventListener('mouseleave', leave);
  }
  $$('#rangeTabs button').forEach(b => b.addEventListener('click', () => {
    RANGE = b.dataset.r; $$('#rangeTabs button').forEach(x => x.classList.toggle('on', x === b)); renderChart();
  }));
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => D && !$('#dashboard').hidden && renderChart(), 150); });

  /* ---------------- search ---------------- */
  const sIn = $('#search'), sOut = $('#searchResults');
  sIn.addEventListener('input', () => {
    const q = sIn.value.trim().toLowerCase();
    if (!q || !D) { sOut.hidden = true; return; }
    const hits = [
      ...D.items.map(i => [i.title, 'Portfolio', 'portfolio']),
      ...D.reviews.map(r => [r.name + ': ' + r.quote, 'Review', 'reviews']),
      ...D.pages.map(p => [p.menu_name, 'Service page', 'service_pages']),
      ...D.faq.map(f => [f.question, 'FAQ', 'faq']),
      ...['Hero', 'About me', 'Contact', 'How it works', 'Before / after', 'Final call to action'].map(s => [s, 'Home page', 'home']),
      ...['Email', 'WhatsApp', 'Calendly', 'Fiverr', 'Upwork', 'LinkedIn', 'Instagram', 'Google title'].map(s => [s, 'Settings', 'settings']),
    ].filter(h => String(h[0]).toLowerCase().includes(q)).slice(0, 8);
    sOut.innerHTML = hits.length ? hits.map(h => `<a href="#${h[2]}"><span>${esc(String(h[0]).slice(0, 60))}</span><small>${h[1]}</small></a>`).join('') : '<p>No matches.</p>';
    sOut.hidden = false;
  });
  sOut.addEventListener('click', () => { sOut.hidden = true; sIn.value = ''; });
  document.addEventListener('click', e => {
    if (!e.target.closest('.search')) sOut.hidden = true;
    [['#bell', '#bellPop'], ['#userBtn', '#userPop']].forEach(([b, p]) => { if (!e.target.closest(b) && !e.target.closest(p)) $(p).hidden = true; });
  });
  $('#bell').addEventListener('click', () => { $('#bellPop').hidden = !$('#bellPop').hidden; });
  $('#userBtn').addEventListener('click', () => { $('#userPop').hidden = !$('#userPop').hidden; });

  /* ---------------- views ---------------- */
  const side = $('#side');
  $('#burger').addEventListener('click', () => side.classList.add('open'));
  $('#scrim').addEventListener('click', () => side.classList.remove('open'));
  const frame = $('#editor');
  frame.addEventListener('load', () => {
    // Hide the editor's own top bar: the dashboard sidebar replaces it
    try {
      const d = frame.contentDocument, st = d.createElement('style');
      st.textContent = `
        header[class*="AppHeader"]{display:none!important}
        body{background:#F7F5F2!important}
        body,button,input,textarea,select{font-family:Poppins,system-ui,sans-serif!important}
        [class*="PublishButton"],[class*="SaveButton"]{background:#F15A22!important;color:#fff!important}
        [class*="ToolbarContainer"]{border-bottom:1px solid #EEEAE5!important;box-shadow:none!important}
        a[class*="SidebarNavLink"][class*="active"],[class*="active"][class*="SidebarNavLink"]{border-left-color:#F15A22!important;color:#F15A22!important}
        input:focus,textarea:focus{border-color:#F15A22!important}`;
      d.head.appendChild(st);
      const fl = d.createElement('link'); fl.rel = 'stylesheet';
      fl.href = 'https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap';
      d.head.appendChild(fl);
    } catch (e) {}
  });
  async function route() {
    const v = location.hash.slice(1) || 'dashboard';
    side.classList.remove('open'); scrollTo(0, 0);
    $$('#menu a').forEach(a => a.classList.toggle('on', a.dataset.view === v || (v === 'dashboard' && a.dataset.view === 'dashboard')));
    if (ROUTES[v]) {
      $('#pageTitle').textContent = ROUTES[v][0];
      document.title = ROUTES[v][0] + ' · Website admin';
      $('#dashboard').hidden = true; $('#editorView').hidden = false;
      const target = 'editor/#/' + ROUTES[v][1];
      if (!frame.getAttribute('src')) frame.src = target;
      else try { frame.contentWindow.location.hash = '#/' + ROUTES[v][1]; } catch (e) { frame.src = target; }
    } else {
      $('#pageTitle').textContent = 'Dashboard'; document.title = 'Dashboard · Website admin';
      $('#editorView').hidden = true; $('#dashboard').hidden = false;
      if (D) renderDashboard();
      try { await loadData(); renderDashboard(); } catch (e) { $('#dataNote').textContent = 'Could not load the latest data. Check your connection and refresh.'; }
    }
  }
  addEventListener('hashchange', route);

  function start() {
    if (!user() && (!LOCAL || /[?&]login\b/.test(location.search))) { $('#login').hidden = false; $('#app').hidden = true; return; }
    $('#login').hidden = true; $('#app').hidden = false;
    route();
  }
  start();
})();
