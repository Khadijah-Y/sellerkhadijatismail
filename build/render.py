"""Builds the website from the content files.

    content/*.json  (edited in the admin at /admin)  ->  public/  (what Vercel publishes)

Run locally:  python build/render.py      Vercel runs the same command on every save.
Text conventions in the admin: *words* = gold italic, **words** = bold, a new line = line break.
"""
import os, re, json, html, shutil, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public')
STATIC = ['styles.css', 'main.js', 'sub.js', 'favicon.svg', 'favicon-32.png', 'apple-touch-icon.png', 'icon-512.png',
          'robots.txt', 'privacy.html', 'terms.html', 'assets', 'case-studies', 'admin']
FILTERS = [('nonfiction', 'Self-help & nonfiction'), ('workbook', 'Workbooks'), ('guide', 'Cookbooks & guides'), ('fiction', "Fiction & children's")]


def load(name):
    with open(os.path.join(ROOT, 'content', name), encoding='utf-8') as f:
        return json.load(f)


S, HOME, SERV, WORK, REV, FAQ, SP = (load(n) for n in ('settings.json', 'home.json', 'services.json', 'portfolio.json', 'reviews.json', 'faq.json', 'service_pages.json'))
WORK = WORK.get('items', [])
URL = S['site_url'].rstrip('/')
VER = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M')          # cache-buster for css/js
e = lambda s: html.escape(str(s or ''), quote=True)


def rich(s):
    """Admin text -> HTML: escape, then *x* -> <em>, **x** -> <b>, newline -> <br>."""
    s = e(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    return s.replace('\n', '<br>')


def plain(s):
    return re.sub(r'\*+', '', str(s or '')).replace('\n', ' ')


def asset(p):
    """Content paths are '/assets/...'; pages use relative paths so they also work when opened locally."""
    p = str(p or '')
    return p[1:] if p.startswith('/') else p


def wa(text=''):
    return f"https://wa.me/{e(S['whatsapp_number'])}" + (f"?text={quote(text)}" if text else '')


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')


def items_ok(lst):
    return [x for x in (lst or []) if x]


ICONS = open(os.path.join(ROOT, 'templates', 'icons.svg'), encoding='utf-8').read()
PAGES = SP.get('pages', [])
SERVICE_LINKS = [(p['slug'], p.get('menu_name') or p['service']) for p in PAGES]
for it in WORK:
    it['id'] = it.get('id') or slug(it.get('title', 'project'))


# ------------------------------------------------------------------ shared pieces
def head(title, desc, canonical, extra=''):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{e(S['name'])}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="google-site-verification" content="{e(S.get('google_verification', ''))}" />
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(S['name'])} · {e(S['role'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{URL}/assets/misc/share.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{URL}/assets/misc/share.jpg">
<meta name="theme-color" content="#16130F">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{extra}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css?v={VER}">
</head>'''


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>\n'


def brand(home_link=True):
    return (f'<a class="brand" href="./" aria-label="{e(S["name"])}, home page"{" data-home" if home_link else ""}><span class="mono">{e(S.get("monogram", "KI"))}</span>'
            f'<span class="brand-text"><b>{e(S["name"])}</b><small>{e(S["role"])}</small></span></a>')


def footer(prefix=''):
    svc = ''.join(f'<a href="{e(s)}.html">{e(n)}</a>' for s, n in SERVICE_LINKS)
    socials = [('wa', wa(), 'WhatsApp'), ('in', S.get('linkedin'), 'LinkedIn'), ('up', S.get('upwork'), 'Upwork'), ('fi', S.get('fiverr'), 'Fiverr'),
               ('ig', S.get('instagram'), 'Instagram'), ('mail', f"mailto:{S['email']}", 'Email')]
    soc = ''
    for icon, href, label in socials:
        if not href:
            continue
        ext = '' if href.startswith('mailto') else ' target="_blank" rel="noopener"'
        inner = 'fi' if icon == 'fi' else f'<svg viewBox="0 0 24 24"><use href="#i-{icon}"/></svg>'
        cls = ' class="s-fi"' if icon == 'fi' else ''
        soc += f'<a href="{e(href)}"{ext} aria-label="{label}"{cls}>{inner}</a>'
    contact = f'<a href="{wa()}" target="_blank" rel="noopener">WhatsApp</a><a href="mailto:{e(S["email"])}">Email me</a>'
    if S.get('fiverr'):
        contact += f'<a href="{e(S["fiverr"])}" target="_blank" rel="noopener">Order on Fiverr</a>'
    if S.get('upwork'):
        contact += f'<a href="{e(S["upwork"])}" target="_blank" rel="noopener">Hire on Upwork</a>'
    contact += f'<a href="{prefix}#leave-review">Leave a review</a>'
    return f'''<footer class="foot">
  <div class="wrap foot-cols">
    <div class="foot-about">
      {brand(prefix == '')}
      <p>{e(S.get('footer_about', ''))}</p>
      <div class="socials">{soc}</div>
    </div>
    <nav aria-label="Services"><h4>Services</h4>{svc}</nav>
    <nav aria-label="Explore"><h4>Explore</h4><a href="{prefix}#work">Portfolio</a><a href="{prefix}#about">About me</a><a href="{prefix}#reviews">Reviews</a><a href="{prefix}#faq">FAQ</a><a href="{prefix}#contact">Get a quote</a></nav>
    <nav aria-label="Contact"><h4>Contact</h4>{contact}
      <a class="btn btn-gold btn-sm foot-btn" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a call →</a>
    </nav>
  </div>
  <div class="wrap foot-bottom">
    <p>© <span id="yr">{datetime.date.today().year}</span> {e(S['name'])}. All rights reserved. {e(S.get('footer_note', ''))}</p>
    <p><a href="privacy.html">Privacy Policy</a> · <a href="terms.html">Terms of Service</a></p>
  </div>
</footer>
'''


def floating():
    out = '<div class="float-btns" aria-label="Quick contact">\n'
    if S.get('linkedin'):
        out += f'  <a class="fb fb-sm" href="{e(S["linkedin"])}" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24"><use href="#i-in"/></svg></a>\n'
    if S.get('upwork'):
        out += f'  <a class="fb fb-sm" href="{e(S["upwork"])}" target="_blank" rel="noopener" aria-label="Hire me on Upwork" title="Hire me on Upwork"><svg viewBox="0 0 24 24"><use href="#i-up"/></svg></a>\n'
    if S.get('fiverr'):
        out += f'  <a class="fb fb-sm fb-fi" href="{e(S["fiverr"])}" target="_blank" rel="noopener" aria-label="Order on Fiverr" title="Order on Fiverr">fi</a>\n'
    out += f'  <a class="fb fb-wa" href="{wa("Hi " + S["name"].split()[0] + ", I have a question about my book.")}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp" title="Chat on WhatsApp"><svg viewBox="0 0 24 24"><use href="#i-wa"/></svg><span class="fb-tip">Chat with me</span></a>\n</div>\n'
    return out


def contact_rows():
    rows = ''
    for r in HOME['contact'].get('rows', []):
        link = r.get('link', '')
        inner = f'<span>{e(r.get("label"))}</span><b>{rich(r.get("value"))}</b>'
        if link:
            ext = '' if link.startswith('mailto') else ' target="_blank" rel="noopener"'
            rows += f'<a class="info" href="{e(link)}"{ext}>{inner}</a>\n'
        else:
            rows += f'<div class="info">{inner}</div>\n'
    li = f'<li><a href="{e(S["linkedin"])}" target="_blank" rel="noopener"><span>LinkedIn</span>{e(S.get("linkedin_label", "LinkedIn"))} ↗</a></li>' if S.get('linkedin') else ''
    return f'<div class="info-grid">\n{rows}</div>\n<ul class="channels">{li}</ul>'


def quote_form(selected=None):
    opts = ['Formatting & typesetting', 'Proofreading', 'Copy editing', 'Cover design', 'Translation', 'Developmental editing', 'Several of these', 'Not sure yet']
    o = ''.join(f'<option{" selected" if x == selected else ""}>{e(x)}</option>' for x in opts)
    return f'''<form class="quote reveal" id="quoteForm" novalidate>
      <h3>Request a quote</h3>
      <label>Your name<input name="name" required autocomplete="name"></label>
      <label>Book title or working title<input name="title"></label>
      <div class="row2">
        <label>Service<select name="service">{o}</select></label>
        <label>Approx. word count<input name="words" inputmode="numeric" placeholder="45,000"></label>
      </div>
      <label>Formats needed</label>
      <div class="chips">
        <label><input type="checkbox" name="fmt" value="Paperback" checked><span>Paperback</span></label>
        <label><input type="checkbox" name="fmt" value="Hardcover"><span>Hardcover</span></label>
        <label><input type="checkbox" name="fmt" value="Ebook"><span>Ebook</span></label>
      </div>
      <label>Anything else?<textarea name="msg" rows="3" placeholder="Genre, launch date, images, questions…"></textarea></label>
      <p class="err" id="formErr" role="alert"></p>
      <div class="form-btns">
        <button type="submit" class="btn btn-gold" data-via="wa">Send on WhatsApp</button>
        <button type="submit" class="btn btn-ghost" data-via="mail">Send by email</button>
      </div>
    </form>'''


def hero_books():
    hero = [w for w in WORK if w.get('show_in_hero') and w.get('cover')]
    hero.sort(key=lambda w: int(w.get('hero_order') or 0) or 999)   # stable: 0 keeps grid order, after numbered ones
    return hero


def site_data():
    hero = hero_books()
    data = {'name': S['name'], 'first': S['name'].split()[0], 'email': S['email'], 'whatsapp': S['whatsapp_number'],
            'hero': [{'cover': asset(w['cover']), 'ar': float(w.get('cover_ratio') or 0.667), 'kicker': w.get('hero_caption') or w.get('category', ''), 'title': w['title']} for w in hero],
            'popups': [{'q': p['quote'], 'n': p['name']} for p in REV.get('popups', []) if p.get('quote')]}
    return '<script>window.SITE = ' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';</script>\n'


# ------------------------------------------------------------------ home page
def section_head(d, cls='section-head reveal'):
    sub = f'<p class="sub">{rich(d.get("subtitle"))}</p>' if d.get('subtitle') else ''
    return f'<div class="{cls}"><p class="eyebrow">{e(d.get("eyebrow"))}</p><h2>{rich(d.get("title"))}</h2>{sub}</div>'


def home():
    H = HOME
    hero = H['hero']
    proof = ''.join(f'<li>{rich(p).replace("★★★★★", "<span class=\"stars\" aria-label=\"5 stars\">★★★★★</span>")}</li>' for p in items_ok(hero.get('proof')))
    plat = ''.join(f'<span>{e(p)}</span><i>✦</i>' for p in items_ok(H['platforms'].get('items')))
    svcs = ''
    for i, s in enumerate(SERV.get('services', [])):
        tag = f'<span class="tag">{e(s["tag"])}</span>' if s.get('tag') else ''
        pts = ''.join(f'<li>{e(p)}</li>' for p in items_ok(s.get('points')))
        more = f'<a class="svc-more" href="{e(s["page"])}.html" aria-label="Learn more about {e(s["title"].lower())}">Learn more <span aria-hidden="true">→</span></a>' if s.get('page') else ''
        svcs += f'''<article class="svc{' svc-alt' if s.get('dark') else ''} reveal"><span class="svc-num">{i + 1:02d}</span>{tag}<h3>{e(s['title'])}</h3><p>{e(s.get('text'))}</p><ul>{pts}</ul>{more}</article>\n'''
    cmpd = H['compare']
    used = sorted({f for w in WORK for f in (w.get('filters') or [])})
    filt = '<button class="on" data-f="all">All work</button>' + ''.join(f'<button data-f="{k}">{e(n)}</button>' for k, n in FILTERS if k in used)
    if any(w.get('collaboration') for w in WORK):
        filt += '<button data-f="collab">Collaborations</button>'
    cards = ''
    for w in WORK:
        f = ' '.join((w.get('filters') or []) + (['collab'] if w.get('collaboration') else []))
        slides = [asset(x) for x in items_ok(w.get('slides'))]
        n = len(slides) or int(w.get('slide_count') or 0)
        strip = asset(w.get('slides_strip')) if not slides and w.get('slides_strip') else ''
        badges = ('<span class="badge badge-new">New</span>' if w.get('new') else '')
        if w.get('collaboration'):
            badges += '<span class="badge" style="left:auto;right:12px">Collaboration</span>' if w.get('new') else '<span class="badge">Collaboration</span>'
        pdf = asset(w.get('pdf'))
        cards += (f'<article class="card reveal" data-f="{e(f)}" data-id="{e(w["id"])}" data-n="{n}" data-pdf="{e(pdf)}" data-strip="{e(strip)}" data-slides="{e(json.dumps(slides))}">\n'
                  f'  <button class="thumb" aria-label="Open case study: {e(w["title"])}">{badges}<img src="{e(asset(w.get("thumbnail")))}" width="820" height="461" alt="{e(w["title"])} – {e(w.get("category", "").lower())} case study: {e(w.get("description", "").lower())}" loading="lazy"></button>\n'
                  f'  <div class="meta"><span class="k">{e(w.get("category"))}</span><h3>{e(w["title"])}</h3><p>{e(w.get("description"))}</p>'
                  + (f'<a class="pdf-link" href="{e(pdf)}">Case study PDF</a>' if pdf else '') + '</div>\n</article>\n')
    A = H['about']
    cnt = ''
    for c in A.get('counters', []):
        num = len(WORK) if c.get('auto_case_studies') else c.get('number', 0)
        dec = f' data-dec="{int(c["decimals"])}"' if c.get('decimals') else ''
        suf = f' data-suffix="{e(c["suffix"])}"' if c.get('suffix') else ''
        cnt += f'<div><b data-count="{num}"{suf}{dec}>0</b><span>{e(c.get("label"))}</span></div>'
    paras = ''.join(f'<p class="reveal">{rich(p)}</p>' for p in items_ok(A.get('paragraphs')))
    steps = ''.join(f'<li class="reveal"><span>{i + 1}</span><h3>{e(s["title"])}</h3><p>{e(s.get("text"))}</p></li>' for i, s in enumerate(H['process'].get('steps', [])))
    revs = ''
    for r in REV.get('reviews', []):
        tags = f'<p class="rv-tags">{e(r["tags"])}</p>' if r.get('tags') else ''
        stars = '★' * int(r.get('rating') or 5)
        revs += (f'<figure class="rv{" rv-big" if r.get("featured") else ""} reveal"><div class="stars" aria-label="{len(stars)} stars">{stars}</div>'
                 f'<blockquote>“{e(r["quote"])}”</blockquote>{tags}<figcaption><span class="av">{e((r.get("name") or "A")[0].upper())}</span><b>{e(r.get("name"))}</b><small>{e(r.get("details"))}</small></figcaption></figure>\n')
    L = H['leave_review']
    points = ''.join(f'<li>{e(p)}</li>' for p in items_ok(L.get('points')))
    if S.get('fiverr'):
        points += f'<li>Prefer Fiverr? <a href="{e(S["fiverr"])}" target="_blank" rel="noopener">Review me there ↗</a></li>'
    faqs = FAQ.get('questions', [])
    faq = ''.join(f'<details class="reveal"><summary>{e(q["question"])}</summary><p>{e(q["answer"])}</p></details>' for q in faqs)
    C, FC = H['contact'], H['final_cta']
    first_cover = next((asset(w['cover']) for w in hero_books()), '')
    org = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Person', '@id': f'{URL}/#khadijat', 'name': S['name'], 'jobTitle': S['role'], 'image': f'{URL}/{asset(A.get("photo"))}', 'url': f'{URL}/',
         'email': f'mailto:{S["email"]}', 'telephone': '+' + S['whatsapp_number'],
         'sameAs': [x for x in (S.get('linkedin'), S.get('upwork'), S.get('instagram'), S.get('fiverr')) if x]},
        {'@type': 'ProfessionalService', '@id': f'{URL}/#service', 'name': f'{S["name"]} · {S["role"]}', 'url': f'{URL}/', 'image': f'{URL}/assets/misc/share.jpg',
         'email': S['email'], 'telephone': '+' + S['whatsapp_number'], 'founder': {'@id': f'{URL}/#khadijat'}, 'areaServed': 'Worldwide',
         'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Book publishing services',
                             'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['title'], 'description': s.get('text', '')}} for s in SERV.get('services', [])]}},
        {'@type': 'WebSite', '@id': f'{URL}/#website', 'url': f'{URL}/', 'name': f'{S["name"]} · {S["role"]}', 'publisher': {'@id': f'{URL}/#khadijat'}, 'inLanguage': 'en'}]}
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage',
              'mainEntity': [{'@type': 'Question', 'name': q['question'], 'acceptedAnswer': {'@type': 'Answer', 'text': q['answer']}} for q in faqs]}
    extra = (f'<link rel="preload" as="image" href="{e(first_cover)}" fetchpriority="high">\n' if first_cover else '') + ld(org)
    first, last = (S['name'].split(' ', 1) + [''])[:2]
    return head(S.get('seo_title') or S['name'], S.get('seo_description', ''), f'{URL}/', extra) + f'''
<body class="is-loading">

<div class="opener" id="opener" aria-hidden="true">
  <div class="op-half op-l"></div><div class="op-half op-r"></div>
  <div class="op-core">
    <svg class="op-ring" viewBox="0 0 120 120"><circle cx="60" cy="60" r="56"/></svg>
    <span class="op-mono">{e(S.get('monogram', 'KI'))}</span>
    <p class="op-name"><span>{e(first)}</span> <span>{e(last)}</span></p>
    <p class="op-role">{e(S['role'])}</p>
    <span class="op-bar"><i></i></span>
  </div>
</div>

<header class="nav" id="top">
  {brand()}
  <nav class="links" id="navlinks">
    <a href="#services">Services</a><a href="#work">Work</a><a href="#about">About</a><a href="#reviews">Reviews</a><a href="#faq">FAQ</a>
    <a class="btn btn-ghost btn-sm" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a call</a>
    <a class="btn btn-gold btn-sm" href="#contact">Get a quote</a>
  </nav>
  <button class="menu" id="menuBtn" aria-label="Open menu" aria-expanded="false"><span></span><span></span></button>
</header>

<main>
<section class="hero" aria-label="Introduction">
  <div class="hero-bg" id="heroBg" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow reveal">{e(hero.get('eyebrow'))}</p>
      <h1 class="reveal">{rich(hero.get('title'))}</h1>
      <p class="lead reveal">{rich(hero.get('lead'))}</p>
      <div class="cta-row reveal">
        <a class="btn btn-gold" href="#contact">{e(hero.get('button_primary'))} <span aria-hidden="true">→</span></a>
        <a class="btn btn-ghost" href="#work">{e(hero.get('button_secondary'))}</a>
      </div>
      <ul class="hero-proof reveal">{proof}</ul>
    </div>
    <div class="stage" id="stage" aria-roledescription="carousel" aria-label="Featured books">
      <div class="glow" aria-hidden="true"></div>
      <div class="books" id="books"></div>
      <div class="stage-caption" aria-live="polite"><span class="cap-kicker" id="capKicker"></span><span class="cap-title" id="capTitle"></span></div>
      <div class="stage-dots" id="dots" role="tablist" aria-label="Choose a book"></div>
    </div>
  </div>
  <a class="scroll-cue" href="#platforms" aria-label="Scroll down"><span></span></a>
</section>

<section class="platforms" id="platforms" aria-label="Platforms">
  <p class="eyebrow center">{e(H['platforms'].get('label'))}</p>
  <div class="marquee"><div class="track">{plat}{plat}</div></div>
</section>

<section class="section light" id="services">
  <div class="wrap">
    {section_head(H['services_section'])}
    <div class="services">
{svcs}    </div>
  </div>
</section>

<section class="section dark compare-sec">
  <div class="wrap compare-grid">
    <div class="reveal">
      <p class="eyebrow">{e(cmpd.get('eyebrow'))}</p>
      <h2>{rich(cmpd.get('title'))}</h2>
      <p class="sub">{rich(cmpd.get('text'))}</p>
      {f'<p class="credit">{e(cmpd["credit"])}</p>' if cmpd.get('credit') else ''}
    </div>
    <div class="compare reveal" id="compare" style="--pos:50%">
      <img src="{e(asset(cmpd.get('after_image')))}" alt="The page after formatting" loading="lazy">
      <div class="before"><img src="{e(asset(cmpd.get('before_image')))}" alt="The page before formatting" loading="lazy"></div>
      <span class="lbl l">Before</span><span class="lbl r">After</span>
      <input type="range" min="0" max="100" value="50" aria-label="Compare before and after" id="compareRange">
      <span class="handle" aria-hidden="true"><i>‹ ›</i></span>
    </div>
  </div>
</section>

<section class="section light" id="work">
  <div class="wrap">
    {section_head(H['work_section'])}
    <div class="filters reveal" id="filters" role="tablist" aria-label="Filter projects">{filt}</div>
    <div class="grid" id="grid">
{cards}    </div>
  </div>
</section>

<section class="section dark about" id="about">
  <div class="wrap about-grid">
    <div class="arch reveal">
      <img src="{e(asset(A.get('photo')))}" width="900" height="1047" alt="{e(S['name'])}" loading="lazy">
      <span class="arch-badge"><b>{e(A.get('badge_number'))}</b> {rich(A.get('badge_text'))}</span>
    </div>
    <div class="about-copy">
      <p class="eyebrow reveal">{e(A.get('eyebrow'))}</p>
      <h2 class="hello reveal">{e(A.get('hello'))} <span class="wave" aria-hidden="true">👋</span></h2>
      <p class="role reveal">{e(A.get('role'))}</p>
      {paras}
      <div class="counters reveal">{cnt}</div>
      <div class="cta-row reveal">
        <a class="btn btn-gold" href="#contact">Work with me</a>
        {f'<a class="btn btn-ghost" href="{e(S["linkedin"])}" target="_blank" rel="noopener">LinkedIn ↗</a>' if S.get('linkedin') else ''}
      </div>
    </div>
  </div>
</section>

<section class="section light">
  <div class="wrap">
    {section_head(H['process'])}
    <ol class="steps">{steps}</ol>
  </div>
</section>

<section class="section dark" id="reviews">
  <div class="wrap">
    {section_head(H['reviews_section'])}
    <div class="reviews">
{revs}    </div>
    {f'<p class="rv-more reveal"><a href="{e(S["fiverr"])}" target="_blank" rel="noopener">{e(H["reviews_section"].get("more_link_text"))}</a></p>' if S.get('fiverr') else ''}
  </div>
</section>

<section class="section light leave" id="leave-review">
  <div class="wrap leave-grid">
    <div class="reveal">
      <p class="eyebrow">{e(L.get('eyebrow'))}</p>
      <h2>{rich(L.get('title'))}</h2>
      <p class="sub">{rich(L.get('subtitle'))}</p>
      <ul class="leave-points">{points}</ul>
    </div>
    <form class="quote review-form reveal" id="reviewForm" novalidate>
      <h3>Leave a review</h3>
      <label>Your name<input name="rname" required autocomplete="name" placeholder="Jane D."></label>
      <fieldset class="rate"><legend>Your rating</legend>
        <div class="stars-in" role="radiogroup" aria-label="Rating">
          <input type="radio" id="r5" name="rating" value="5"><label for="r5" title="5 stars">★</label>
          <input type="radio" id="r4" name="rating" value="4"><label for="r4" title="4 stars">★</label>
          <input type="radio" id="r3" name="rating" value="3"><label for="r3" title="3 stars">★</label>
          <input type="radio" id="r2" name="rating" value="2"><label for="r2" title="2 stars">★</label>
          <input type="radio" id="r1" name="rating" value="1"><label for="r1" title="1 star">★</label>
        </div>
      </fieldset>
      <label>What did I help you with?
        <select name="rservice"><option>Book formatting &amp; typesetting</option><option>Proofreading</option><option>Copy editing</option><option>Cover design</option><option>Translation</option><option>Developmental editing</option><option>Several services</option></select>
      </label>
      <label>Your review<textarea name="rtext" rows="4" required placeholder="How did your project go?"></textarea></label>
      <label class="consent"><input type="checkbox" name="consent" required><span>I agree that my name and review can be shown on this website.</span></label>
      <p class="err" id="reviewErr" role="alert"></p>
      <div class="form-btns">
        <button type="submit" class="btn btn-gold" data-via="wa">Send review on WhatsApp</button>
        <button type="submit" class="btn btn-ghost" data-via="mail">Send by email</button>
      </div>
      <p class="review-ok" id="reviewOk" hidden>Thank you! Your review is ready to send. It will appear here once it's checked.</p>
    </form>
  </div>
</section>

<section class="section light" id="faq">
  <div class="wrap faq-grid">
    {section_head(H['faq_section'])}
    <div class="faq">{faq}</div>
  </div>
</section>

<section class="section dark contact" id="contact">
  <div class="wrap contact-grid">
    <div class="reveal">
      <p class="eyebrow">{e(C.get('eyebrow'))}</p>
      <h2 class="big">{rich(C.get('title'))}</h2>
      <p class="sub">{rich(C.get('subtitle'))}</p>
      {contact_rows()}
    </div>
    {quote_form()}
  </div>
</section>

<section class="final-cta" aria-label="Get started">
  <div class="wrap fc-inner reveal">
    <p class="eyebrow center">{e(FC.get('eyebrow'))}</p>
    <h2>{rich(FC.get('title'))}</h2>
    <p class="sub">{rich(FC.get('subtitle'))}</p>
    <div class="cta-row center">
      <a class="btn btn-gold" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a free consultation <span aria-hidden="true">→</span></a>
      <a class="btn btn-ghost" href="#contact">Get a quote</a>
      {f'<a class="btn btn-ghost" href="{e(S["fiverr"])}" target="_blank" rel="noopener">Order on Fiverr ↗</a>' if S.get('fiverr') else ''}
    </div>
    <p class="fc-note">{e(FC.get('note'))}</p>
  </div>
</section>
</main>

{ld(faq_ld)}{footer()}
{ICONS}
{floating()}
<div class="proof" id="proof" role="status" aria-live="polite">
  <span class="proof-av" id="proofAv">A</span>
  <div class="proof-body">
    <p class="proof-stars">★★★★★ <span>5-star review · Fiverr</span></p>
    <p class="proof-quote" id="proofQuote"></p>
    <p class="proof-name" id="proofName"></p>
  </div>
  <button class="proof-x" id="proofX" aria-label="Close review pop-up">×</button>
</div>

<a class="sticky-call" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a free consultation <span aria-hidden="true">→</span></a>

<div class="viewer" id="viewer" role="dialog" aria-modal="true" aria-labelledby="vTitle" hidden>
  <div class="v-top">
    <div><p class="eyebrow" id="vKicker"></p><h3 id="vTitle"></h3></div>
    <div class="v-actions"><a class="btn btn-gold btn-sm" id="vPdf" download>Download PDF</a><button class="v-close" id="vClose" aria-label="Close">✕</button></div>
  </div>
  <div class="v-stage">
    <button class="v-nav prev" id="vPrev" aria-label="Previous slide">‹</button>
    <div class="v-frame" id="vImg" role="img"></div>
    <button class="v-nav next" id="vNext" aria-label="Next slide">›</button>
  </div>
  <p class="v-count" id="vCount"></p>
</div>

{site_data()}<script src="main.js?v={VER}"></script>
</body>
</html>
'''


# ------------------------------------------------------------------ service pages
def project_card(pid):
    w = next((x for x in WORK if x['id'] == pid), None)
    if not w:
        return ''
    collab = '<span class="badge">Collaboration</span>' if w.get('collaboration') else ''
    return (f'<a class="card reveal" href="{e(asset(w.get("pdf")))}" target="_blank" rel="noopener">'
            f'<span class="thumb">{collab}<img src="{e(asset(w.get("thumbnail")))}" alt="{e(w["title"])} case study" loading="lazy"></span>'
            f'<span class="meta"><span class="k">{e(w.get("category"))}</span><h3>{e(w["title"])}</h3><p>{e(w.get("description"))} · <span class="pdf-inline">Open case study PDF ↗</span></p></span></a>')


def visual(v):
    imgs = [asset(x) for x in items_ok(v.get('images'))]
    style, alt = v.get('style', 'page'), v.get('alt', '')
    if not imgs:
        return ''
    if style in ('page', 'photo'):
        return f'<figure class="sv-visual sv-{style} reveal"><img src="{e(imgs[0])}" alt="{e(alt)}" fetchpriority="high"></figure>'
    tags = ''.join(f'<img src="{e(x)}" alt="" loading="eager">' for x in imgs[:3])
    return f'<figure class="sv-visual sv-covers n{min(len(imgs), 3)} reveal" role="img" aria-label="{e(alt)}">{tags}</figure>'


def service_page(p):
    url = f'{URL}/{p["slug"]}'
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', 'name': plain(p['eyebrow']).split(' · ')[0], 'serviceType': p['service'], 'description': p['seo_description'], 'url': url,
         'provider': {'@type': 'Person', '@id': f'{URL}/#khadijat', 'name': S['name'], 'url': f'{URL}/'}, 'areaServed': 'Worldwide'},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{URL}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Services', 'item': f'{URL}/#services'},
            {'@type': 'ListItem', 'position': 3, 'name': p['menu_name'], 'item': url}]},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q['question'], 'acceptedAnswer': {'@type': 'Answer', 'text': q['answer']}} for q in p.get('faq', [])]}]}
    offers = ''.join(f'<article class="svc reveal"><span class="svc-num">{i + 1:02d}</span><h3>{e(o["title"])}</h3><p>{e(o.get("text"))}</p></article>' for i, o in enumerate(p.get('offers', [])))
    why = ''.join(f'<div class="why reveal"><h3>{e(o["title"])}</h3><p>{e(o.get("text"))}</p></div>' for o in p.get('why', []))
    checks = ''.join(f'<div class="checks reveal"><h3>{e(c["title"])}</h3><ul>' + ''.join(f'<li>{e(x)}</li>' for x in items_ok(c.get('items'))) + '</ul></div>' for c in p.get('checks', []))
    steps = ''.join(f'<li class="reveal"><span>{i + 1}</span><h3>{e(s["title"])}</h3><p>{e(s.get("text"))}</p></li>' for i, s in enumerate(SP.get('steps', [])))
    who = ''.join(f'<li>{e(x)}</li>' for x in items_ok(p.get('who')))
    faq = ''.join(f'<details class="reveal"><summary>{e(q["question"])}</summary><p>{e(q["answer"])}</p></details>' for q in p.get('faq', []))
    others = ''.join(f'<a href="{e(s)}.html">{e(n)}</a>' for s, n in SERVICE_LINKS if s != p['slug'])
    cards = ''.join(project_card(x) for x in items_ok(p.get('projects')))
    if cards:
        proj = (f'<section class="section light" id="projects"><div class="wrap"><div class="section-head reveal"><p class="eyebrow">Selected projects</p>'
                f'<h2>Real books, <em>real work</em>.</h2><p class="sub">Open any project to see the full case study.</p></div>'
                f'<div class="grid">{cards}</div><p class="rv-more reveal dark-link"><a href="./#work">See my full portfolio →</a></p></div></section>')
    else:
        proj = ('<section class="section light sv-port"><div class="wrap sv-port-in reveal"><p class="eyebrow">Portfolio</p>'
                '<h2>See the books I\'ve <em>worked on</em>.</h2><p class="sub">Formatting, covers and full publishing projects across many genres.</p>'
                '<div class="cta-row"><a class="btn btn-gold" href="./#work">View my portfolio →</a></div></div></section>')
    return head(p['seo_title'], p['seo_description'], url, ld(graph)) + f'''
<body class="sv-page-body">
<header class="nav">
  {brand(False)}
  <nav class="links" id="navlinks">
    <a href="./">Home</a><a href="./#services">Services</a><a href="./#work">Work</a><a href="./#about">About</a><a href="./#reviews">Reviews</a>
    <a class="btn btn-ghost btn-sm" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a call</a>
    <a class="btn btn-gold btn-sm" href="#quote">Get a quote</a>
  </nav>
  <button class="menu" id="menuBtn" aria-label="Open menu" aria-expanded="false"><span></span><span></span></button>
</header>
<main>
<section class="sv-hero">
  <div class="wrap sv-hero-grid">
    <div>
      <nav class="crumbs reveal" aria-label="Breadcrumb"><a href="./">Home</a><span>/</span><a href="./#services">Services</a><span>/</span><b>{e(p['menu_name'])}</b></nav>
      <p class="eyebrow reveal">{e(p['eyebrow'])}</p>
      <h1 class="reveal">{rich(p['title'])}</h1>
      <p class="lead reveal">{rich(p.get('lead'))}</p>
      <div class="cta-row reveal"><a class="btn btn-gold" href="#quote">Request a quote <span aria-hidden="true">→</span></a><a class="btn btn-ghost" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a free call</a></div>
      <ul class="hero-proof reveal">{''.join(f'<li>{rich(x).replace("★★★★★", "<span class=\"stars\">★★★★★</span>")}</li>' for x in items_ok(HOME['hero'].get('proof'))[:2])}<li>Worldwide</li></ul>
    </div>
    {visual(p.get('visual', {}))}
  </div>
</section>
<section class="section light"><div class="wrap"><div class="section-head reveal"><p class="eyebrow">What I offer</p><h2>{rich(p.get('offers_title'))}</h2><p class="sub">{rich(p.get('offers_subtitle'))}</p></div><div class="services">{offers}</div></div></section>
<section class="section dark"><div class="wrap"><div class="section-head reveal"><p class="eyebrow">Quality</p><h2>{rich(p.get('why_title'))}</h2></div><div class="why-grid">{why}</div></div></section>
<section class="section light"><div class="wrap"><div class="section-head reveal"><p class="eyebrow">The details</p><h2>{rich(p.get('checks_title'))}</h2></div><div class="checks-grid">{checks}</div></div></section>
<section class="section dark"><div class="wrap"><div class="section-head reveal"><p class="eyebrow">How it works</p><h2>Simple, clear <em>and</em> stress-free.</h2></div><ol class="steps steps-dark">{steps}</ol></div></section>
{proj}
<section class="section dark"><div class="wrap who-grid"><div class="section-head reveal"><p class="eyebrow">Is this you?</p><h2>Who this service is <em>for</em></h2></div><ul class="who reveal">{who}</ul></div></section>
<section class="section light" id="faq"><div class="wrap faq-grid"><div class="section-head reveal"><p class="eyebrow">Questions</p><h2>Frequently asked <em>questions</em></h2><p class="sub">Something else on your mind? <a href="#quote">Send me a message.</a></p></div><div class="faq">{faq}</div></div></section>
<section class="section dark contact" id="quote">
  <div class="wrap contact-grid">
    <div class="reveal">
      <p class="eyebrow">Get started</p>
      <h2 class="big">Ready to <em>begin?</em></h2>
      <p class="sub">Tell me about your book and I'll reply with the scope, files, timeline and quote. Free consultation, no commitment.</p>
      {contact_rows()}
      <p class="channels-label">Other services</p>
      <p class="other-svcs">{others}</p>
    </div>
    {quote_form(p.get('form_service'))}
  </div>
</section>
</main>
{footer('./')}
{ICONS}
{floating()}
<a class="sticky-call" href="{e(S['calendly'])}" target="_blank" rel="noopener">Book a free consultation <span aria-hidden="true">→</span></a>
{site_data()}<script src="sub.js?v={VER}"></script>
</body>
</html>
'''


def sitemap():
    today = datetime.date.today().isoformat()
    urls = [('', '1.0')] + [(p['slug'], '0.8') for p in PAGES] + [('privacy', '0.3'), ('terms', '0.3')]
    rows = ''.join(f'  <url><loc>{URL}/{u}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>\n' for u, pr in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n'


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name in STATIC:
        src = os.path.join(ROOT, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(OUT, name))
        elif os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, name))
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(home())
    for p in PAGES:
        with open(os.path.join(OUT, p['slug'] + '.html'), 'w', encoding='utf-8') as f:
            f.write(service_page(p))
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap())
    if not os.environ.get('VERCEL'):   # local preview only: lets the dashboard show data without signing in
        shutil.copytree(os.path.join(ROOT, 'content'), os.path.join(OUT, 'admin', 'dev-content'), ignore=shutil.ignore_patterns('*.bak'))
    print(f'built {OUT}: home + {len(PAGES)} service pages, {len(WORK)} portfolio items, {len(REV.get("reviews", []))} reviews')


if __name__ == '__main__':
    main()
