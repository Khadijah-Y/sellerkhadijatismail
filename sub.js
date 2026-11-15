/* Shared script for the service pages (lighter than main.js) */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // nav: solid background on scroll, phone menu
  const nav = $('.nav'), menuBtn = $('#menuBtn'), links = $('#navlinks');
  const onScroll = () => {
    nav.classList.toggle('scrolled', scrollY > 30);
    document.body.classList.toggle('scrolled-far', scrollY > innerHeight * 0.8);
  };
  addEventListener('scroll', onScroll, { passive: true }); onScroll();
  const setMenu = open => { links.classList.toggle('open', open); menuBtn.setAttribute('aria-expanded', open); document.body.style.overflow = open ? 'hidden' : ''; };
  menuBtn.addEventListener('click', () => setMenu(!links.classList.contains('open')));
  $$('a', links).forEach(a => a.addEventListener('click', () => setMenu(false)));

  // reveal on scroll
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target, sibs = $$(':scope > .reveal', el.parentElement);
    el.style.transitionDelay = Math.min(sibs.indexOf(el), 6) * 80 + 'ms';
    el.classList.add('in'); io.unobserve(el);
  }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  $$('.reveal').forEach(el => io.observe(el));
  document.body.classList.add('ready');

  // quote form → WhatsApp or email
  const form = $('#quoteForm');
  if (form) {
    const err = $('#formErr'); let via = 'wa';
    $$('button[type=submit]', form).forEach(b => b.addEventListener('click', () => { via = b.dataset.via; }));
    form.addEventListener('input', () => { err.textContent = ''; });
    form.addEventListener('submit', e => {
      e.preventDefault();
      const fd = new FormData(form), name = (fd.get('name') || '').trim();
      if (!name) { err.textContent = 'Please add your name first.'; form.querySelector('[name=name]').focus(); return; }
      const lines = [`Hi Khadijat, I'd like a quote.`, ``, `Name: ${name}`,
        fd.get('title') ? `Book: ${fd.get('title')}` : '', `Service: ${fd.get('service')}`,
        fd.get('words') ? `Word count: ${fd.get('words')}` : '', `Formats: ${fd.getAll('fmt').join(', ') || 'Not sure'}`,
        fd.get('msg') ? `\n${fd.get('msg')}` : ''].filter(Boolean).join('\n');
      const url = via === 'wa'
        ? 'https://wa.me/2349021651449?text=' + encodeURIComponent(lines)
        : 'mailto:khadijahismail525@gmail.com?subject=' + encodeURIComponent('Book project quote: ' + (fd.get('title') || name)) + '&body=' + encodeURIComponent(lines);
      err.textContent = '';
      window.open(url, '_blank', 'noopener');
    });
  }

  const yr = $('#yr'); if (yr) yr.textContent = new Date().getFullYear();
  if (!reduce) setTimeout(() => { const w = $('.fb-wa'); if (w) { w.classList.add('tip'); setTimeout(() => w.classList.remove('tip'), 3500); } }, 5000);
})();
