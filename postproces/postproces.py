#!/usr/bin/env python3
"""Observatori Lingüístic: post-procés de la web generada per build.py.

S'executa sobre la carpeta de la web ja generada (la del repositori
observatori-linguistic-website) i és idempotent: es pot tornar a passar.

    python3 postproces.py <carpeta-de-la-web>

Què fa:
  1. SEO: canonical, hreflang (ca, es, x-default), Open Graph i Twitter, dades
     estructurades (Dataset, WebSite, BreadcrumbList), títols i descripcions
     útils per a comarques, municipis i districtes, sitemap.xml i robots.txt.
  2. Treu de l'HTML les variants grans del filtre de tipus de centre (concertats,
     privats i combinacions) i les desa en fitxers v-<abast>.json al costat de
     cada pàgina; static/pp.js les carrega quan algú canvia el filtre.
  3. Crea una pàgina per a cada centre analitzat, a <municipi>/<nom-del-centre>/.
  4. Peu: autoria discreta, contacte (GitHub i correu sense l'adreça a l'HTML) i
     privacitat. Pàgina de privacitat en català i castellà.
  5. Petites millores d'usabilitat (pp.css): mides de lletra, zones tàctils,
     subnavegació al mòbil, aclariment de quins centres compten a cada secció.

Sense dependències fora de la biblioteca estàndard.
"""
import base64
import hashlib
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from urllib.parse import quote

BASE = "https://observatorilinguistic.com"
REPO = "https://github.com/Observatori-Linguistic/observatori-linguistic-website"
REPO_ANTIC = "https://github.com/Observatori-Linguistic/observatori-linguistic-frontend"
REPO_DOCS = "https://github.com/Observatori-Linguistic/observatori-linguistic-documents"
CORREU_USUARI = "joanbanyes"          # el domini (gmail.com) el posa pp.js
MARCA = "<!--pp-->"                   # pàgina ja processada
LLINDAR_VARIANT = 2000                # bytes: les variants més petites es queden a l'HTML
AQUI = os.path.dirname(os.path.abspath(__file__))

NOM = {"ca": "Observatori Lingüístic", "es": "Observatori Lingüístic"}  # el nom no es tradueix
PRIV = {"ca": "privacitat", "es": "privacidad"}
COM = {"ca": "comarques", "es": "comarcas"}
LOCALE = {"ca": "ca_ES", "es": "es_ES"}

TXT = {
    "ca": {
        "pare": 'Anàlisi transparent i de codi obert: els documents, les dades i el codi són públics a <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>, perquè qualsevol persona ho pugui comprovar.',
        "error": 'Has vist una dada errònia? <a href="{issues}" rel="noopener" target="_blank">Explica-ho a GitHub</a> o <button type="button" class="pp-lnk" data-pp-m="{m}">escriu un correu</button>.',
        "priv": '<a href="{priv}">Privacitat</a>',
        "fx_err": "Hi ha alguna cosa que no és correcta en aquesta fitxa?",
        "tornar": "← Tots els centres de {lloc}",
        "eb_centre": "Centre educatiu",
        "lead_centre": "Quin paper dona a cada llengua, curs a curs, el projecte lingüístic que publica el centre. És el que diu el document, no el que s'observa a l'aula: <a href=\"{met}\">com ho mesurem</a>.",
        "nota_centre": "Les dades surten del document del centre, no de l'aula. Com es llegeixen: <a href=\"{met}\">Com ho mesurem</a>.",
        "t_centre": "{nom}, {lloc}: projecte lingüístic · Observatori Lingüístic Escolar",
        "d_centre": "{nom} ({lloc}), projecte lingüístic curs a curs. {resum}",
        "t_mun": "{nom}: projecte lingüístic de cada escola i institut · Observatori Lingüístic Escolar",
        "d_mun": "Quin paper té el català, el castellà i l'anglès a cada curs, de P3 a batxillerat, a les escoles i instituts de {nom} ({pare}), segons el seu projecte lingüístic. {xif}.",
        "d_mun0": "Escoles i instituts de {nom} ({pare}) i si publiquen el seu projecte lingüístic: quin paper hi té cada llengua, curs a curs. {n} centres.",
        "t_com": "{nom}: les llengües a les escoles i instituts, curs a curs · Observatori Lingüístic Escolar",
        "d_com": "{nom}: quin paper té el català, el castellà i l'anglès a cada curs, de P3 a batxillerat, a les escoles i instituts de la comarca, segons el seu projecte lingüístic. {xif}.",
        "ab_seg": "segons el que diuen els seus documents",
        "xif_pub": "{a} de {n} centres públics analitzats ({at} de {nt} amb concertats i privats)",
        "xif_tot": "{at} de {nt} centres analitzats",
        "cites": None,
        "dataset_desc": "Paper de cada llengua (català, castellà, anglès i altres) curs a curs, de P3 a 2n de batxillerat, a les escoles i instituts de Catalunya, segons el projecte lingüístic que publica cada centre. Cada dada va amb la cita literal del document i l'enllaç a l'original. Inclou centres públics, concertats i privats del directori del Departament d'Educació.",
        "priv_t": "Privacitat",
        "priv_lead": "Què passa amb les teves dades quan visites aquesta web.",
        "inici": "Inici",
        "com_t": "Comarques i municipis",
        "com_lead": "Totes les comarques de Catalunya amb les xifres dels seus centres, i la llista de tots els municipis i districtes per arribar a cada centre.",
        "com_desc": "Les 43 comarques de Catalunya i tots els seus municipis: quin paper té el català, el castellà i l'anglès a les escoles i instituts, segons el projecte lingüístic de cada centre.",
        "mun_t": "Tots els municipis",
        "mun_p": "Ordenats per comarca. Cada municipi porta a les fitxes dels seus centres.",
        "mapa": "Mapa del web",
        "metodo": "Com ho mesurem",
        "priv_c": "Privacitat",
    },
    "es": {
        "pare": 'Análisis transparente y de código abierto: los documentos, los datos y el código son públicos en <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>, para que cualquier persona pueda comprobarlo.',
        "error": '¿Has visto un dato erróneo? <a href="{issues}" rel="noopener" target="_blank">Cuéntalo en GitHub</a> o <button type="button" class="pp-lnk" data-pp-m="{m}">escribe un correo</button>.',
        "priv": '<a href="{priv}">Privacidad</a>',
        "fx_err": "¿Hay algo que no es correcto en esta ficha?",
        "tornar": "← Todos los centros de {lloc}",
        "eb_centre": "Centro educativo",
        "lead_centre": "Qué papel da a cada lengua, curso a curso, el proyecto lingüístico que publica el centro. Es lo que dice el documento, no lo que se observa en el aula: <a href=\"{met}\">cómo lo medimos</a>.",
        "nota_centre": "Los datos salen del documento del centro, no del aula. Cómo se leen: <a href=\"{met}\">Cómo lo medimos</a>.",
        "t_centre": "{nom}, {lloc}: proyecto lingüístico · Observatorio Lingüístico Escolar",
        "d_centre": "{nom} ({lloc}), proyecto lingüístico curso a curso. {resum}",
        "t_mun": "{nom}: proyecto lingüístico de cada escuela e instituto · Observatorio Lingüístico Escolar",
        "d_mun": "Qué papel tienen el catalán, el castellano y el inglés en cada curso, de P3 a bachillerato, en las escuelas e institutos de {nom} ({pare}), según su proyecto lingüístico. {xif}.",
        "d_mun0": "Escuelas e institutos de {nom} ({pare}) y si publican su proyecto lingüístico: qué papel tiene cada lengua, curso a curso. {n} centros.",
        "t_com": "{nom}: las lenguas en las escuelas e institutos, curso a curso · Observatorio Lingüístico Escolar",
        "d_com": "{nom}: qué papel tienen el catalán, el castellano y el inglés en cada curso, de P3 a bachillerato, en las escuelas e institutos de la comarca, según su proyecto lingüístico. {xif}.",
        "ab_seg": "según lo que dicen sus documentos",
        "xif_pub": "{a} de {n} centros públicos analizados ({at} de {nt} con concertados y privados)",
        "xif_tot": "{at} de {nt} centros analizados",
        "cites": ("Ver las citas del documento</summary>", "Ver las citas del documento (en su idioma original)</summary>"),
        "dataset_desc": "Papel de cada lengua (catalán, castellano, inglés y otras) curso a curso, de P3 a 2.º de bachillerato, en las escuelas e institutos de Cataluña, según el proyecto lingüístico que publica cada centro. Cada dato va con la cita literal del documento y el enlace al original. Incluye centros públicos, concertados y privados del directorio del Departament d'Educació.",
        "priv_t": "Privacidad",
        "priv_lead": "Qué pasa con tus datos cuando visitas esta web.",
        "inici": "Inicio",
        "com_t": "Comarcas y municipios",
        "com_lead": "Todas las comarcas de Cataluña con las cifras de sus centros, y la lista de todos los municipios y distritos para llegar a cada centro.",
        "com_desc": "Las 43 comarcas de Cataluña y todos sus municipios: qué papel tienen el catalán, el castellano y el inglés en las escuelas e institutos, según el proyecto lingüístico de cada centro.",
        "mun_t": "Todos los municipios",
        "mun_p": "Ordenados por comarca. Cada municipio lleva a las fichas de sus centros.",
        "mapa": "Mapa de la web",
        "metodo": "Cómo lo medimos",
        "priv_c": "Privacidad",
    },
}

PRIV_COS = {
    "ca": """<section id="qui"><h2>Qui fa aquesta web</h2><p>És un projecte independent i de codi obert d'anàlisi de dades, fet amb la documentació pública dels centres educatius. Els documents, les dades i el codi són públics a <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>. No està vinculat a cap administració, centre, partit ni organització, i no té ànim de lucre.</p><p>Per a qualsevol qüestió sobre aquesta pàgina o sobre les teves dades, pots <a href="{issues}" rel="noopener" target="_blank">obrir una incidència a GitHub</a> o <button type="button" class="pp-lnk" data-pp-m="{m}">escriure un correu</button>.</p></section>
<section id="dades"><h2>Quines dades es recullen</h2><p>Per fer servir la web no cal registrar-se ni donar cap dada. La web no té formularis ni comptes d'usuari.</p><p>El navegador desa, només al teu dispositiu, l'idioma triat i el filtre de tipus de centre. Aquesta informació no s'envia enlloc.</p></section>
<section id="estadistiques"><h2>Estadístiques de visites, sense galetes</h2><p>Per saber quantes persones fan servir la web i quines pàgines miren, fem servir Cloudflare Web Analytics. No instal·la galetes, no desa res al teu dispositiu i no identifica ningú: només dona xifres agregades (visites, pàgines, país, tipus de dispositiu i d'on arriba la visita). Per això no veuràs cap avís de galetes.</p><p>Si no vols que es compti la teva visita, pots bloquejar el domini <code>static.cloudflareinsights.com</code> al navegador o amb un bloquejador de continguts; la web funciona igual.</p><p>La web no fa servir Google Analytics ni cap eina de publicitat.</p></section>
<section id="allotjament"><h2>Allotjament</h2><p>La web s'allotja a Cloudflare Pages. Com qualsevol servidor web, Cloudflare tracta l'adreça IP de les visites per servir les pàgines i protegir-les d'atacs.</p></section>
<section id="drets"><h2>Els teus drets</h2><p>Pots demanar accedir a les teves dades, rectificar-les o suprimir-les escrivint per les vies de dalt. També pots presentar una reclamació a l'Agència Espanyola de Protecció de Dades (aepd.es).</p></section>""",
    "es": """<section id="qui"><h2>Quién hace esta web</h2><p>Es un proyecto independiente y de código abierto de análisis de datos, hecho con la documentación pública de los centros educativos. Los documentos, los datos y el código son públicos en <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>. No está vinculado a ninguna administración, centro, partido ni organización, y no tiene ánimo de lucro.</p><p>Para cualquier cuestión sobre esta página o sobre tus datos, puedes <a href="{issues}" rel="noopener" target="_blank">abrir una incidencia en GitHub</a> o <button type="button" class="pp-lnk" data-pp-m="{m}">escribir un correo</button>.</p></section>
<section id="dades"><h2>Qué datos se recogen</h2><p>Para usar la web no hace falta registrarse ni dar ningún dato. La web no tiene formularios ni cuentas de usuario.</p><p>El navegador guarda, solo en tu dispositivo, el idioma elegido y el filtro de tipo de centro. Esta información no se envía a ningún sitio.</p></section>
<section id="estadistiques"><h2>Estadísticas de visitas, sin cookies</h2><p>Para saber cuántas personas usan la web y qué páginas miran, usamos Cloudflare Web Analytics. No instala cookies, no guarda nada en tu dispositivo y no identifica a nadie: solo da cifras agregadas (visitas, páginas, país, tipo de dispositivo y de dónde llega la visita). Por eso no verás ningún aviso de cookies.</p><p>Si no quieres que se cuente tu visita, puedes bloquear el dominio <code>static.cloudflareinsights.com</code> en el navegador o con un bloqueador de contenidos; la web funciona igual.</p><p>La web no usa Google Analytics ni ninguna herramienta de publicidad.</p></section>
<section id="allotjament"><h2>Alojamiento</h2><p>La web se aloja en Cloudflare Pages. Como cualquier servidor web, Cloudflare trata la dirección IP de las visitas para servir las páginas y protegerlas de ataques.</p></section>
<section id="drets"><h2>Tus derechos</h2><p>Puedes pedir acceder a tus datos, rectificarlos o suprimirlos escribiendo por las vías de arriba. También puedes presentar una reclamación ante la Agencia Española de Protección de Datos (aepd.es).</p></section>""",
}

# ------------------------------------------------------------------ utilitats


def llegeix(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def escriu(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def slug(s):
    s = unicodedata.normalize("NFKD", html.unescape(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80].strip("-") or "centre"


def text(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def attr(s):
    return html.escape(s, quote=True)


def retalla(s, n=300):
    if len(s) <= n:
        return s
    s = s[:n].rsplit(" ", 1)[0].rstrip(",;:·")
    return s + "…"


VOID = {"br", "img", "meta", "link", "input", "hr", "wbr", "source", "area", "col", "embed", "param", "track"}
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>|<!--.*?-->", re.S)


def element(s, inici):
    """Final (exclusiu) de l'element que comença a s[inici]."""
    prof = 0
    for m in TAG.finditer(s, inici):
        if m.group(0).startswith("<!--"):
            continue
        tanca, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or attrs.rstrip().endswith("/"):
            continue
        prof += -1 if tanca else 1
        if prof == 0:
            return m.end()
    raise ValueError("element sense tancar")


def blocs_v(s):
    """Elements més externs amb la classe «v»: (inici, final, tag, classes, inici_interior, final_interior)."""
    pila, out, dins = [], [], 0
    for m in TAG.finditer(s):
        if m.group(0).startswith("<!--"):
            continue
        tanca, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if not tanca:
            if tag in VOID or attrs.rstrip().endswith("/"):
                continue
            cm = re.search(r'\bclass="([^"]*)"', attrs)
            cls = cm.group(1).split() if cm else []
            es_v = "v" in cls
            pila.append((tag, m.start(), m.end(), cls, es_v))
            if es_v:
                dins += 1
        else:
            t = None
            while pila:
                t, st, ie, cls, es_v = pila.pop()
                if es_v:
                    dins -= 1
                if t == tag:
                    break
            if t == tag and es_v and dins == 0:
                out.append((st, m.end(), tag, cls, ie, m.start()))
    return out


def idioma_a(s, rel_ca, rel_es):
    """Els enllaços CA/ES de la capçalera apunten a la mateixa pàgina en l'altre idioma."""
    def f(m):
        d = m.group(0)
        d = re.sub(r'href="((?:\.\./)*)ca/[^"]*"', lambda x: f'href="{x.group(1)}{rel_ca}"', d)
        d = re.sub(r'href="((?:\.\./)*)es/[^"]*"', lambda x: f'href="{x.group(1)}{rel_es}"', d)
        return d
    return re.sub(r'<div class="idioma".*?</div>', f, s, count=1, flags=re.S)


def rel_un_nivell_mes(s):
    """Afegeix «../» als enllaços relatius (per a contingut mogut un nivell més avall)."""
    def f(m):
        url = m.group(2)
        if re.match(r"^(#|/|[a-zA-Z][a-zA-Z0-9+.-]*:|//)", url) or url == "":
            return m.group(0)
        return m.group(1) + "../" + url + m.group(3)
    return re.sub(r'(\b(?:href|src)=")([^"]*)(")', f, s)


def url_de(rel):
    """«ca/maresme/» -> https://.../ca/maresme/"""
    return BASE + "/" + rel


# ------------------------------------------------------------------ pàgines


class Pagina:
    def __init__(self, arrel, rel):
        self.arrel = arrel
        self.rel = rel                      # «ca/maresme/mataro/» (sense index.html)
        self.cami = os.path.join(arrel, rel, "index.html")
        # el repositori de la web es va moure (enllaços i text visible)
        self.s = llegeix(self.cami).replace(REPO_ANTIC, REPO).replace(REPO_ANTIC[8:], REPO[8:])
        self.lang = rel.split("/")[0]

    @property
    def parts(self):
        return [p for p in self.rel.split("/")[1:] if p]

    def desa(self):
        escriu(self.cami, self.s)


def molles(s):
    m = re.search(r'<nav class="molles"[^>]*>.*?</nav>', s, re.S)
    if not m:
        return []
    out = []
    for a in re.finditer(r'<a href="([^"]*)">(.*?)</a>|<span aria-current="page">(.*?)</span>', m.group(0), re.S):
        if a.group(1) is not None:
            out.append((text(a.group(2)), a.group(1)))
        else:
            out.append((text(a.group(3)), None))
    return out


def absolut(rel_pagina, href):
    """URL absoluta d'un href relatiu dins de rel_pagina."""
    parts = [p for p in rel_pagina.split("/") if p]
    h = href.split("#")[0]
    for seg in h.split("/"):
        if seg == "..":
            parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return BASE + "/" + "/".join(parts) + ("/" if parts else "")


# ------------------------------------------------------------------ 1. pàgines de centre


def resum_centre(card):
    files = re.findall(r'<div class="cl-f" role="listitem" aria-label="([^"]+)"', card)
    trossos = []
    for f in files:
        f = html.unescape(f).rstrip(".")
        if ". " in f:
            llengua, resta = f.split(". ", 1)
            resta = re.sub(r"(: )(\w)", lambda m: m.group(1) + m.group(2).lower(), resta)
            f = f"{llengua} ({resta})"
        trossos.append(f)
    return "; ".join(trossos) + "."


def card_amb_error(card, lang, codi, nom, lloc, url_fitxa):
    titol = f"[{codi}] {nom} ({lloc})"
    if lang == "ca":
        cos = f"Fitxa: {url_fitxa}\n\nQuè no és correcte:\n\n\nOn ho diu el document (pàgina o frase), si ho saps:\n"
    else:
        cos = f"Ficha: {url_fitxa}\n\nQué no es correcto:\n\n\nDónde lo dice el documento (página o frase), si lo sabes:\n"
    href = f"{REPO}/issues/new?title={quote(titol)}&body={quote(cos)}"
    p = f'<p class="fx-err"><a href="{attr(href)}" rel="noopener nofollow" target="_blank">{TXT[lang]["fx_err"]}</a></p>'
    return card[: card.rfind("</article>")] + p + "</article>"


def pagines_de_centre(arrel, pagines):
    """Crea <lloc>/<slug>/index.html per a cada fitxa. Torna {rel_ca: rel_es} de les noves."""
    noves = {}
    slugs = {}          # codi -> rel relatiu dins del lloc
    # primer el català: decideix els noms de carpeta
    per_lang = {"ca": [], "es": []}
    for p in pagines:
        if '<article class="fx' in p.s and not p.s.count('data-pp-centre'):
            per_lang[p.lang].append(p)
    for lang in ("ca", "es"):
        for p in per_lang[lang]:
            dir_pag = os.path.join(arrel, p.rel)
            existents = {d for d in os.listdir(dir_pag) if os.path.isdir(os.path.join(dir_pag, d))}
            usats = set()
            mol = molles(p.s)
            lloc = mol[-1][0] if mol else ""
            for m in re.finditer(r'<article class="fx[^"]*" id="c-(\w+)">', p.s):
                codi = m.group(1)
                ini = m.start()
                fi = element(p.s, ini)
                card = p.s[ini:fi]
                nom = text(re.search(r"<h3>(.*?)</h3>", card, re.S).group(1))
                clau = (p.rel.split("/", 1)[1], codi)
                if lang == "ca" or clau not in slugs:
                    sl = slug(nom)
                    if sl in usats or (sl in existents and not os.path.exists(os.path.join(dir_pag, sl, ".pp-centre"))):
                        sl = f"{sl}-{codi}"
                    if sl in usats:
                        sl = codi
                    slugs[clau] = sl
                sl = slugs[clau]
                usats.add(sl)
                rel_c = f"{p.rel}{sl}/"
                crea_pagina_centre(arrel, p, rel_c, card, codi, nom, lloc, mol)
                if lang == "ca":
                    noves[rel_c] = "es/" + rel_c.split("/", 1)[1]
    return slugs, noves


def crea_pagina_centre(arrel, p, rel_c, card, codi, nom, lloc, mol):
    lang = p.lang
    t = TXT[lang]
    s = p.s
    head = s[: s.find("</head>")]
    m_top = re.search(r'<header class="top">.*?</header>', s, re.S)
    top = m_top.group(0)
    peu_ini = s.find('<footer class="peu"')
    peu = s[peu_ini: s.find("</body>")]
    m_main = re.search(r'<main id="main"([^>]*)>', s)
    main_attrs = m_main.group(1)
    m_pl = re.search(r'<div class="pl"[^>]*>', s)
    i_lgd = s.find('<div class="lgd-f">')
    lgd = s[i_lgd:element(s, i_lgd)] if i_lgd != -1 else ""
    # la fitxa, sempre visible i sense dependre del filtre
    card = re.sub(r'^<article class="[^"]*"', lambda m: '<article class="fx"', card, count=1)
    url_c = url_de(rel_c)
    card = card_amb_error(card, lang, codi, nom, lloc, url_c)
    card = re.sub(r"<h3>.*?</h3>", "", card, count=1, flags=re.S)      # el nom ja és l'h1 de la pàgina
    # molles: l'últim element passa a ser enllaç al lloc
    parts = []
    for nm, href in mol:
        if href is None:
            parts.append(f'<a href="../">{html.escape(nm)}</a>')
        else:
            parts.append(f'<a href="../{href}">{html.escape(nm)}</a>')
    parts.append(f'<span aria-current="page">{html.escape(nom)}</span>')
    nav = '<nav class="molles" aria-label="breadcrumb">' + '<span class="sep" aria-hidden="true">/</span>'.join(parts) + "</nav>"
    arrel_rel = re.search(r'data-arrel="([^"]*)"', main_attrs).group(1)
    met = "../" + arrel_rel + lang + "/metodologia/"
    attrs_nou = main_attrs.replace('data-arrel="' + arrel_rel + '"', 'data-arrel="../' + arrel_rel + '"')
    cos = (
        f'<main id="main"{attrs_nou} data-pp-centre="{codi}">'
        + (m_pl.group(0) if m_pl else "<div>")
        + '<div class="wrap pp-centre">'
        + nav
        + f'<header class="ph-s"><p class="eb">{html.escape(t["eb_centre"].format(lloc=lloc))}</p><h1>{html.escape(nom)}</h1>'
        + f'<p class="lead">{t["lead_centre"].format(met=met)}</p></header>'
        + '<section class="sec" id="centres">'
        + rel_un_nivell_mes(lgd)
        + '<div class="fxs">' + rel_un_nivell_mes(card) + "</div>"
        + f'<p class="pp-tornar"><a href="../">{html.escape(t["tornar"].format(lloc=lloc))}</a></p>'
        + "</section></div></div></main>"
    )
    title = t["t_centre"].format(nom=nom, lloc=lloc)
    desc = retalla(t["d_centre"].format(nom=nom, lloc=lloc, resum=resum_centre(card)), 300)
    head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(desc)}">', head)
    head = rel_un_nivell_mes(head)
    out = head + "</head>\n<body>\n" + rel_un_nivell_mes(s[s.find("<body>") + 6: m_top.start()]) \
        + rel_un_nivell_mes(top) + cos + rel_un_nivell_mes(peu) + "</body>\n</html>\n"
    resta = rel_c.split("/", 1)[1]
    out = idioma_a(out, "ca/" + resta, "es/" + resta)
    escriu(os.path.join(arrel, rel_c, "index.html"), out)
    escriu(os.path.join(arrel, rel_c, ".pp-centre"), codi + "\n")


def enllaca_fitxes(p, slugs):
    """A la pàgina del municipi: el nom de cada fitxa enllaça a la seva pàgina, i avís d'error."""
    clau_lloc = p.rel.split("/", 1)[1]
    mol = molles(p.s)
    lloc = mol[-1][0] if mol else ""

    out, pos = [], 0
    for m in re.finditer(r'<article class="fx[^"]*" id="c-(\w+)">', p.s):
        codi = m.group(1)
        sl = slugs.get((clau_lloc, codi))
        if not sl:
            continue
        ini = m.start()
        fi = element(p.s, ini)
        card = p.s[ini:fi]
        nom = text(re.search(r"<h3>(.*?)</h3>", card, re.S).group(1))
        card = re.sub(r"<h3>(.*?)</h3>", lambda h: f'<h3><a href="{sl}/">{h.group(1)}</a></h3>', card, count=1)
        card = card_amb_error(card, p.lang, codi, nom, lloc, url_de(f"{p.rel}{sl}/"))
        out.append(p.s[pos:ini])
        out.append(card)
        pos = fi
    out.append(p.s[pos:])
    p.s = "".join(out)


# ------------------------------------------------------------------ 2. variants a demanda


def treu_variants(p):
    blocs = blocs_v(p.s)
    grans = [b for b in blocs
             if "v-pub" not in b[3] and b[2] in ("div", "section", "ul", "ol", "table")
             and b[1] - b[0] > LLINDAR_VARIANT and 'class="fx' not in p.s[b[0]:b[1]]]
    if not grans:
        return 0
    fitxers = {}
    out, pos = [], 0
    for i, (st, en, tag, cls, ie, ii) in enumerate(grans):
        obre = p.s[st:ie]
        interior = p.s[ie:ii]
        for c in cls:
            if c.startswith("v-"):
                fitxers.setdefault(c[2:], {})[str(i)] = interior
        out.append(p.s[pos:st])
        out.append(obre[:-1] + f' data-vl="{i}">' + p.s[ii:en])
        pos = en
    out.append(p.s[pos:])
    p.s = "".join(out)
    d = os.path.dirname(p.cami)
    for ab, contingut in fitxers.items():
        escriu(os.path.join(d, f"v-{ab}.json"), json.dumps(contingut, ensure_ascii=False, separators=(",", ":")))
    p.s = re.sub(r'(<main id="main"[^>]*?)>', lambda m: m.group(1) + f' data-vp="{p.rel}">', p.s, count=1)
    return len(grans)


# ------------------------------------------------------------------ 3. capçalera: SEO, OG, JSON-LD


def alternates(rel_ca, rel_es, xdef):
    return (
        f'<link rel="alternate" hreflang="ca" href="{url_de(rel_ca)}">'
        f'<link rel="alternate" hreflang="es" href="{url_de(rel_es)}">'
        f'<link rel="alternate" hreflang="x-default" href="{url_de(xdef)}">'
    )


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def dataset(lang, data):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": BASE + "/#web", "url": BASE + "/", "name": NOM[lang],
             "inLanguage": ["ca", "es"]},
            {"@type": "Dataset", "name": NOM[lang] + (": projectes lingüístics dels centres educatius de Catalunya" if lang == "ca"
                                                      else ": proyectos lingüísticos de los centros educativos de Cataluña"),
             "description": TXT[lang]["dataset_desc"], "url": url_de(f"{lang}/"),
             "inLanguage": lang, "isAccessibleForFree": True,
             "license": "https://creativecommons.org/licenses/by/4.0/",
             "creator": {"@type": "Organization", "name": NOM[lang], "url": BASE + "/"},
             "spatialCoverage": {"@type": "Place", "name": "Catalunya" if lang == "ca" else "Cataluña"},
             "temporalCoverage": "2026", "dateModified": data,
             "keywords": (["projecte lingüístic", "escoles", "instituts", "català", "castellà", "anglès", "Catalunya"] if lang == "ca"
                          else ["proyecto lingüístico", "escuelas", "institutos", "catalán", "castellano", "inglés", "Cataluña"]),
             "sameAs": [REPO, REPO_DOCS],
             "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                               "contentUrl": f"{BASE}/dq-{lang}.json"}],
             "measurementTechnique": "Lectura dels projectes lingüístics publicats pels centres, amb cita literal de cada dada" if lang == "ca"
             else "Lectura de los proyectos lingüísticos publicados por los centros, con cita literal de cada dato"},
        ],
    }


def breadcrumbs(p, mol):
    items = []
    for i, (nm, href) in enumerate(mol, 1):
        it = {"@type": "ListItem", "position": i, "name": nm}
        it["item"] = absolut(p.rel, href) if href else url_de(p.rel)
        items.append(it)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def xifres_lead(s, abast="v-tot"):
    """De <p class="lead"> treu (centres, analitzats) de la variant d'un abast (per defecte, tots els centres)."""
    m = re.search(r'<p class="lead">(.*?)</p>', s, re.S)
    if not m:
        return None
    for sp in re.finditer(r'<span class="v ([^"]*)">(.*?)</span>', m.group(1), re.S):
        if abast in sp.group(1).split():
            n = re.findall(r"(\d[\d.]*)", text(sp.group(2)))
            if len(n) >= 2:
                return int(n[0].replace(".", "")), int(n[1].replace(".", ""))
    return None


def frase_xifres(s, t):
    """Les xifres de la descripció: les dels públics (el que mostra la pàgina en obrir-la) i el total."""
    nt, at = xifres_lead(s)
    pub = xifres_lead(s, "v-pub")
    if pub and pub[0] and pub[0] != nt:
        return t["xif_pub"].format(n=pub[0], a=pub[1], nt=nt, at=at)
    return t["xif_tot"].format(nt=nt, at=at)


def millora_titols(p):
    t = TXT[p.lang]
    eb = re.search(r'<p class="eb">(.*?)</p>', p.s, re.S)
    h1 = re.search(r"<h1>(.*?)</h1>", p.s, re.S)
    if not eb or not h1 or "data-pp-centre" in p.s:
        return
    tipus = text(eb.group(1)).split("·")[0].strip()
    nom = text(h1.group(1))
    x = xifres_lead(p.s)
    if not x:
        return
    n, a = x
    if tipus == "Comarca":
        title = t["t_com"].format(nom=nom)
        desc = t["d_com"].format(nom=nom, xif=frase_xifres(p.s, t))
    else:
        pare = text(eb.group(1)).split("·")[-1].strip()
        title = t["t_mun"].format(nom=nom)
        desc = (t["d_mun"] if a else t["d_mun0"]).format(nom=nom, pare=pare, n=n, a=a, xif=frase_xifres(p.s, t))
    p.s = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", p.s, count=1, flags=re.S)
    p.s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(desc)}">', p.s, count=1)


def capcalera(p, rel_ca, rel_es, data):
    lang = p.lang
    url = url_de(p.rel)
    title = text(re.search(r"<title>(.*?)</title>", p.s, re.S).group(1))
    dm = re.search(r'<meta name="description" content="([^"]*)">', p.s)
    desc = html.unescape(dm.group(1)) if dm else ""
    xdef = "" if p.rel in (f"{lang}/",) else rel_ca
    tags = [f'<link rel="canonical" href="{url}">', alternates(rel_ca, rel_es, xdef)]
    og_t = title.split(" · ")[0]
    img = f"{BASE}/static/og-{lang}.png"
    tags.append(
        f'<meta property="og:type" content="website"><meta property="og:site_name" content="{attr(NOM[lang])}">'
        f'<meta property="og:title" content="{attr(og_t)}"><meta property="og:description" content="{attr(desc)}">'
        f'<meta property="og:url" content="{url}"><meta property="og:image" content="{img}">'
        f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        f'<meta property="og:image:alt" content="{attr(NOM[lang])}">'
        f'<meta property="og:locale" content="{LOCALE[lang]}"><meta property="og:locale:alternate" content="{LOCALE["es" if lang == "ca" else "ca"]}">'
        f'<meta name="twitter:card" content="summary_large_image">'
    )
    mol = molles(p.s)
    if p.rel == f"{lang}/":
        tags.append(jsonld(dataset(lang, data)))
    elif mol:
        tags.append(jsonld(breadcrumbs(p, mol)))
    bloc = MARCA + "".join(tags)
    p.s = re.sub(r'(<meta name="description" content="[^"]*">)', lambda m: m.group(1) + bloc, p.s, count=1)


def recursos(p, v_css, v_js):
    arr = re.search(r'<link rel="stylesheet" href="([^"]*)static/estil\.css', p.s).group(1)
    p.s = re.sub(r'(<link rel="stylesheet" href="[^"]*static/estil\.css[^"]*">)',
                 lambda m: m.group(1) + f'<link rel="stylesheet" href="{arr}static/pp.css?v={v_css}">', p.s, count=1)
    p.s = p.s.replace("</body>", f'<script src="{arr}static/pp.js?v={v_js}" defer></script>\n</body>', 1)


def peu(p):
    lang = p.lang
    t = TXT[lang]
    arr = re.search(r'<main id="main"[^>]*data-arrel="([^"]*)"', p.s).group(1)
    m = base64.b64encode(CORREU_USUARI[::-1].encode()).decode().rstrip("=")
    issues = REPO + "/issues/new"
    priv = f"{arr}{lang}/{PRIV[lang]}/"

    def f1(mm):
        return mm.group(0) + f'<p class="peu-pare">{t["pare"]}</p>'
    p.s = re.sub(r'(<footer class="peu"><div class="wrap peu-in"><div>.*?</a><p>.*?</p>)', f1, p.s, count=1, flags=re.S)
    mapa = (f'<nav class="peu-c peu-mapa" aria-label="{attr(t["mapa"])}">'
            f'<a href="{arr}{lang}/">{t["inici"]}</a> · <a href="{arr}{lang}/{COM[lang]}/">{t["com_t"]}</a> · '
            f'<a href="{arr}{lang}/metodologia/">{t["metodo"]}</a> · <a href="{priv}">{t["priv_c"]}</a></nav>')
    extra = f'<p class="peu-c">{t["error"].format(issues=issues, m=m)}</p>' + mapa
    p.s = re.sub(r'(<p class="peu-cat">)', lambda mm: extra + mm.group(1), p.s, count=1)


def avis_abast(p):
    """Sota el títol de cada secció amb xifres, quins centres compten."""
    m = re.search(r'<div class="abast-n">.*?</div><p>(.*?)</p></div>', p.s, re.S)
    if not m:
        return
    spans = m.group(1)
    seg = TXT[p.lang]["ab_seg"]
    nota = f'<p class="pp-ab">{spans.replace(".</span>", "</span>")}<span class="pp-ab-s">· {seg}</span></p>'
    p.s = re.sub(r'(<section class="sec[^"]*" id="(?!centres|municipis)[^"]*"[^>]*><div class="sh">.*?</h2>(?:<p>.*?</p>)?)',
                 lambda mm: mm.group(1) + nota, p.s, flags=re.S)


def navegacio(p):
    """El menú «Comarques» porta a la pàgina pròpia; a la portada, la secció surt."""
    p.s = re.sub(r'href="([^"]*?)\b(ca|es)/#llocs"', lambda m: f'href="{m.group(1)}{m.group(2)}/{COM[m.group(2)]}/"', p.s)
    if p.rel == f"{p.lang}/":
        i = p.s.find('<section class="sec" id="llocs"')
        if i != -1:
            p.s = p.s[:i] + p.s[element(p.s, i):]
        p.s = re.sub(r'<p class="hero-l"><a href="#llocs">(.*?) ↓</a></p>',
                     lambda m: f'<p class="hero-l"><a href="{COM[p.lang]}/">{m.group(1)} →</a></p>', p.s)
        p.s = re.sub(r'<a href="#llocs">(?:(?!</a>).)*</a>', "", p.s, flags=re.S)  # subnavegació
    if p.rel == f"{p.lang}/{COM[p.lang]}/":
        p.s = re.sub(r'(<nav class="nav"[^>]*>.*?<a href="[^"]*{0}/"\s*)>'.format(COM[p.lang]),
                     lambda m: m.group(1) + ' aria-current="page">', p.s, count=1, flags=re.S)


def es_cites(p):
    c = TXT[p.lang]["cites"]
    if c:
        p.s = p.s.replace(c[0], c[1])


# ------------------------------------------------------------------ v3: una sola capçalera, nom, ordre, projecte lingüístic

SUBTITOL = {"ca": "Escola a escola", "es": "Escuela a escuela"}
PL = {"ca": "projecte-linguistic", "es": "proyecto-linguistico"}
ORDRE = ["habitual", "cursos", "materies", "alumnat", "espais", "families", "drets"]
AB_CURT = {
    "ca": {"pub": "Públics", "con": "Concertats", "pri": "Privats", "pc": "Públics i concertats",
           "pp": "Públics i privats", "cp": "Concertats i privats", "tot": "Tots"},
    "es": {"pub": "Públicos", "con": "Concertados", "pri": "Privados", "pc": "Públicos y concertados",
           "pp": "Públicos y privados", "cp": "Concertados y privados", "tot": "Todos"},
}
T3 = {
    "ca": {
        "centres": "Centres",
        "canvia": "Canvia-ho",
        "abm_n": "Tria quins tipus de centre compten a les xifres de tot el web. Com a mínim un.",
        "abm_l": "Tipus de centre que compten a les xifres",
        "nav_pl": "Projecte lingüístic",
        "seg": ", segons el que diuen els seus documents.",
        "eb_data": "Dades públiques, analitzades de manera independent amb la IA Claude",
        "peu_qui": 'Projecte independent i de codi obert: els documents, les dades i el codi són públics a <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>, perquè qualsevol persona ho pugui comprovar. No està vinculat a cap administració, centre ni organització.',
        "peu_dades": "Dades extretes dels projectes lingüístics que publiquen els mateixos centres; cada dada enllaça el seu document. Última actualització: {data}.",
        "peu_cat": "Fet a Catalunya.",
        "pl_t": "Què és un projecte lingüístic",
        "pl_lead": "És el document on cada escola i institut explica com ensenya i fa servir les llengües. Aquí trobaràs què hi ha de constar, per què es publica i de quan són els que hem pogut llegir.",
        "pl_desc": "Què és el projecte lingüístic d'un centre educatiu de Catalunya, què hi ha de constar segons la llei, per què es publica i de quan són els documents.",
        "pl_toc": "En aquesta pàgina",
        "doc_sub": "L'any de cada document, segons la data que hi consta. {n} documents no porten data i no hi compten.",
        "doc_abans": "Abans",
        "doc_tip_abans": "Abans del 2007: {n} documents",
        "doc_tip": "{y}: {n} documents",
    },
    "es": {
        "centres": "Centros",
        "canvia": "Cambiar",
        "abm_n": "Elige qué tipos de centro cuentan en las cifras de toda la web. Como mínimo uno.",
        "abm_l": "Tipos de centro que cuentan en las cifras",
        "nav_pl": "Proyecto lingüístico",
        "seg": ", según lo que dicen sus documentos.",
        "eb_data": "Datos públicos, analizados de forma independiente con la IA Claude",
        "peu_qui": 'Proyecto independiente y de código abierto: los documentos, los datos y el código son públicos en <a href="https://github.com/Observatori-Linguistic" rel="noopener" target="_blank">GitHub</a>, para que cualquier persona pueda comprobarlo. No está vinculado a ninguna administración, centro ni organización.',
        "peu_dades": "Datos extraídos de los proyectos lingüísticos que publican los propios centros; cada dato enlaza su documento. Última actualización: {data}.",
        "peu_cat": "Hecho en Cataluña.",
        "pl_t": "Qué es un proyecto lingüístico",
        "pl_lead": "Es el documento en el que cada escuela e instituto explica cómo enseña y usa las lenguas. Aquí encontrarás qué debe incluir, por qué se publica y de cuándo son los que hemos podido leer.",
        "pl_desc": "Qué es el proyecto lingüístico de un centro educativo de Cataluña, qué debe incluir según la ley, por qué se publica y de cuándo son los documentos.",
        "pl_toc": "En esta página",
        "doc_sub": "El año de cada documento, según la fecha que consta en él. {n} documentos no llevan fecha y no cuentan.",
        "doc_abans": "Antes",
        "doc_tip_abans": "Antes de 2007: {n} documentos",
        "doc_tip": "{y}: {n} documentos",
    },
}

PL_COS = {
    "ca": [
        ("que", "Què és", """<p>El projecte lingüístic forma part del projecte educatiu de cada centre. Hi consta quina llengua es fa servir a les classes, quan i com s'ensenyen el català, el castellà i les llengües estrangeres, en quines llengües es comunica el centre amb les famílies i com s'acull l'alumnat que arriba sense conèixer les llengües oficials.</p>
<p>La Llei d'educació de Catalunya (Llei 12/2009, article 14) obliga a tenir-ne un tots els centres públics i els privats sostinguts amb fons públics, és a dir, els concertats. Els privats sense concert no hi estan obligats, i pocs el publiquen.</p>"""),
        ("contingut", "Què hi ha de constar", """<p>Segons l'article 14 de la Llei d'educació, el projecte lingüístic ha de tractar, com a mínim:</p>
<ul><li>l'ús del català com a llengua vehicular i d'aprenentatge;</li><li>l'ensenyament i l'aprenentatge del castellà;</li><li>les opcions de llengües estrangeres que ofereix el centre;</li><li>com s'adapta l'ensenyament de les llengües a la realitat sociolingüística del centre, per a tot l'alumnat i per a cada alumne;</li><li>la coherència en l'ús de les llengües als serveis del centre i a les activitats de l'associació de famílies.</li></ul>
<p>La Llei 8/2022 i el Decret llei 6/2022 estableixen que l'ús de les llengües es decideix amb criteris pedagògics i de manera singular per a cada centre, sense percentatges. Aquestes normes es van aprovar després d'una sentència del Tribunal Superior de Justícia de Catalunya (TSJC) que fixava que almenys el 25 % del temps lectiu s'havia de fer en castellà.</p>
<p>El Decret 91/2024, del règim lingüístic del sistema educatiu no universitari, hi afegeix, entre altres coses, indicadors per avaluar les llengües, les mesures per a l'alumnat nouvingut i els criteris de coherència lingüística del centre. El TSJC ha anul·lat diversos articles d'aquest decret; la sentència no és ferma, però el març de 2026 en va ordenar l'execució provisional.</p>"""),
        ("qui", "Qui el fa", """<p>L'elabora el mateix centre, amb la participació del claustre i del consell escolar, on hi ha representants del professorat, de les famílies i de l'alumnat. Després, el Departament d'Educació el valida.</p>"""),
        ("public", "Per què es publica", """<p>La llei estatal d'educació (LOE, article 121) diu que els centres han de fer públic el seu projecte educatiu perquè el conegui tota la comunitat educativa, i el projecte lingüístic en forma part. A Catalunya, les famílies tenen dret a conèixer el projecte educatiu del centre (Decret 102/2010, article 6).</p>
<p>Per a les famílies és la manera de saber quin paper hi té cada llengua, també abans de triar centre. La majoria de centres el publiquen al seu web, però no tots: ara mateix, {nopub} dels {cens} centres no el publiquen.</p>"""),
        ("documents", "De quan són els documents", """<p>La normativa també regula la revisió dels projectes lingüístics (Decret llei 6/2022). El 2022, el Departament d'Educació va demanar als centres que comprovessin amb un qüestionari si el seu projecte s'ajustava a la nova normativa, i que l'adaptessin si calia. Tot i així, molts documents fa anys que no s'actualitzen. Cada fitxa d'aquest web mostra la data del document del centre.</p>"""),
        ("web", "Com el llegim en aquest web", """<p>De cada projecte lingüístic en traiem quin paper dona el document a cada llengua, curs a curs, amb la frase literal que ho justifica. Ho expliquem a <a href="{arr}ca/metodologia/">Com ho mesurem</a>. Per començar, busca el teu municipi a <a href="{arr}ca/comarques/">Comarques i municipis</a>.</p>"""),
    ],
    "es": [
        ("que", "Qué es", """<p>El proyecto lingüístico forma parte del proyecto educativo de cada centro. En él consta qué lengua se usa en las clases, cuándo y cómo se enseñan el catalán, el castellano y las lenguas extranjeras, en qué lenguas se comunica el centro con las familias y cómo se acoge al alumnado que llega sin conocer las lenguas oficiales.</p>
<p>La Ley de educación de Cataluña (Ley 12/2009, artículo 14) obliga a tener uno a todos los centros públicos y a los privados sostenidos con fondos públicos, es decir, los concertados. Los privados sin concierto no están obligados, y pocos lo publican.</p>"""),
        ("contingut", "Qué debe incluir", """<p>Según el artículo 14 de la Ley de educación, el proyecto lingüístico debe tratar, como mínimo:</p>
<ul><li>el uso del catalán como lengua vehicular y de aprendizaje;</li><li>la enseñanza y el aprendizaje del castellano;</li><li>las opciones de lenguas extranjeras que ofrece el centro;</li><li>cómo se adapta la enseñanza de las lenguas a la realidad sociolingüística del centro, para todo el alumnado y para cada alumno;</li><li>la coherencia en el uso de las lenguas en los servicios del centro y en las actividades de la asociación de familias.</li></ul>
<p>La Ley 8/2022 y el Decreto ley 6/2022 establecen que el uso de las lenguas se decide con criterios pedagógicos y de forma singular para cada centro, sin porcentajes. Estas normas se aprobaron después de una sentencia del Tribunal Superior de Justicia de Cataluña (TSJC) que fijaba que al menos el 25 % del tiempo lectivo debía hacerse en castellano.</p>
<p>El Decreto 91/2024, del régimen lingüístico del sistema educativo no universitario, añade, entre otras cosas, indicadores para evaluar las lenguas, las medidas para el alumnado recién llegado y los criterios de coherencia lingüística del centro. El TSJC ha anulado varios artículos de este decreto; la sentencia no es firme, pero en marzo de 2026 ordenó su ejecución provisional.</p>"""),
        ("qui", "Quién lo hace", """<p>Lo elabora el propio centro, con la participación del claustro y del consejo escolar, donde hay representantes del profesorado, de las familias y del alumnado. Después, el Departament d'Educació lo valida.</p>"""),
        ("public", "Por qué se publica", """<p>La ley estatal de educación (LOE, artículo 121) dice que los centros deben hacer público su proyecto educativo para que lo conozca toda la comunidad educativa, y el proyecto lingüístico forma parte de él. En Cataluña, las familias tienen derecho a conocer el proyecto educativo del centro (Decreto 102/2010, artículo 6).</p>
<p>Para las familias es la forma de saber qué papel tiene cada lengua, también antes de elegir centro. La mayoría de centros lo publican en su web, pero no todos: ahora mismo, {nopub} de los {cens} centros no lo publican.</p>"""),
        ("documents", "De cuándo son los documentos", """<p>La normativa también regula la revisión de los proyectos lingüísticos (Decreto ley 6/2022). En 2022, el Departament d'Educació pidió a los centros que comprobaran con un cuestionario si su proyecto se ajustaba a la nueva normativa, y que lo adaptaran si hacía falta. Aun así, muchos documentos llevan años sin actualizarse. Cada ficha de esta web muestra la fecha del documento del centro.</p>"""),
        ("web", "Cómo lo leemos en esta web", """<p>De cada proyecto lingüístico sacamos qué papel da el documento a cada lengua, curso a curso, con la frase literal que lo justifica. Lo explicamos en <a href="{arr}es/metodologia/">Cómo lo medimos</a>. Para empezar, busca tu municipio en <a href="{arr}es/comarcas/">Comarcas y municipios</a>.</p>"""),
    ],
}


def marca(p_s, lang):
    """Nom «Observatori Lingüístic» i, al logotip, un subtítol que expliqui el projecte."""
    s = re.sub(r'(<span class="mw"><b>[^<]*</b> <span>)Escolar(</span>)', lambda m: m.group(1) + SUBTITOL[lang] + m.group(2), p_s)
    return (s.replace("Observatori Lingüístic Escolar", "Observatori Lingüístic").replace("Observatorio Lingüístico Escolar", "Observatori Lingüístic")
             .replace("Observatorio Lingüístico", "Observatori Lingüístic"))


def data_text(s):
    m = re.search(r"(?:Última actualització de les dades|Última actualización de los datos): ([^.<]*)\.", s)
    return m.group(1) if m else ""


def menu_abast(p, filtre_tpl):
    """El filtre de tipus de centre passa a la capçalera, en un menú compacte; la subnavegació deixa de ser fixa."""
    if 'class="pp-abm"' in p.s:
        return
    t = T3[p.lang]
    i = p.s.find('<div class="filtre filtre-s"')
    if i != -1:
        f = p.s[i:element(p.s, i)]
        p.s = p.s[:i] + p.s[element(p.s, i):]
    elif "data-tipus" in p.s or "data-pp-abm" in p.s:
        f = filtre_tpl[p.lang]
    else:
        return
    f = f.replace("filtre filtre-s", "filtre pp-abf")
    spans = "".join(f'<span class="v v-{k}">{v}</span>' for k, v in AB_CURT[p.lang].items())
    menu = (f'<details class="pp-abm"><summary title="{attr(t["abm_l"])}"><span class="pp-abm-t">{t["centres"]}:</span><span class="pp-abm-v">{spans}</span></summary>'
            f'<div class="pp-abm-p">{f}<p>{t["abm_n"]}</p></div></details>')
    p.s = p.s.replace('<nav class="nav"', menu + '<nav class="nav"', 1)
    # el selector d'idioma, fora del menú: al mòbil va al costat del logotip
    p.s = p.s.replace('<nav class="subnav"', '<nav class="subnav pp-index"', 1)
    # el filtre de dins de la pàgina surt: queda la frase, amb un enllaç que obre el menú de la capçalera
    while True:
        i = p.s.find('<div class="filtre filtre-h"')
        if i == -1:
            break
        p.s = p.s[:i] + p.s[element(p.s, i):]
    i = p.s.find('<div class="abast-n">')
    if i != -1:
        j = element(p.s, i)
        bloc = re.sub(r'</p></div>$', f' <button type="button" class="pp-lnk pp-canvia" data-pp-abm-obre>{t["canvia"]}</button></p></div>', p.s[i:j])
        p.s = p.s[:i] + bloc + p.s[j:]


def idioma_fora(p):
    """El selector CA/ES surt de <nav class="nav"> i queda com a darrer element de la capçalera."""
    m = re.search(r'<header class="top">.*?</header>', p.s, re.S)
    if not m or 'pp-idioma' in m.group(0):
        return
    top = m.group(0)
    i = top.find('<div class="idioma"')
    if i == -1:
        return
    j = element(top, i)
    idi = top[i:j].replace('<div class="idioma"', '<div class="idioma pp-idioma"', 1)
    top = top[:i] + top[j:]
    k = top.rfind("</div></header>")
    top = top[:k] + idi + top[k:]
    p.s = p.s[:m.start()] + top + p.s[m.end():]


def seccions_a_capcalera(p):
    """L'índex de seccions forma part de la capçalera (segona línia), visible des que es carrega la pàgina."""
    i = p.s.find('<nav class="subnav')
    if i == -1:
        return
    j = element(p.s, i)
    sub = p.s[i:j]
    p.s = p.s[:i] + p.s[j:]
    m = re.search(r'<header class="top">.*?</header>', p.s, re.S)
    k = m.end() - len("</header>")
    p.s = p.s[:k] + sub + p.s[k:]
    p.s = p.s.replace('<header class="top">', '<header class="top pp-amb-seccions">', 1)


def llengues_oficials(p):
    """«Les llengües oficials, comparades»: què vol dir la xifra va en una fila pròpia a cada bloc
    (sobre les dues columnes de xifres), no dins la columna; fora «(P3–P5)» i la nota «La xifra:»;
    la nota final explica qui compta a les pestanyes de l'alumnat."""
    NOTA = {"ca": " Les dues pestanyes només compten els centres amb alumnat majoritàriament d'una de les dues llengües; la resta només entra a «Tots els centres».",
            "es": " Las dos pestañas solo cuentan los centros con alumnado mayoritariamente de una de las dos lenguas; el resto solo entra en «Todos los centros»."}
    def secc(sec):
        sec = sec.replace("Infantil (P3–P5)", "Infantil")
        parts = sec.split('<div class="cc-g">')
        out = [parts[0]]
        for part in parts[1:]:
            m = re.match(r"(.*?)<small>(?:La cifra|La xifra): (.*?)</small></div>", part, re.S)
            if not m:
                out.append('<div class="cc-g">' + part)
                continue
            cap = re.sub(r"\s+(en toda la etapa|a tota l&#x27;etapa|a tota l'etapa)$", "", m.group(2))
            cap_html = f'<span class="pp-cgc" aria-hidden="true">% {cap}</span>'
            cap_l = cap_html.replace("pp-cgc", "pp-cgc pp-cgc-e")
            cap_r = cap_html.replace("pp-cgc", "pp-cgc pp-cgc-d")
            part = part[m.end():]
            part = re.sub(r'(<span class="cc-v">(?:<(?=\d)|>)?[^<]*?)<small>.*?</small>(</span>)', r"\1\2", part, flags=re.S)
            out.append(f'<div class="cc-g pp-cg">{cap_l}<span class="pp-cgt">{m.group(1)}</span>{cap_r}</div>' + part)
        sec = "".join(out)
        sec = re.sub(r"((?:consta en|consta en) \d+ (?:de los|dels) \d+ (?:centros|centres)\.)(</p>)",
                     lambda x: x.group(1) + NOTA[p.lang] + x.group(2), sec, count=1)
        return sec
    out, pos = [], 0
    for m in re.finditer(r'<section class="sec sec-dr" id="drets[^"]*"', p.s):
        if m.start() < pos:
            continue
        j = element(p.s, m.start())
        out.append(p.s[pos:m.start()])
        out.append(secc(p.s[m.start():j]))
        pos = j
    out.append(p.s[pos:])
    p.s = "".join(out)


HP = {
    "ca": {"ca": "Més català", "ca_es": "Més català i castellà", "es": "Més castellà", "altres": "Més altres llengües",
           "frase": "En {n}, el grup més nombrós de l'alumnat parla {l}", "noms": {"ca": "català", "ca_es": "català i castellà", "es": "castellà", "altres": "altres llengües"},
           "i": " i ",
           "nota": " Cada centre surt a la pestanya de la llengua del grup més nombrós de l'alumnat (sense comptar la part sense desglossar), ordenat de més a menys. La pestanya que s'obre és la que té més centres."},
    "es": {"ca": "Más catalán", "ca_es": "Más catalán y castellano", "es": "Más castellano", "altres": "Más otras lenguas",
           "frase": "En {n}, el grupo más numeroso del alumnado habla {l}", "noms": {"ca": "catalán", "ca_es": "catalán y castellano", "es": "castellano", "altres": "otras lenguas"},
           "i": " y ",
           "nota": " Cada centro sale en la pestaña de la lengua del grupo más numeroso de su alumnado (sin contar la parte sin desglosar), ordenado de más a menos. La pestaña que se abre es la que tiene más centros."},
}
HP_L = ["ca", "ca_es", "es", "altres"]


def alumnat_pestanyes(p):
    """«Quina llengua parla l'alumnat a casa»: abans, una sola llista ordenada per qui té més castellà.
    Ara, pestanyes (com a «Les llengües oficials, comparades»): cada centre a la de la llengua del grup
    més nombrós (català, castellà, altres), ordenat per aquesta xifra; s'obre la que té més centres.
    La frase de la capçalera de la secció, simètrica."""
    T = HP[p.lang]
    def secc(sec):
        m = re.search(r'<ul class="(hrows(?: hrows-l)?)">(.*?)</ul>(<button type="button" class="mes-b" data-desplega>([^<]*?)\(\d+\)</button>)?', sec, re.S)
        if not m or "pp-hp" in sec:
            return sec
        files = re.findall(r'<li class="hrow[^"]*">.*?</li>', m.group(2), re.S)
        grups = {k: [] for k in HP_L}
        for li in files:
            v = {k: 0.0 for k in HP_L}
            for cl, fx in re.findall(r'class="hs h-([a-z_]+)" style="flex:([\d.]+)"', li):
                if cl in v:
                    v[cl] = float(fx)
            mx = max(v.values())
            for k in HP_L:
                if v[k] == mx:
                    grups[k].append((-v[k], li))
        for k in HP_L:
            grups[k].sort(key=lambda x: x[0])
        presents = [k for k in HP_L if grups[k]]
        if not presents:
            return sec
        obre = max(presents, key=lambda k: (len(grups[k]), -HP_L.index(k)))
        boto = (m.group(4) or ("Veure'ls tots " if p.lang == "ca" else "Verlos todos ")).rstrip() + " "
        vistes = []
        for k in presents:
            ul = f'<ul class="{m.group(1)}">' + "".join(li for _, li in grups[k]) + "</ul>"
            if len(grups[k]) > 12 and "hrows-l" in m.group(1):
                ul += f'<button type="button" class="mes-b" data-desplega>{boto}({len(grups[k])})</button>'
            hid = "" if k == obre else " hidden"
            vistes.append(f'<div class="pp-hv" data-cc-v="{k}"{hid}>{ul}</div>')
        pest = ""
        if len(presents) > 1:
            pest = '<div class="cc-p pp-hp" role="tablist">' + "".join(
                f'<button type="button" role="tab" data-cc="{k}" aria-selected="{"true" if k == obre else "false"}">{T[k]} <small>{len(grups[k])}</small></button>'
                for k in presents) + "</div>"
        sec = sec[:m.start()] + pest + "".join(vistes) + sec[m.end():]
        # frase de la capçalera: simètrica
        parts = [f"en {len(grups[k])}, {T['noms'][k]}" for k in presents]
        if parts:
            parts[0] = T["frase"].format(n=len(grups[presents[0]]), l=T["noms"][presents[0]])
            if len(parts) > 1:
                frase = "; ".join(parts[:-1]) + ";" + T["i"] + parts[-1] + "."
            else:
                frase = parts[0] + "."
            sec = re.sub(r"(<div class=\"sh\"><h2.*?</h2><p>[^<]*?\.) En \d+, (?:hi ha|hay) [^<]*?\.(</p>)",
                         lambda x: x.group(1) + " " + frase + x.group(2), sec, count=1, flags=re.S)
        # nota final
        sec = re.sub(r'(<p class="nota">[^<]*?)(</p>)(?![\s\S]*<p class="nota">)', lambda x: x.group(1) + T["nota"] + x.group(2), sec, count=1)
        return sec
    out, pos = [], 0
    for m in re.finditer(r'<section class="sec" id="alumnat[^"]*"', p.s):
        if m.start() < pos:
            continue
        j = element(p.s, m.start())
        out.append(p.s[pos:m.start()])
        out.append(secc(p.s[m.start():j]))
        pos = j
    out.append(p.s[pos:])
    p.s = "".join(out)


TL = {
    "ca": {"sub": "Per a cada llengua, la mateixa pregunta que a «Les llengües oficials, comparades»: quin paper li dona el document a l'etapa triada. La xifra: llengua de les classes a tota l'etapa. Fes clic al títol d'una columna per ordenar-la, o a una cel·la per veure'n els centres.",
           "et": {"infantil": "Infantil", "primaria": "Primària", "eso": "ESO", "batxillerat": "Batxillerat"},
           "centres": "centres", "tab": "Etapa"},
    "es": {"sub": "Para cada lengua, la misma pregunta que en «Las lenguas oficiales, comparadas»: qué papel le da el documento en la etapa elegida. La cifra: lengua de las clases en toda la etapa. Haz clic en el título de una columna para ordenarla, o en una celda para ver sus centros.",
           "et": {"infantil": "Infantil", "primaria": "Primaria", "eso": "ESO", "batxillerat": "Bachillerato"},
           "centres": "centros", "tab": "Etapa"},
}
ET_LLETRA = {"infantil": "I", "primaria": "P", "eso": "E", "batxillerat": "B"}
TI_AB = {"pub": [""], "con": ["c"], "pri": ["p"], "pc": ["", "c"], "pp": ["", "p"], "cp": ["c", "p"], "tot": ["", "c", "p"]}
CATS = ["veh", "mat", "asig", "parcial", "nc", "no"]
CAT_CL = {"veh": "r-vehicular", "mat": "r-materia", "asig": "r-asignatura", "parcial": "r-ocasional", "nc": "cc-nc", "no": "cc-sw-no"}


def categoria_etapa(rs):
    """La mateixa classificació que «Les llengües oficials, comparades» (app.js, cc)."""
    tots = lambda st: all(x in st for x in rs)
    algun = lambda st: any(x in st for x in rs)
    if tots("V"):
        return "veh"
    if algun("VM"):
        return "mat"
    if tots("A"):
        return "asig"
    if algun("AOC"):
        return "parcial"
    if tots("X"):
        return "nc"
    return "no"


def pct_txt(v):
    if v == 0:
        return "0 %"
    if v < 1:
        return "&lt;1 %"
    if v > 99 and v < 100:
        return "&gt;99 %"
    return f"{round(v)} %"


_IDX = {}


def index_llocs(dq):
    """(abast, etapa, lloc, llengua) -> recompte de categories, per a tots els prefixos de lloc (comarca, municipi, districte)."""
    if id(dq) in _IDX:
        return _IDX[id(dq)]
    etapes = dict((e[0], e[1]) for e in dq["etapes"])
    idx = {}
    for r in dq["c"]:
        ti = r.get("ti") or ""
        parts = r["u"].split("/")
        prefixos = ["/".join(parts[:k]) for k in range(1, len(parts) + 1)] + [""]
        for et, cs in etapes.items():
            if ET_LLETRA[et] not in r["e"]:
                continue
            if not any(r["r"]["ca"][k] not in "X-" or r["r"]["es"][k] not in "X-" for k in cs):
                continue
            cats = {ll: categoria_etapa([r["r"][ll][k] for k in cs]) for ll in ("ca", "es", "en")}
            for ab, tis in TI_AB.items():
                if ti not in tis:
                    continue
                for pre in prefixos:
                    for ll, c in cats.items():
                        d = idx.setdefault((ab, et, pre, ll), {x: 0 for x in CATS})
                        d[c] += 1
    _IDX[id(dq)] = idx
    return idx


def taula_llocs(p, dq):
    """La taula de comarques (o de municipis) amb la mateixa mesura per a cada llengua i cada etapa."""
    i = p.s.find('<section class="sec" id="llocs"')
    if i == -1 or dq is None or "pp-tl" in p.s:
        return
    j = element(p.s, i)
    sec = p.s[i:j]
    lang = p.lang
    t = TL[lang]
    l = dq["l"]
    etapes = dict((e[0], e[1]) for e in dq["etapes"])
    centres = dq["c"]

    idx = index_llocs(dq)

    def cel(ab, L, et, ll):
        comp = idx.get((ab, et, L, ll))
        n = sum(comp.values()) if comp else 0
        if not n:
            return '<td data-v="-1" class="pp-buit">—</td>'
        segs = "".join(f'<i class="{CAT_CL[c]}" style="width:{100 * comp[c] / n:.2f}%"></i>' for c in CATS if comp[c] and c != "no")
        veh = 100 * comp["veh"] / n
        nom_l = l["noms"][ll]
        parts = [f'{l["cc_c_no_etapa" if c == "no" else "cc_c_" + c]} {pct_txt(100 * comp[c] / n)}'.replace("&lt;", "<").replace("&gt;", ">")
                 for c in CATS if comp[c]]
        tip = f'{nom_l} · {t["et"][et]} ({n} {t["centres"]}): ' + " · ".join(parts)
        return (f'<td data-v="{veh:.2f}" data-q="cc:{et}:{ll}" data-l="{L}" tabindex="0" role="button" data-tip="{attr(tip)}">'
                f'<span class="cc-t pp-mini">{segs}</span><b>{pct_txt(veh)}</b></td>')

    def nova_taula(ab, taula):
        thead = re.search(r"<thead>.*?</thead>", taula, re.S).group(0)
        ths = re.findall(r"<th scope=\"col\">.*?</th>", thead, re.S)
        files = re.findall(r"<tr>(<th scope=\"row\".*?</th>)(<td.*?</td>)(<td.*?</td>)(<td.*?)</tr>", taula, re.S)
        cap = "".join(ths[:3])
        for k, ll in enumerate(("ca", "es", "en")):
            cap += (f'<th scope="col"><button type="button" data-ordena="{3 + k}"><span class="xip x-{ll}"><i aria-hidden="true">{ll.upper()}</i></span> '
                    f'{l["noms"][ll]}</button></th>')
        blocs = []
        for et in ("infantil", "primaria", "eso", "batxillerat"):
            cos = []
            for th, td1, td2, resta in files:
                L = re.search(r'data-l="([^"]*)"', resta)
                if not L:
                    continue
                L = L.group(1)
                cos.append("<tr>" + th + td1 + td2 + "".join(cel(ab, L, et, ll) for ll in ("ca", "es", "en")) + "</tr>")
            blocs.append(f'<div class="scroll pp-et-t" data-et="{et}"><table class="tl pp-tl" data-taula><thead><tr>{cap}</tr></thead>'
                         f'<tbody>{"".join(cos)}</tbody></table></div>')
        return "".join(blocs)

    def f(m):
        ab = m.group(1)
        dins = sec[m.end():element(sec, m.start()) - len("</div>")]
        k = dins.find("<table")
        taula = dins[k:element(dins, k)]
        return f'<div class="v v-{ab}">' + nova_taula(ab, taula) + "</div>"
    out, pos = [], 0
    for m in re.finditer(r'<div class="v v-(\w+)">', sec):
        if m.start() < pos:
            continue
        e = element(sec, m.start())
        out.append(sec[pos:m.start()])
        out.append(f(m))
        pos = e
    out.append(sec[pos:])
    sec = "".join(out)
    tabs = ('<div class="cc-p pp-et-tabs" role="tablist" aria-label="' + t["tab"] + '">'
            + "".join(f'<button type="button" role="tab" data-pp-et="{et}" aria-selected="{"true" if et == "infantil" else "false"}">{nom}</button>'
                      for et, nom in t["et"].items()) + "</div>")
    lg = ('<ul class="cc-lg pp-tl-lg">' + "".join(
        f'<li><span class="sw {CAT_CL[c] if c != "no" else "cc-sw-no"}"></span>{l["cc_c_no_etapa" if c == "no" else "cc_c_" + c]}</li>' for c in CATS) + "</ul>")
    sec = re.sub(r'(<div class="sh">.*?</h2>)<p>.*?</p>(</div>)', lambda m: m.group(1) + f"<p>{t['sub']}</p>" + m.group(2) + tabs + lg, sec, count=1, flags=re.S)
    sec = sec.replace('<section class="sec" id="llocs"', '<section class="sec pp-llocs" data-pp-et-on="infantil" id="llocs"', 1)
    p.s = p.s[:i] + sec + p.s[j:]


def reordena(p):
    """Ordre de les seccions: habitual, curs a curs, matèries, alumnat, fora de l'aula, famílies, llengües oficials.
    La secció de l'antiguitat dels documents passa a la pàgina del projecte lingüístic."""
    s = p.s
    items = []
    for m in re.finditer(r'<section class="sec[^"]*" id="([a-z]+)(?:__\w+)?"', s):
        base = m.group(1)
        if base in ORDRE or base == "antiguitat":
            items.append((base, m.start(), element(s, m.start())))
    grups, actual = [], []
    for it in items:
        if actual and s[actual[-1][2]:it[1]].strip() != "":
            grups.append(actual)
            actual = []
        actual.append(it)
    if actual:
        grups.append(actual)
    for g in reversed(grups):
        bons = sorted([x for x in g if x[0] != "antiguitat"], key=lambda x: ORDRE.index(x[0]))
        nou = "".join(s[a:b] for _, a, b in bons)
        s = s[:g[0][1]] + nou + s[g[-1][2]:]
    # subnavegació: el mateix ordre
    def f(m):
        links = re.findall(r'<a href="#([a-z]+)">.*?</a>', m.group(2), re.S)
        cos = m.group(2)
        trossos = {k: re.search(r'<a href="#' + k + r'">.*?</a>', cos, re.S).group(0) for k in links}
        ord_links = [k for k in links if k in ORDRE]
        ord_sorted = sorted(ord_links, key=ORDRE.index)
        it = iter(ord_sorted)
        nous = [trossos[next(it)] if k in ORDRE else trossos[k] for k in links if k != "antiguitat"]
        return m.group(1) + "".join(nous) + m.group(3)
    s = re.sub(r'(<div class="sn-a">)(.*?)(</div>)', f, s, count=1, flags=re.S)
    p.s = s


def capcalera_pagina(p):
    """Portada i llocs: sense dades repetides. L'etiqueta superior diu el tipus de pàgina o la data de les dades."""
    t = T3[p.lang]
    lang = p.lang
    # el filtre de la capçalera de la pàgina diu també que les xifres surten dels documents
    i = p.s.find('<div class="abast-n">')
    if i != -1:
        j = element(p.s, i)
        p.s = p.s[:i] + re.sub(r"\.</span>", lambda x: t["seg"] + "</span>", p.s[i:j]) + p.s[j:]
    if p.rel == f"{lang}/":
        tot = re.search(r'<p class="hero-n">.*?<span class="v v-tot">(\d[\d.]*)', p.s, re.S)
        n = int(tot.group(1).replace(".", "")) if tot else 0
        p.s = re.sub(r'<p class="eb">[^<]*</p>', f'<p class="eb">{t["eb_data"].format(n=f"{n:,}".replace(",", "."))}</p>', p.s, count=1)
        p.s = re.sub(r'<p class="hero-n">.*?</p>', "", p.s, count=1, flags=re.S)
        # «projecte lingüístic» de l'entradeta enllaça a la pàgina que l'explica
        p.s = re.sub(r'(<p class="lead">[^<]*?)(projecte lingüístic|proyecto lingüístico)', lambda m: f'{m.group(1)}<a href="{PL[lang]}/">{m.group(2)}</a>', p.s, count=1)
    m = re.search(r'<header class="ph-l[^"]*">', p.s)
    if m:
        # «Municipi · Maresme» repeteix les molles: només el tipus
        p.s = re.sub(r'(<p class="eb">)([^<·]*?)\s*·[^<]*(</p>)', lambda x: x.group(1) + x.group(2) + x.group(3), p.s, count=1)
        # el nombre de centres ja surt a la llegenda de la barra
        if '<div class="cob"' in p.s:
            p.s = re.sub(r'(<h1>.*?</h1>)<p class="lead">.*?</p>', lambda x: x.group(1), p.s, count=1, flags=re.S)


def peu3(p):
    lang = p.lang
    t, t3 = TXT[lang], T3[lang]
    arr = re.search(r'<main id="main"[^>]*data-arrel="([^"]*)"', p.s).group(1)
    i = p.s.find('<footer class="peu"')
    if i == -1:
        return
    j = element(p.s, i)
    peu = p.s[i:j]
    marca_html = re.search(r'<a class="marca".*?</a>', peu, re.S).group(0)
    mapa_f = re.search(r'<p class="peu-f">.*?</p>', peu, re.S)
    cat_svg = re.search(r'<p class="peu-cat">(<svg.*?</svg>)', peu, re.S)
    m = base64.b64encode(CORREU_USUARI[::-1].encode()).decode().rstrip("=")
    issues = REPO + "/issues/new"
    data = data_text(peu)
    nav = (f'<nav class="peu-c peu-mapa" aria-label="{attr(t["mapa"])}">'
           f'<a href="{arr}{lang}/">{t["inici"]}</a> · <a href="{arr}{lang}/{COM[lang]}/">{t["com_t"]}</a> · '
           f'<a href="{arr}{lang}/{PL[lang]}/">{t3["pl_t"]}</a> · '
           f'<a href="{arr}{lang}/metodologia/">{t["metodo"]}</a> · <a href="{arr}{lang}/{PRIV[lang]}/">{t["priv_c"]}</a></nav>')
    nou = (f'<footer class="peu"><div class="wrap peu-in"><div>{marca_html}<p>{t3["peu_qui"]}</p></div>'
           f'<div><p>{t3["peu_dades"].format(data=data)}</p>'
           f'<p class="peu-c">{t["error"].format(issues=issues, m=m)}</p>{nav}'
           + (mapa_f.group(0) if mapa_f else "")
           + (f'<p class="peu-cat">{cat_svg.group(1)}{t3["peu_cat"]}</p>' if cat_svg else "")
           + "</div></div></footer>")
    p.s = p.s[:i] + nou + p.s[j:]


def nav_pl(p):
    """Menú: Comarques · Projecte lingüístic · Com ho mesurem."""
    t3 = T3[p.lang]
    lang = p.lang
    def f(m):
        nav = m.group(0)
        if f'>{t3["nav_pl"]}</a>' in nav:
            return nav
        return re.sub(r'(<a href="([^"]*?){0}/{1}/"[^>]*>[^<]*</a>)'.format(lang, COM[lang]),
                      lambda x: x.group(1) + f'<a href="{x.group(2)}{lang}/{PL[lang]}/">{t3["nav_pl"]}</a>', nav, count=1)
    p.s = re.sub(r'<nav class="nav".*?</nav>', f, p.s, count=1, flags=re.S)
    if p.rel == f"{lang}/{PL[lang]}/":
        p.s = re.sub(r'(<nav class="nav".*?<a href="[^"]*{0}/")>'.format(PL[lang]), lambda m: m.group(1) + ' aria-current="page">', p.s, count=1, flags=re.S)


def grafic_anys(sec, lang, any_ref=2026):
    """Barres de tots els anys des del 2007, amb els anteriors agrupats en una sola barra."""
    t3 = T3[lang]
    anys = {}
    for m in re.finditer(r'data-tip="(\d{4}): (\d+) [^"]*"', sec):
        anys[int(m.group(1))] = int(m.group(2))
    if not anys:
        return sec
    darrer = max(anys)
    abans = sum(n for y, n in anys.items() if y < 2007)
    min_abans = min([y for y, n in anys.items() if y < 2007 and n > 0], default=None)
    barres = [("<", abans, min_abans)] + [(y, anys.get(y, 0), y) for y in range(2007, darrer + 1)]
    mx = max(n for _, n, _ in barres) or 1
    lis = []
    for y, n, q in barres:
        vell = y == "<" or any_ref - y >= 5
        tip = t3["doc_tip_abans"].format(n=n) if y == "<" else t3["doc_tip"].format(y=y, n=n)
        x = t3["doc_abans"] if y == "<" else f"’{y % 100:02d}"
        dq = f' data-q="any:{q}" tabindex="0" role="button"' if n and q else ""
        lis.append(f'<li class="{"vell" if vell else ""}{" yc-ab" if y == "<" else ""}"{dq}><span class="yc-b" data-tip="{attr(tip)}">'
                   f'<i style="height:{100 * n / mx:.1f}%"></i></span><span class="yc-x">{x}</span></li>')
    return re.sub(r'(<ul class="yc"[^>]*>).*?(</ul>)', lambda m: m.group(1) + "".join(lis) + m.group(2), sec, count=1, flags=re.S)


def pagina_pl(arrel, lang, s):
    """/ca/projecte-linguistic/ i /es/proyecto-linguistico/: què és, què hi ha de constar, per què es publica
    i el gràfic de l'antiguitat dels documents (abans a la portada)."""
    t, t3 = TXT[lang], T3[lang]
    head = s[: s.find("</head>")]
    m_top = re.search(r'<header class="top">.*?</header>', s, re.S)
    peu_ini = s.find('<footer class="peu"')
    m_main = re.search(r'<main id="main"([^>]*)>', s)
    arrel_rel = re.search(r'data-arrel="([^"]*)"', m_main.group(1)).group(1)
    attrs = m_main.group(1).replace('data-arrel="' + arrel_rel + '"', 'data-arrel="../' + arrel_rel + '"') + " data-pp-abm"
    arr = "../" + arrel_rel
    # el gràfic, per a cada tipus de centre
    grafics = []
    for m in re.finditer(r'<section class="sec" id="antiguitat(?:__(\w+))?"', s):
        ab = m.group(1) or "pub"
        sec = s[m.start():element(s, m.start())]
        nd = re.search(r"(\d[\d.]*) no (?:porten data|llevan fecha)", sec)
        sub = t3["doc_sub"].format(n=nd.group(1) if nd else "0")
        sec = re.sub(r'(<div class="sh">.*?</h2>)<p>.*?</p>', lambda x: x.group(1) + f"<p>{sub}</p>", sec, count=1, flags=re.S)
        sec = re.sub(r'<h2 id="antiguitat-t[^"]*">.*?</h2>', "", sec, count=1, flags=re.S)
        sec = sec.replace('aria-labelledby="antiguitat-t"', 'aria-labelledby="documents-t"').replace('id="antiguitat', 'id="anys')
        sec = grafic_anys(sec, lang)
        sec = sec.replace('<div class="sh">', '<div class="sh pp-sh">', 1)
        grafics.append(f'<div class="v v-{ab}">{sec}</div>')
    cens = re.search(r'<span class="v v-tot">(\d[\d.]*) [^<]*?(\d[\d.]*),', s)
    n_an, n_cens = (int(cens.group(1).replace(".", "")), int(cens.group(2).replace(".", ""))) if cens else (0, 0)
    fmt = lambda n: f"{n:,}".replace(",", ".")
    toc, cos = [], []
    for sid, tit, html_s in PL_COS[lang]:
        toc.append(f'<li><a href="#{sid}">{tit}</a></li>')
        txt = html_s.format(arr=arr, nopub=fmt(n_cens - n_an), cens=fmt(n_cens))
        extra = "".join(grafics) if sid == "documents" else ""
        cos.append(f'<section id="{sid}"><h2 id="{sid}-t">{tit}</h2>{txt}{extra}</section>')
    nav = (f'<nav class="molles" aria-label="breadcrumb"><a href="../">{"Catalunya" if lang == "ca" else "Cataluña"}</a>'
           f'<span class="sep" aria-hidden="true">/</span><span aria-current="page">{t3["pl_t"]}</span></nav>')
    main = (f'<main id="main"{attrs}><div class="wrap estret met pp-pl">{nav}'
            f'<header class="ph-s"><h1>{t3["pl_t"]}</h1><p class="lead">{t3["pl_lead"]}</p></header>'
            f'<nav class="met-toc pp-toc" aria-label="{t3["pl_toc"]}"><p>{t3["pl_toc"]}</p><ol>{"".join(toc)}</ol></nav>'
            f'<article class="prosa">{"".join(cos)}</article></div></main>')
    head = re.sub(r"<title>.*?</title>", f"<title>{t3['pl_t']} · {NOM[lang]}</title>", head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(t3["pl_desc"])}">', head, count=1)
    out = (rel_un_nivell_mes(head) + "</head>\n<body>\n" + rel_un_nivell_mes(s[s.find("<body>") + 6: m_top.start()])
           + rel_un_nivell_mes(m_top.group(0)) + main + rel_un_nivell_mes(s[peu_ini: s.find("</body>")]) + "</body>\n</html>\n")
    out = idioma_a(out, f"ca/{PL['ca']}/", f"es/{PL['es']}/")
    escriu(os.path.join(arrel, lang, PL[lang], "index.html"), out)


def metodologia(p):
    """Coherència amb la pàgina del projecte lingüístic."""
    lang = p.lang
    if p.rel != f"{lang}/metodologia/":
        return
    if lang == "ca":
        p.s = p.s.replace("Tots els centres educatius de Catalunya han de tenir un projecte lingüístic",
                          f'Tots els centres públics i concertats de Catalunya han de tenir un <a href="../{PL[lang]}/">projecte lingüístic</a>')
        p.s = p.s.replace("Els botons «Públics», «Concertats» i «Privats»", "Els botons «Públics», «Concertats» i «Privats» del menú «Centres» de la capçalera")
        p.s = re.sub(r"(Hi ha documents antics\. Cada centre mostra la data del seu\.)",
                     lambda m: m.group(1) + f' <a href="../{PL[lang]}/#documents">De quan són els documents</a>.', p.s, count=1)
    else:
        p.s = p.s.replace("Todos los centros educativos de Cataluña deben tener un proyecto lingüístico",
                          f'Todos los centros públicos y concertados de Cataluña deben tener un <a href="../{PL[lang]}/">proyecto lingüístico</a>')
        p.s = p.s.replace("Los botones «Públicos», «Concertados» y «Privados»", "Los botones «Públicos», «Concertados» y «Privados» del menú «Centros» de la cabecera")
        p.s = re.sub(r"(Hay documentos antiguos\. Cada centro muestra la fecha del suyo\.)",
                     lambda m: m.group(1) + f' <a href="../{PL[lang]}/#documents">De cuándo son los documentos</a>.', p.s, count=1)


def etiquetes_calaix(arrel):
    """Al panell de detall, l'ordre és una opció discreta: «Ordre: barrejat»."""
    for lang, pre in (("ca", "Ordre: "), ("es", "Orden: ")):
        c = os.path.join(arrel, f"dq-{lang}.json")
        if not os.path.exists(c):
            continue
        d = json.loads(llegeix(c))
        l = d.get("l", {})
        if l.get("dq_o_barreja", "").startswith(pre):
            continue
        for k in ("dq_o_barreja", "dq_o_municipi", "dq_o_nom"):
            if k in l:
                l[k] = pre + l[k][:1].lower() + l[k][1:]
        if "cc_g_infantil" in l:
            l["cc_g_infantil"] = l["cc_g_infantil"].replace(" (P3–P5)", "")
        escriu(c, json.dumps(d, ensure_ascii=False, separators=(",", ":")))



# ------------------------------------------------------------------ pàgina de privacitat i arrel


def pagina_privacitat(arrel, lang, plantilla):
    t = TXT[lang]
    s = plantilla
    m = base64.b64encode(CORREU_USUARI[::-1].encode()).decode().rstrip("=")
    cos = PRIV_COS[lang].format(issues=REPO + "/issues/new", m=m)
    s = re.sub(r"<title>.*?</title>", f"<title>{t['priv_t']} · {NOM[lang]}</title>", s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(t["priv_lead"])}">', s, count=1)
    ini = s.find('<div class="wrap estret met">')
    fi = s.find("</main>")
    nou = (f'<div class="wrap estret met"><nav class="molles" aria-label="breadcrumb"><a href="../../{lang}/">{t["inici"]}</a>'
           f'<span class="sep" aria-hidden="true">/</span><span aria-current="page">{t["priv_t"]}</span></nav>'
           f'<header class="ph-s"><h1>{t["priv_t"]}</h1><p class="lead">{t["priv_lead"]}</p></header>'
           f'<article class="prosa">{cos}</article></div>')
    s = s[:ini] + nou + s[fi:]
    # l'idioma: l'enllaç CA/ES de la capçalera apunta a l'altra pàgina de privacitat
    s = idioma_a(s, f"ca/{PRIV['ca']}/", f"es/{PRIV['es']}/")
    s = s.replace('metodologia/" aria-current="page">', 'metodologia/">', 1)
    escriu(os.path.join(arrel, lang, PRIV[lang], "index.html"), s)


def nom_h1(cami):
    s = llegeix(cami)
    m = re.search(r"<h1>(.*?)</h1>", s, re.S)
    return text(m.group(1)) if m else None


def clau_ordre(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def index_municipis(arrel, lang):
    """[(comarca, slug, [(municipi, slug, [(districte, slug)])])] a partir de les carpetes."""
    base = os.path.join(arrel, lang)
    out = []
    for com in sorted(os.listdir(base)):
        dc = os.path.join(base, com)
        if not os.path.isfile(os.path.join(dc, "index.html")) or com in (COM[lang], PRIV[lang], "metodologia"):
            continue
        sc = llegeix(os.path.join(dc, "index.html"))
        eb = re.search(r'<p class="eb">(.*?)</p>', sc, re.S)
        if "noindex" in sc or not eb or text(eb.group(1)).split("·")[0].strip() != "Comarca":
            continue
        muns = []
        for mun in os.listdir(dc):
            dm = os.path.join(dc, mun)
            if not os.path.isfile(os.path.join(dm, "index.html")) or os.path.exists(os.path.join(dm, ".pp-centre")):
                continue
            dists = []
            for d in os.listdir(dm):
                dd = os.path.join(dm, d)
                if os.path.isfile(os.path.join(dd, "index.html")) and not os.path.exists(os.path.join(dd, ".pp-centre")):
                    dists.append((nom_h1(os.path.join(dd, "index.html")), d))
            muns.append((nom_h1(os.path.join(dm, "index.html")), mun, sorted(dists, key=lambda x: clau_ordre(x[0]))))
        out.append((nom_h1(os.path.join(dc, "index.html")), com, sorted(muns, key=lambda x: clau_ordre(x[0]))))
    return sorted(out, key=lambda x: clau_ordre(x[0]))


def pagina_comarques(arrel, lang, s):
    """/ca/comarques/ i /es/comarcas/: la taula de comarques (abans a la portada) i el mapa de municipis."""
    t = TXT[lang]
    head = s[: s.find("</head>")]
    m_top = re.search(r'<header class="top">.*?</header>', s, re.S)
    peu_ini = s.find('<footer class="peu"')
    i = s.find('<section class="sec" id="llocs"')
    llocs = s[i:element(s, i)]
    i = s.find('<div class="abast-n">')
    abast = s[i:element(s, i)] if i != -1 else ""
    m_main = re.search(r'<main id="main"([^>]*)>', s)
    arrel_rel = re.search(r'data-arrel="([^"]*)"', m_main.group(1)).group(1)
    attrs = m_main.group(1).replace('data-arrel="' + arrel_rel + '"', 'data-arrel="../' + arrel_rel + '"')
    blocs = []
    for nc, sc, muns in index_municipis(arrel, lang):
        items = []
        for nm, sm, dists in muns:
            li = f'<a href="../{sc}/{sm}/">{html.escape(nm)}</a>'
            if dists:
                li += ' <span class="pp-dist">(' + " · ".join(f'<a href="../{sc}/{sm}/{sd}/">{html.escape(nd)}</a>' for nd, sd in dists) + ")</span>"
            items.append(f"<li>{li}</li>")
        blocs.append(f'<div class="pp-com"><h3><a href="../{sc}/">{html.escape(nc)}</a> <span>{len(muns)}</span></h3><ul>{"".join(items)}</ul></div>')
    municipis = (f'<section class="sec" id="municipis" aria-labelledby="municipis-t"><div class="sh"><h2 id="municipis-t">{t["mun_t"]}</h2>'
                 f'<p>{t["mun_p"]}</p></div><div class="pp-coms">{"".join(blocs)}</div></section>')
    nav = (f'<nav class="molles" aria-label="breadcrumb"><a href="../">{"Catalunya" if lang == "ca" else "Cataluña"}</a>'
           f'<span class="sep" aria-hidden="true">/</span><span aria-current="page">{t["com_t"]}</span></nav>')
    cos = (f'<main id="main"{attrs}><div class="wrap pp-comarques">{nav}'
           f'<header class="ph-s"><h1>{t["com_t"]}</h1><p class="lead">{t["com_lead"]}</p>{rel_un_nivell_mes(abast)}</header>'
           f'{rel_un_nivell_mes(llocs)}{municipis}</div></main>')
    head = re.sub(r"<title>.*?</title>", f"<title>{t['com_t']} · {NOM[lang]}</title>", head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(t["com_desc"])}">', head, count=1)
    out = (rel_un_nivell_mes(head) + "</head>\n<body>\n" + rel_un_nivell_mes(s[s.find("<body>") + 6: m_top.start()])
           + rel_un_nivell_mes(m_top.group(0)) + cos + rel_un_nivell_mes(s[peu_ini: s.find("</body>")]) + "</body>\n</html>\n")
    out = idioma_a(out, f"ca/{COM['ca']}/", f"es/{COM['es']}/")
    escriu(os.path.join(arrel, lang, COM[lang], "index.html"), out)


def arrel_index(arrel, v_css):
    s = llegeix(os.path.join(arrel, "index.html"))
    if MARCA in s:
        return
    css = re.search(r'href="static/estil\.css\?v=([^"]*)"', s).group(1)
    nou = f"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Observatori Lingüístic</title>
<meta name="description" content="Quines llengües s'ensenyen a cada escola i institut de Catalunya, curs a curs, segons el seu projecte lingüístic. Qué lenguas se enseñan en cada escuela e instituto de Cataluña.">{MARCA}
<link rel="canonical" href="{BASE}/">{alternates("ca/", "es/", "")}
<meta property="og:type" content="website"><meta property="og:title" content="Observatori Lingüístic Escolar"><meta property="og:url" content="{BASE}/">
<meta property="og:description" content="Quines llengües s'ensenyen a cada escola i institut de Catalunya, curs a curs, segons el seu projecte lingüístic.">
<meta property="og:image" content="{BASE}/static/og-ca.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="static/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="static/estil.css?v={css}">
</head>
<body>
<main class="tria"><svg class="logo" viewBox="0 0 28 28" aria-hidden="true" width="56" height="56"><rect x="2" y="3" width="24" height="5" rx="1.5" fill="#123a73"/><rect x="10" y="10" width="16" height="5" rx="1.5" fill="#4d8de0"/><rect x="7" y="17" width="19" height="5" rx="1.5" fill="#2763b8"/></svg><h1>Observatori Lingüístic</h1>
<p lang="ca">Quines llengües s'ensenyen a cada escola i institut de Catalunya, curs a curs de P3 a batxillerat, segons el projecte lingüístic que publica el mateix centre.</p>
<p lang="es">Qué lenguas se enseñan en cada escuela e instituto de Cataluña, curso a curso de P3 a bachillerato, según el proyecto lingüístico que publica el propio centro.</p>
<p class="tria-l"><a href="ca/" lang="ca" hreflang="ca" data-llengua="ca">Català</a><a href="es/" lang="es" hreflang="es" data-llengua="es">Castellano</a></p></main><script>(function(){{var l;try{{l=localStorage.getItem("llengua")}}catch(x){{}}if(!l){{var n=(navigator.languages||[navigator.language||""]).join(",").toLowerCase();l=/(^|,)ca/.test(n)?"ca":"es"}}location.replace(l==="ca"?"ca/":"es/")}})();</script>
</body>
</html>
"""
    escriu(os.path.join(arrel, "index.html"), marca(nou, "ca"))


def pagina_404(arrel):
    c = os.path.join(arrel, "404.html")
    s = llegeix(c)
    if MARCA in s:
        return
    s = s.replace("<title>", f'<meta name="robots" content="noindex">{MARCA}<title>', 1)
    s = marca(s, "ca")
    escriu(c, s)


# ------------------------------------------------------------------ sitemap, robots, capçaleres HTTP


def sitemap(arrel, parelles, data):
    linies = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for rel_ca, rel_es in sorted(parelles):
        xdef = "" if rel_ca == "ca/" else rel_ca
        alt = (f'<xhtml:link rel="alternate" hreflang="ca" href="{url_de(rel_ca)}"/>'
               f'<xhtml:link rel="alternate" hreflang="es" href="{url_de(rel_es)}"/>'
               f'<xhtml:link rel="alternate" hreflang="x-default" href="{url_de(xdef)}"/>')
        for r in (rel_ca, rel_es):
            linies.append(f"<url><loc>{url_de(r)}</loc><lastmod>{data}</lastmod>{alt}</url>")
    linies.append("</urlset>")
    escriu(os.path.join(arrel, "sitemap.xml"), "\n".join(linies) + "\n")
    escriu(os.path.join(arrel, "robots.txt"),
           "User-agent: *\nAllow: /\n\nSitemap: " + BASE + "/sitemap.xml\n")


def capcaleres_http(arrel):
    c = os.path.join(arrel, "_headers")
    s = llegeix(c) if os.path.exists(c) else ""
    if "# pp" in s:
        return
    s = s.rstrip("\n") + """
# pp: HTML a la memòria cau de Cloudflare i del navegador (curta, amb revalidació en segon pla)
/ca/*
  Cache-Control: public, max-age=300, stale-while-revalidate=86400
/es/*
  Cache-Control: public, max-age=300, stale-while-revalidate=86400
/sitemap.xml
  Cache-Control: public, max-age=3600
"""
    escriu(c, s)


# ------------------------------------------------------------------ principal


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    arrel = os.path.abspath(sys.argv[1])
    st = os.path.join(arrel, "static")
    for f in ("pp.js", "pp.css", "og-ca.png", "og-es.png"):
        shutil.copyfile(os.path.join(AQUI, "assets", f), os.path.join(st, f))
    v_css = hashlib.md5(open(os.path.join(st, "pp.css"), "rb").read()).hexdigest()[:10]
    v_js = hashlib.md5(open(os.path.join(st, "pp.js"), "rb").read()).hexdigest()[:10]

    # pàgines existents
    rels = []
    for lang in ("ca", "es"):
        for d, _, fs in os.walk(os.path.join(arrel, lang)):
            if "index.html" in fs and not os.path.exists(os.path.join(d, ".pp-centre")):
                rels.append(os.path.relpath(d, arrel).replace(os.sep, "/") + "/")
    pagines = [Pagina(arrel, r) for r in sorted(rels)]
    pendents = [p for p in pagines if MARCA not in p.s]
    if not pendents:
        print("Ja estava processada.")
    data = re.search(r'data-v="[^"]*-(\d{4}-\d{2}-\d{2})"', pagines[0].s).group(1)

    # privacitat (a partir de la pàgina de metodologia, abans de processar-la)
    pagines = [p for p in pagines if p.rel not in (f"{p.lang}/{PRIV[p.lang]}/", f"{p.lang}/{COM[p.lang]}/", f"{p.lang}/{PL[p.lang]}/")]
    filtre_tpl = {}
    for p in pagines:
        if p.rel == f"{p.lang}/":
            i = p.s.find('<div class="filtre filtre-s"')
            if i == -1:
                i = p.s.find('<div class="filtre pp-abf"')
            filtre_tpl[p.lang] = p.s[i:element(p.s, i)].replace("filtre pp-abf", "filtre filtre-s") if i != -1 else ""
    etiquetes_calaix(arrel)
    DQ = {}
    for lg in ("ca", "es"):
        c = os.path.join(arrel, f"dq-{lg}.json")
        DQ[lg] = json.loads(llegeix(c)) if os.path.exists(c) else None
    pendents = [p for p in pendents if p in pagines]
    for lang in ("ca", "es"):
        met = next(p for p in pagines if p.rel == f"{lang}/metodologia/")
        inici = next(p for p in pagines if p.rel == f"{lang}/")
        rels_noves = []
        if MARCA not in met.s:
            pagina_privacitat(arrel, lang, met.s)
            rels_noves.append(f"{lang}/{PRIV[lang]}/")
        if MARCA not in inici.s:
            pagina_comarques(arrel, lang, inici.s)
            rels_noves.append(f"{lang}/{COM[lang]}/")
            pagina_pl(arrel, lang, inici.s)
            rels_noves.append(f"{lang}/{PL[lang]}/")
        for r in rels_noves:
            pagines.append(Pagina(arrel, r))
            pendents.append(pagines[-1])

    # pàgines de centre (a partir de les pàgines dels llocs encara sense processar)
    slugs, centres = pagines_de_centre(arrel, [p for p in pendents if "data-pp-centre" not in p.s])
    noves = []
    for rel_ca, rel_es in centres.items():
        for r in (rel_ca, rel_es):
            if os.path.exists(os.path.join(arrel, r, "index.html")):
                noves.append(Pagina(arrel, r))
    for p in pendents:
        if '<article class="fx' in p.s and "data-pp-centre" not in p.s:
            enllaca_fitxes(p, slugs)

    # parelles ca/es
    def parella(rel):
        lang, resta = rel.split("/", 1)
        if resta == f"{PRIV[lang]}/":
            return f"ca/{PRIV['ca']}/", f"es/{PRIV['es']}/"
        if resta == f"{COM[lang]}/":
            return f"ca/{COM['ca']}/", f"es/{COM['es']}/"
        if resta == f"{PL[lang]}/":
            return f"ca/{PL['ca']}/", f"es/{PL['es']}/"
        return "ca/" + resta, "es/" + resta
    totes = pagines + noves
    existeix = {p.rel for p in totes}
    n_var = 0
    for p in pendents + noves:
        if MARCA in p.s or '<main id="main"' not in p.s:
            if MARCA not in p.s:
                p.s = marca(p.s, p.lang)
                p.desa()
            continue
        rc, re_ = parella(p.rel)
        if rc not in existeix or re_ not in existeix:
            print("sense parella:", p.rel)
        if "noindex" not in p.s:
            millora_titols(p)
        navegacio(p)
        nav_pl(p)
        reordena(p)
        llengues_oficials(p)
        alumnat_pestanyes(p)
        taula_llocs(p, DQ.get(p.lang))
        capcalera_pagina(p)
        menu_abast(p, filtre_tpl)
        idioma_fora(p)
        seccions_a_capcalera(p)
        metodologia(p)
        es_cites(p)
        n_var += treu_variants(p)
        peu3(p)
        capcalera(p, rc, re_, data)
        recursos(p, v_css, v_js)
        p.s = marca(p.s, p.lang)
        p.desa()

    totes, existeix = [], set()
    for lang in ("ca", "es"):
        for d, _, fs in os.walk(os.path.join(arrel, lang)):
            if "index.html" in fs:
                q = Pagina(arrel, os.path.relpath(d, arrel).replace(os.sep, "/") + "/")
                totes.append(q)
                existeix.add(q.rel)
    parelles = set()
    for p in totes:
        if "noindex" in p.s:
            continue
        rc, re_ = parella(p.rel)
        if rc in existeix and re_ in existeix:
            parelles.add((rc, re_))
    sitemap(arrel, parelles, data)
    arrel_index(arrel, v_css)
    pagina_404(arrel)
    capcaleres_http(arrel)
    print(f"Pàgines processades: {len(pendents) + len(noves)} · pàgines de centre: {len(noves)} · "
          f"variants mogudes a JSON: {n_var} · URL al sitemap: {2 * len(parelles)}")


if __name__ == "__main__":
    main()
