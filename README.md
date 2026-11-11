# Observatori Lingüístic · Web

La web estàtica de l'Observatori Lingüístic: quines llengües s'ensenyen a
cada escola i institut de Catalunya, curs a curs de P3 a 2n de batxillerat, segons
el projecte lingüístic que publica el mateix centre. En català i en castellà.

*La web estática del Observatori Lingüístic: qué lenguas se enseñan en
cada escuela e instituto de Cataluña, curso a curso de P3 a 2.º de bachillerato,
según el proyecto lingüístico que publica el propio centro.*

## Contingut

    index.html, 404.html, _headers    la portada, la pàgina d'error i les capçaleres HTTP
    ca/, es/                          les pàgines, en català i en castellà
    cerca.json                        l'índex del cercador
    dq-ca.json, dq-es.json            les dades que es mostren en clicar una xifra
    p/<codi>.json                     les cites literals de cada centre analitzat
    static/                           CSS, JavaScript, icona i tipografies
    sitemap.xml, robots.txt           per als cercadors
    postproces/                       el post-procés que s'aplica a la web generada

Els documents originals dels centres són al repositori
[observatori-linguistic-documents](https://github.com/Observatori-Linguistic/observatori-linguistic-documents).
La metodologia és a la pàgina «Com ho mesurem» («Cómo lo medimos») de la web.

## Llicències

- Dades (els fitxers JSON i les xifres i textos de les pàgines): Creative Commons
  Reconeixement 4.0 Internacional (CC BY 4.0). Vegeu `LICENSE-DADES.md`.
- JavaScript i CSS: MIT. Vegeu `LICENSE`.
- Tipografies (`static/fonts/`): SIL Open Font License, amb la llicència al costat.

## Post-procés

Després de generar la web, cal passar-hi `postproces/postproces.py` (Python 3, sense
dependències): afegeix les etiquetes per als cercadors i les xarxes, el sitemap, les
pàgines de cada centre, el peu i la càrrega a demanda de les xifres
de concertats i privats.

    python3 postproces/postproces.py .
