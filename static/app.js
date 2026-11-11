/* Observatori Lingüístic Escolar: cercador, interruptor públics/tots, rètols,
   gràfic curs a curs, taules ordenables. Sense dependències. Tot és opcional:
   sense JavaScript la web es llegeix sencera, amb les xifres dels centres públics. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var main = document.querySelector("main[data-arrel]");
  var arrel = main ? main.getAttribute("data-arrel") : "";
  var lang = main ? main.getAttribute("data-lang") : "es";

  function desa(k, v) { try { localStorage.setItem(k, v); } catch (x) {} }

  // ---- idioma preferit
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a[data-llengua]");
    if (a) desa("llengua", a.getAttribute("data-llengua"));
  });

  // ---- abast: quins tipus de centre compten (públics d'entrada; concertats i privats a voluntat, mai cap)
  var ABASTS = ["pub", "con", "pri", "pc", "pp", "cp", "tot"];
  var TIPUS_AB = { pub: [""], con: ["c"], pri: ["p"], pc: ["", "c"], pp: ["", "p"], cp: ["c", "p"], tot: ["", "c", "p"] };
  var CLAU = { "pub": "pub", "con": "con", "pri": "pri", "pub,con": "pc", "pub,pri": "pp", "con,pri": "cp", "pub,con,pri": "tot" };
  var DE_AB = { pub: ["pub"], con: ["con"], pri: ["pri"], pc: ["pub", "con"], pp: ["pub", "pri"], cp: ["con", "pri"], tot: ["pub", "con", "pri"] };
  function abActual() {
    for (var i = 1; i < ABASTS.length; i++) if (doc.classList.contains("ab-" + ABASTS[i])) return ABASTS[i];
    return "pub";
  }
  // un registre del panell (r.ti: «c» concertat, «p» privat, res si és públic) entra a l'abast?
  function dins(r, ab) { return TIPUS_AB[ab || "pub"].indexOf(r.ti || "") !== -1; }
  var botons = Array.prototype.slice.call(document.querySelectorAll("[data-tipus]"));
  function pinta_botons() {
    var on = DE_AB[abActual()];
    botons.forEach(function (b) { b.setAttribute("aria-pressed", on.indexOf(b.getAttribute("data-tipus")) !== -1 ? "true" : "false"); });
  }
  function posa(ab) {
    if (ABASTS.indexOf(ab) === -1) ab = "pub";
    var y = window.scrollY;
    ABASTS.forEach(function (x) { doc.classList.toggle("ab-" + x, x === ab && x !== "pub"); });
    pinta_botons();
    desa("abast", ab);
    window.scrollTo(0, y);
  }
  botons.forEach(function (b) {
    b.addEventListener("click", function () {
      var on = DE_AB[abActual()].slice(), k = b.getAttribute("data-tipus"), i = on.indexOf(k);
      if (i === -1) on.push(k);
      else if (on.length > 1) on.splice(i, 1);
      else { b.classList.add("ft-no"); setTimeout(function () { b.classList.remove("ft-no"); }, 400); return; }   // mai cap
      on.sort(function (a, c) { return ["pub", "con", "pri"].indexOf(a) - ["pub", "con", "pri"].indexOf(c); });
      posa(CLAU[on.join(",")]);
    });
  });
  pinta_botons();
  // amagat per l'abast triat?
  function amagat(el) { for (var x = el; x && x !== document.body; x = x.parentElement) { if (getComputedStyle(x).display === "none") return true; } return false; }
  // l'element visible d'un id: el mateix, o la seva còpia d'una altra versió («id__abast»)
  function visible(id) {
    var el = document.getElementById(id);
    if (el && !amagat(el)) return el;
    var cands = document.querySelectorAll('[id^="' + id.replace(/"/g, "") + '__"]');
    for (var i = 0; i < cands.length; i++) if (!amagat(cands[i])) return cands[i];
    return null;
  }
  function ves_a(id, suau) {
    var el = visible(id);
    if (!el) {
      // un centre que l'abast triat amaga: s'ensenyen tots
      var crua = document.getElementById(id);
      if (!crua) return false;
      posa("tot");
      el = crua;
    }
    el.scrollIntoView({ behavior: suau ? "smooth" : "auto", block: "start" });
    return true;
  }
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest('a[href^="#"]');
    if (!a || a.hasAttribute("data-q")) return;
    var id = decodeURIComponent(a.getAttribute("href").slice(1));
    if (!id) return;
    var el = document.getElementById(id);
    if (el && !amagat(el)) return;            // el comportament normal ja funciona
    if (ves_a(id, true)) { ev.preventDefault(); history.pushState(null, "", "#" + id); }
  });
  function revela() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var el = document.getElementById(id);
    if (el && !amagat(el)) return;
    setTimeout(function () { ves_a(id, false); }, 30);
  }
  revela();
  window.addEventListener("hashchange", revela);

  // ---- rètols emergents
  var tip = null;
  function mostra(el) {
    var text = el.getAttribute("data-tip-" + abActual()) || el.getAttribute("data-tip");
    if (!text) return;
    if (!tip) { tip = document.createElement("div"); tip.id = "tip"; tip.setAttribute("role", "tooltip"); document.body.appendChild(tip); }
    tip.textContent = text;
    tip.hidden = false;
    var r = el.getBoundingClientRect(), t = tip.getBoundingClientRect();
    var left = Math.min(Math.max(8, r.left + r.width / 2 - t.width / 2), window.innerWidth - t.width - 8);
    var top = r.top - t.height - 10;
    if (top < 8) top = r.bottom + 10;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }
  function amaga() { if (tip) tip.hidden = true; }
  var actiu = null;
  ["pointerover", "pointerdown"].forEach(function (tipus) {
    document.addEventListener(tipus, function (ev) {
      var el = ev.target.closest && ev.target.closest("[data-tip]");
      if (el) mostra(el); else amaga();
      // gràfic curs a curs: marca el curs a tots els panells
      var c = ev.target.closest && ev.target.closest("[data-hl] [data-c]");
      if (actiu && (!c || actiu.f !== c.closest("[data-hl]") || actiu.c !== c.getAttribute("data-c"))) {
        actiu.els.forEach(function (x) { x.classList.remove("on"); });
        actiu = null;
      }
      if (c && !actiu) {
        var f = c.closest("[data-hl]"), k = c.getAttribute("data-c");
        var els = Array.prototype.slice.call(f.querySelectorAll('[data-c="' + k + '"]'));
        els.forEach(function (x) { x.classList.add("on"); });
        actiu = { f: f, c: k, els: els };
      }
    });
  });
  window.addEventListener("scroll", amaga, { passive: true });

  // ---- cara a cara: tots els centres o segons la llengua de l'alumnat
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest("[data-cc]");
    if (!b) return;
    var p = b.closest(".panell");
    p.querySelectorAll("[data-cc]").forEach(function (x) { x.setAttribute("aria-selected", x === b ? "true" : "false"); });
    p.querySelectorAll("[data-cc-v]").forEach(function (v) { v.hidden = v.getAttribute("data-cc-v") !== b.getAttribute("data-cc"); });
  });

  // ---- llistes llargues
  document.querySelectorAll("[data-desplega]").forEach(function (b) {
    b.addEventListener("click", function () {
      var l = b.previousElementSibling;
      if (l) l.classList.add("obert");
      b.hidden = true;
    });
  });

  // ---- taules ordenables
  document.querySelectorAll("[data-taula]").forEach(function (taula) {
    var cos = taula.tBodies[0];
    taula.querySelectorAll("[data-ordena]").forEach(function (b) {
      b.addEventListener("click", function () {
        var k = +b.getAttribute("data-ordena");
        var dir = b.getAttribute("data-dir") === "desc" ? "asc" : (k === 0 && !b.getAttribute("data-dir") ? "asc" : "desc");
        if (k === 0 && b.getAttribute("data-dir") === "asc") dir = "desc";
        taula.querySelectorAll("[data-ordena]").forEach(function (x) { x.removeAttribute("data-dir"); });
        b.setAttribute("data-dir", dir);
        var files = Array.prototype.slice.call(cos.rows);
        files.sort(function (a, c) {
          var x = a.cells[k].getAttribute("data-v"), y = c.cells[k].getAttribute("data-v");
          var r = k === 0 ? x.localeCompare(y) : (+x) - (+y);
          return dir === "asc" ? r : -r;
        });
        files.forEach(function (f) { cos.appendChild(f); });
      });
    });
  });

  // ---- subnavegació: marca la secció visible (també a les còpies de cada tipus de centre, «id__ab»)
  var sub = document.querySelector(".subnav");
  var sna = sub && sub.querySelector(".sn-a");
  function vores() {           // ombra als costats quan hi ha més enllaços amagats
    if (!sna) return;
    var max = sna.scrollWidth - sna.clientWidth;
    sna.classList.toggle("mes-d", max > 2 && sna.scrollLeft < max - 2);
    sna.classList.toggle("mes-e", sna.scrollLeft > 2);
  }
  if (sna) {
    sna.addEventListener("scroll", vores, { passive: true });
    window.addEventListener("resize", vores);
    vores();
  }
  if (sub && "IntersectionObserver" in window) {
    var enllacos = {};
    sub.querySelectorAll("a[href^='#']").forEach(function (a) { enllacos[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entrades) {
      entrades.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = enllacos[en.target.id.split("__")[0]];
        if (!a || a.classList.contains("on")) return;
        sub.querySelectorAll("a.on").forEach(function (x) { x.classList.remove("on"); });
        a.classList.add("on");
        if (sna && (a.offsetLeft < sna.scrollLeft || a.offsetLeft + a.offsetWidth > sna.scrollLeft + sna.clientWidth)) {
          sna.scrollTo({ left: Math.max(0, a.offsetLeft - 24), behavior: "smooth" });
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(enllacos).forEach(function (id) {
      document.querySelectorAll('[id="' + id + '"],[id^="' + id + '__"]').forEach(function (s) { obs.observe(s); });
    });
  }

  // ---- detall de cada xifra: un clic a una marca obre els centres que hi compten i les seves cites
  var prev = main && main.hasAttribute("data-prev");
  var versio = main ? main.getAttribute("data-v") : "";
  var DQ = null, DQcarrega = null, proves = {};
  var LL4 = ["ca", "es", "en", "altres"];
  var LROL = { V: "vehicular", M: "materia", A: "asignatura", O: "optativa", C: "ocasional", N: "nada", X: "no_consta" };
  var LCOM = { E: "escrit", S: "part", P: "peticio", O: "oral", T: "traduccio", N: "no", X: "nc" };
  function carregaDQ() {
    if (DQ) return Promise.resolve(DQ);
    if (!DQcarrega) {
      DQcarrega = fetch(arrel + "dq-" + lang + ".json?v=" + versio).then(function (r) {
        if (!r.ok) throw new Error(r.status); return r.json();
      }).then(function (d) { DQ = d; return d; }, function (err) { DQcarrega = null; throw err; });
    }
    return DQcarrega;
  }
  function prova(k) {
    if (!proves[k]) {
      proves[k] = fetch(arrel + "p/" + k + ".json?v=" + versio).then(function (r) {
        if (!r.ok) throw new Error(r.status); return r.json();
      }).catch(function (err) { delete proves[k]; throw err; });
    }
    return proves[k];
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function fmt(s, o) { return String(s).replace(/\{(\w+)\}/g, function (_, k) { return o[k] != null ? o[k] : ""; }); }
  function pc(v, n) {
    if (!n) return "—";
    var p = 100 * v / n;
    if (p > 0 && p < 1) return "<1\u202f%";
    if (p > 99 && p < 100) return ">99\u202f%";
    return Math.round(p) + "\u202f%";
  }
  function normalDQ(s) {
    return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/l·l/g, "ll").replace(/[^a-z0-9]+/g, " ").trim();
  }
  function rang(a, b) { var o = []; for (var i = a; i <= b; i++) o.push(i); return o; }
  function treu(s) { return String(s || "").replace("{p} ", "").replace("{p}", "").trim(); }
  function cap1(s) { s = String(s || ""); return s.charAt(0).toUpperCase() + s.slice(1); }

  // les cites que proven cada pregunta
  function citesLlengua(l, sec) {
    return function (p) {
      var q = p.q || {}, out = [];
      var k = l + (sec ? "_s" : ""), alt = l + (sec ? "" : "_s");
      var txt = q[k] || q[alt];
      if (txt) out.push({ c: DQ.l.noms[l] + (q[k] ? "" : ""), t: txt });
      return out;
    };
  }
  function citesMateries(l, cursos, area) {
    return function (p) {
      var out = [];
      (p.mt || []).forEach(function (m) {
        if (m[0] !== l || (area && m[1] !== area)) return;
        if (cursos && !(m[3] || []).some(function (i) { return cursos.indexOf(i) !== -1; })) return;
        out.push({ c: DQ.l.noms[l] + " · " + (DQ.l["ar_" + m[1]] || m[2]), t: m[4] });
      });
      return out;
    };
  }
  function citesTracte(filtre) {
    return function (p) {
      return (p.td || []).filter(filtre).map(function (x) {
        return { c: DQ.l["tamb_" + x[0]] + (x[1].length ? " · " + x[1].map(function (l) { return DQ.l.codis[l] || l; }).join(" ") : ""),
                 f: (x[2] || {})[lang], t: x[3] };
      });
    };
  }

  var FILTRE = null;     // «a=es»: només els centres amb aquesta llengua majoritària de l'alumnat
  function resol(qq, L, tot, curs) {
    var l = DQ.l, parts = qq.split(":");
    var tipus = parts[0];
    var fa = FILTRE && /^a=/.test(FILTRE) ? FILTRE.slice(2) : null;
    var base0 = DQ.c.filter(function (r) {
      return dins(r, tot) &&
        (L === "" || r.u === L || r.u.indexOf(L + "/") === 0) && (!fa || (r.a || "no_consta") === fa);
    });
    var R = { q: qq };
    function grups(defs, base) {
      R.base = base;
      R.grups = defs.map(function (d) {
        return { k: d[0], lab: d[1], cls: d[2] || "", cs: base.filter(d[3]) };
      });
    }
    if (tipus === "ind") {
      var k = parts[1];
      // els indicadors d'un sol curs: el desglossament del curs, amb el grup que compta l'indicador
      var simple = { ca_p3: ["ca", 0, "V", "k_ca_p3"], es_p3: ["es", 0, "VMA", "k_es_p3"], en_p3: ["en", 0, "VMA", "k_en_p3"],
                     es_1: ["es", 3, "VMA", "k_es_1"] }[k];
      if (simple) return resol("curs:" + simple[0] + ":" + simple[1], L, tot, null, simple);
      var def = {
        es_materia_pri: ["es", "k_es_mat", "P", rang(3, 8), "VM", false],
        en_materia_pri: ["en", "k_en_mat", "P", rang(3, 8), "VM", false],
        ca_eso: ["ca", "k_ca_eso", "E", rang(9, 12), "V", true],
        ca_inf: ["ca", "k_ca_inf", "I", rang(0, 2), "V", true],
        es_inf: ["es", "k_es_inf", "I", rang(0, 2), "VMA", false],
        en_inf: ["en", "k_en_inf", "I", rang(0, 2), "VMA", false],
        es_materia_eso: ["es", "k_es_mat_eso", "E", rang(9, 12), "VM", false],
        en_materia_eso: ["en", "k_en_mat_eso", "E", rang(9, 12), "VM", false],
        altres_eso: ["altres", "k_alt_eso", "E", rang(9, 12), "VMAO", false]
      }[k];
      if (!def) return null;
      var ll = def[0], cursos = def[3];
      var fa = function (r) {
        var f = function (i) { return def[4].indexOf(r.r[ll][i]) !== -1; };
        return def[5] ? cursos.every(f) : cursos.some(f);
      };
      R.titol = l.noms[ll] + " · " + treu(l[def[1]]);
      grups([["si", l.dq_si, "g-si", fa], ["no", l.dq_no, "g-no", function (r) { return !fa(r); }]],
            base0.filter(function (r) { return r.e.indexOf(def[2]) !== -1; }));
      R.sel = "si";
      var mat = def[4] === "VM" && ll !== "altres";
      var cq = citesLlengua(ll, def[2] === "E" || def[2] === "B"), cm = citesMateries(ll, cursos);
      R.ev = mat ? function (p) { return cm(p).concat(cq(p)); } : cq;
      R.cita = function (r) { return "#c-" + r.k + "-q-" + ll + (def[2] === "E" ? "-s" : ""); };
      return R;
    }
    if (tipus === "curs") {
      var ll2 = parts[1], i = curs != null ? curs : +String(parts[2]).split("-")[0];
      var base = base0.filter(function (r) { return r.r[ll2] && r.r[ll2][i] !== "-"; });
      R.titol = l.noms[ll2] + " · " + l.cursos_l[i];
      R.curs = { l: ll2, i: i };
      grups(DQ.rols.map(function (rol) {
        var lt = Object.keys(LROL).filter(function (x) { return LROL[x] === rol; })[0];
        return [rol, l["s_" + rol], "r-" + rol, function (r) { return r.r[ll2] && r.r[ll2][i] === lt; }];
      }), base);
      var ext = arguments[4];
      if (ext && ext[2].length > 1) {
        R.grups.unshift({ k: "ind", lab: cap1(treu(l[ext[3]])), cls: "g-si", cs: base.filter(function (r) { return ext[2].indexOf(r.r[ll2][i]) !== -1; }) });
        R.solapa = true;
      }
      R.sel = ext ? (ext[2].length > 1 ? "ind" : LROL[ext[2]]) : null;
      R.ev = citesLlengua(ll2, i >= 9);
      R.cita = function (r) { return "#c-" + r.k + "-q-" + ll2 + (i >= 9 ? "-s" : ""); };
      return R;
    }
    if (tipus === "com") {
      var j = LL4.indexOf(parts[1]);
      R.titol = l.noms[parts[1]] + " · " + l.com_tit;
      grups(DQ.com.map(function (k) {
        return [k, l["cf_" + k], "cf-" + k, function (r) { return LCOM[r.f.charAt(j)] === k; }];
      }), base0);
      R.sel = parts[2];
      R.ev = function (p) { return p.com ? [{ c: l.com_tit, t: p.com }] : []; };
      R.cita = function (r) { return "#c-" + r.k + "-q-com"; };
      return R;
    }
    if (tipus === "mat") {
      var lm = parts[1], g = parts[2], area = parts[3];
      var et = g === "infprim" ? "IP" : "EB", cs = g === "infprim" ? rang(0, 8) : rang(9, 14);
      var base = base0.filter(function (r) { return r.e.split("").some(function (x) { return et.indexOf(x) !== -1; }); });
      var te = function (r) { return ((r.mt || {})[lm] || {})[g] || []; };
      var arees = {};
      base.forEach(function (r) { te(r).forEach(function (a) { arees[a] = (arees[a] || 0) + 1; }); });
      var defs = [["*", l.dq_alguna, "g-si", function (r) { return te(r).length > 0; }]];
      if (area !== "*" && area !== "cap" && !arees[area]) arees[area] = 0;
      Object.keys(arees).sort(function (a, b) { return arees[b] - arees[a]; }).forEach(function (a) {
        defs.push([a, cap1(l["ar_" + a] || a), "g-ar", function (r) { return te(r).indexOf(a) !== -1; }]);
      });
      defs.push(["cap", l.dq_cap_mat, "g-no", function (r) { return te(r).length === 0; }]);
      R.titol = l.noms[lm] + " · " + l["mt_h_" + g];
      grups(defs, base);
      R.sel = area;
      R.solapa = true;
      R.evSel = function (k) { return citesMateries(lm, cs, k === "*" || k === "cap" ? null : k); };
      R.citaSel = function (k) {
        return function (r) {
          var a = k === "*" || k === "cap" ? te(r)[0] : k;
          return a ? "#c-" + r.k + "-q-mt-" + lm + "-" + a : null;
        };
      };
      return R;
    }
    if (tipus === "esp") {
      var dim = parts[1], kk = parts[2], defs2;
      var es = function (r) { return r.es || ["no_consta", [], []]; };
      if (dim === "amb") {
        defs2 = DQ.ambits_espais.map(function (a) { return [a, l["amb_" + a], "g-ar", function (r) { return es(r)[1].indexOf(a) !== -1; }]; });
        defs2.push(["no", l.dq_esp_no, "g-no", function (r) { return es(r)[1].length === 0; }]);
        R.solapa = true;
      } else if (dim === "car") {
        defs2 = DQ.car.map(function (c) { return [c, l["car_" + c], "car-" + c, function (r) { return es(r)[0] === c; }]; });
      } else {
        var lls = {};
        base0.forEach(function (r) { es(r)[2].forEach(function (x) { lls[x] = (lls[x] || 0) + 1; }); });
        defs2 = Object.keys(lls).sort(function (a, b) { return lls[b] - lls[a]; }).map(function (x) {
          return [x, l.noms[x] || x, "g-ar", function (r) { return es(r)[2].indexOf(x) !== -1; }];
        });
        R.solapa = true;
      }
      R.titol = l.esp_tit + " · " + l["esp_h_" + (dim === "amb" ? "ambits" : dim === "car" ? "caracter" : "llengues")];
      grups(defs2, base0);
      R.sel = kk;
      R.ev = function (p) {
        var o = [];
        if (p.esp) o.push({ c: l.esp_tit, f: (p.esp_d || {})[lang], t: p.esp });
        return o;
      };
      R.cita = function (r) { return r.es ? "#c-" + r.k + "-q-esp" : null; };
      return R;
    }
    if (tipus === "td") {
      var base = base0.filter(function (r) { return r.t; });
      var dim2 = parts[1], k3 = parts[2];
      R.titol = l.td_tit;
      if (dim2 === "al") {
        // un àmbit i una llengua: centres amb alguna norma d'aquell àmbit que esmenta la llengua
        var la = parts[3];
        var fa2 = function (x) { return x[0] === k3 && x[1].indexOf(la) !== -1; };
        R.titol = l.noms[la] + " · " + l["tamb_" + k3];
        grups([["si", l.dq_si, "g-si", function (r) { return r.t.some(fa2); }],
               ["no", l.dq_no, "g-no", function (r) { return !r.t.some(fa2); }]], base);
        R.sel = "si";
        R.ev = citesTracte(fa2);
        R.cita = function (r) {
          var j = -1;
          r.t.some(function (x, i) { if (fa2(x)) { j = i; return true; } return false; });
          return j >= 0 ? "#c-" + r.k + "-t-" + j : null;
        };
        return R;
      }
      if (dim2 === "*") {
        grups([["si", l.dq_td_si, "g-si", function (r) { return r.t.length > 0; }],
               ["no", l.dq_td_no, "g-no", function (r) { return r.t.length === 0; }]], base);
        R.sel = "si";
        R.ev = citesTracte(function () { return true; });
      } else if (dim2 === "amb") {
        grups(DQ.ambits_tracte.map(function (a) {
          return [a, l["tamb_" + a], "g-ar", function (r) { return r.t.some(function (x) { return x[0] === a; }); }];
        }), base);
        R.sel = k3; R.solapa = true;
        R.evSel = function (k) { return citesTracte(function (x) { return x[0] === k; }); };
      } else {
        grups(LL4.concat(["oc"]).map(function (x) {
          return [x, l.noms[x], "g-ar", function (r) { return r.t.some(function (y) { return y[1].indexOf(x) !== -1; }); }];
        }), base);
        R.sel = k3; R.solapa = true;
        R.evSel = function (k) { return citesTracte(function (x) { return x[1].indexOf(k) !== -1; }); };
      }
      R.titol += " · " + l[dim2 === "ll" ? "td_h_llengues" : "td_h_ambits"];
      // l'enllaç porta al primer cas del centre que hi compta
      R.citaSel = function (k) {
        return function (r) {
          var j = -1;
          r.t.some(function (x, i) {
            var ok = dim2 === "*" || (dim2 === "amb" ? x[0] === k : x[1].indexOf(k) !== -1);
            if (ok) j = i;
            return ok;
          });
          return j >= 0 ? "#c-" + r.k + "-t-" + j : null;
        };
      };
      return R;
    }
    if (tipus === "any") {
      var base = base0.filter(function (r) { return r.y; });
      R.titol = l.any_tit;
      if (parts[1] === "vells") {
        grups([["vells", l.dq_vells, "g-vell", function (r) { return DQ.any - r.y >= 5; }],
               ["recents", l.dq_recents, "g-si", function (r) { return DQ.any - r.y < 5; }]], base);
        R.sel = "vells";
      } else {
        var anys = {};
        base.forEach(function (r) { anys[r.y] = 1; });
        grups(Object.keys(anys).sort(function (a, b) { return b - a; }).map(function (y) {
          return [y, y, DQ.any - y >= 5 ? "g-vell" : "g-si", function (r) { return String(r.y) === y; }];
        }), base);
        R.sel = parts[1];
      }
      R.ev = function (p) { return p.any && p.any[1] ? [{ c: String(p.any[0]), t: p.any[1] }] : []; };
      return R;
    }
    if (tipus === "espa") {
      // fora de l'aula, un espai: quina llengua hi fixa el document (dades.cat_espai)
      var ae = parts[1];
      var ce = function (r) {
        var es = r.es;
        if (!es || es[1].indexOf(ae) === -1) return "no";
        if (es[0] === "lliure") return "lliure";
        var ll = es[2];
        if (ll.indexOf("es") !== -1) return "es";
        if (ll.length && ll.every(function (x) { return x === "ca" || x === "oc"; })) return es[0] === "norma" ? "ca_norma" : "ca_rec";
        if (ll.indexOf("ca") !== -1) return "ca_altres";
        return ll.length ? "altres" : "no";
      };
      R.titol = l.esp_tit + " · " + l["amb_" + ae];
      grups(["ca_norma", "ca_rec", "ca_altres", "es", "altres", "lliure", "no"].map(function (k) {
        return [k, l["ea_" + k], "ea-" + k, function (r) { return ce(r) === k; }];
      }), base0);
      R.sel = parts[2];
      R.ev = function (p) { return p.esp ? [{ c: l.esp_tit, f: (p.esp_d || {})[lang], t: p.esp }] : []; };
      R.cita = function (r) { return r.es ? "#c-" + r.k + "-q-esp" : null; };
      return R;
    }
    if (tipus === "cc") {
      // català i castellà, cara a cara: la mateixa pregunta per a cada llengua (dades.resposta)
      var kc = parts[1], lc2 = parts[2], j2 = LL4.indexOf(lc2), grupT;
      if (kc === "com") {
        grupT = "families";
        var fc = function (r) { return r.f.charAt(j2); };
        grups([["si", l.cc_c_si, "cc-si", function (r) { return fc(r) === "E"; }],
               ["part", l.cc_c_part, "cc-part", function (r) { return fc(r) === "S"; }],
               ["cond", l.cc_c_cond, "cc-cond", function (r) { return fc(r) === "P"; }],
               ["nc", l.cc_c_nc, "cc-nc", function (r) { return fc(r) === "X"; }],
               ["no", l.dq_cc_no_com, "cc-sw-no", function (r) { return "ESPX".indexOf(fc(r)) === -1; }]], base0);
        R.ev = function (p) { return p.com ? [{ c: l.com_tit, t: p.com }] : []; };
        R.cita = function (r) { return "#c-" + r.k + "-q-com"; };
      } else if (kc === "esp") {
        grupT = "espais";
        var fs = function (r) { return !!r.es && r.es[0] === "norma" && r.es[2].indexOf(lc2) !== -1; };
        grups([["si", l.cc_c_si, "cc-si", fs], ["nc", l.cc_c_nc, "cc-nc", function (r) { return !r.es; }],
               ["no", l.cc_c_no_esp, "cc-sw-no", function (r) { return !!r.es && !fs(r); }]], base0);
        R.ev = function (p) { return p.esp ? [{ c: l.esp_tit, f: (p.esp_d || {})[lang], t: p.esp }] : []; };
        R.cita = function (r) { return r.es ? "#c-" + r.k + "-q-esp" : null; };
      } else {
        // una etapa: el paper de la llengua, del més fort al més feble (dades.categoria_etapa)
        grupT = "aprenentatge";
        var cs2 = DQ.etapes.filter(function (x) { return x[0] === kc; })[0][1];
        var lt2 = { infantil: "I", primaria: "P", eso: "E", batxillerat: "B" }[kc];
        var cat = function (r) {
          var rs = cs2.map(function (i) { return r.r[lc2].charAt(i); });
          var tots3 = function (set) { return rs.every(function (x) { return set.indexOf(x) !== -1; }); };
          var algun3 = function (set) { return rs.some(function (x) { return set.indexOf(x) !== -1; }); };
          if (tots3("V")) return "veh";
          if (algun3("VM")) return "mat";
          if (tots3("A")) return "asig";
          if (algun3("AOC")) return "parcial";
          if (tots3("X")) return "nc";
          return "no";
        };
        var base2 = base0.filter(function (r) {
          return r.e.indexOf(lt2) !== -1 && cs2.some(function (i) {
            return "X-".indexOf(r.r.ca.charAt(i)) === -1 || "X-".indexOf(r.r.es.charAt(i)) === -1;
          });
        });
        var CL = { veh: "r-vehicular", mat: "r-materia", asig: "r-asignatura", parcial: "r-ocasional", nc: "cc-nc", no: "cc-sw-no" };
        grups(["veh", "mat", "asig", "parcial", "nc", "no"].map(function (c) {
          return [c, l[c === "no" ? "cc_c_no_etapa" : "cc_c_" + c], CL[c], function (r) { return cat(r) === c; }];
        }), base2);
        var sec2 = kc === "eso" || kc === "batxillerat";
        R.ev = citesLlengua(lc2, sec2);
        R.cita = function (r) { return "#c-" + r.k + "-q-" + lc2 + (sec2 ? "-s" : ""); };
      }
      R.titol = l.noms[lc2] + " · " + (grupT === "aprenentatge" ? l["cc_g_" + kc] : l["cc_" + kc]);
      R.sel = parts[3] || null;
      return R;
    }
    if (tipus === "alu") {
      R.titol = l.dr_h_alumnat;
      grups(["es", "ca", "ca_es", "altres", "no_consta"].map(function (g) {
        return [g, l["dr_g_" + g], g === "no_consta" ? "g-no" : "g-ar", function (r) { return (r.a || "no_consta") === g; }];
      }), base0);
      R.sel = parts[1];
      R.ev = function (p) { return p.al ? [{ c: l.dq_al, t: p.al }] : []; };
      R.cita = function (r) { return "#c-" + r.k + "-q-al"; };
      return R;
    }
    if (tipus === "drt") {
      // drets lingüístics: les mateixes mesures per a cada llengua oficial
      if (parts[1] === "com") {
        var lc = parts[2], jc = LL4.concat(["oc"]).indexOf(lc), R2;
        if (jc < 4) { R2 = resol("com:" + lc + ":escrit", L, tot); }
        else {
          // l'aranès no té columna pròpia a «f»: es mira a la cita de comunicació (només hi ha l'Aran)
          return null;
        }
        R2.grups.unshift({ k: "ind", lab: l.dq_ind_com, cls: "g-si", cs: R2.base.filter(function (r) { return "EP".indexOf(r.f.charAt(jc)) !== -1; }) });
        R2.sel = "ind";
        return R2;
      }
      if (parts[1] === "vinf") {
        var lv = parts[2];
        var fv = function (r) { return r.r[lv].slice(0, 3) === "VVV"; };
        R.titol = l.noms[lv] + " · " + l.pp_vinf;
        grups([["si", l.dq_si, "g-si", fv], ["no", l.dq_no, "g-no", function (r) { return !fv(r); }]],
              base0.filter(function (r) { return r.r[lv] && r.e.indexOf("I") !== -1; }));
        R.sel = "si";
        R.ev = citesLlengua(lv, false);
        R.cita = function (r) { return "#c-" + r.k + "-q-" + lv; };
        return R;
      }
      if (parts[1] === "inf") {
        var li = parts[2];
        var fi = function (r) { return [0, 1, 2].some(function (i) { return "VMA".indexOf(r.r[li].charAt(i)) !== -1; }); };
        R.titol = l.noms[li] + " · " + l.pp_inf;
        grups([["si", l.dq_si, "g-si", fi], ["no", l.dq_no, "g-no", function (r) { return !fi(r); }]],
              base0.filter(function (r) { return r.r[li] && r.e.indexOf("I") !== -1; }));
        R.sel = "si";
        R.ev = citesLlengua(li, false);
        R.cita = function (r) { return "#c-" + r.k + "-q-" + li; };
        return R;
      }
      if (parts[1] === "norma" || parts[1] === "pati") {
        var ln = parts[2], amb = parts[1] === "pati";
        var pt = function (r) {
          return !!r.es && r.es[0] === "norma" && (!ln || r.es[2].indexOf(ln) !== -1) && (!amb || r.es[1].indexOf("pati") !== -1);
        };
        R.titol = (ln ? l.noms[ln] + " · " : "") + l[amb ? "pp_pati" : "pp_norma"];
        grups([["si", l.dq_si, "g-si", pt], ["no", l.dq_no, "g-no", function (r) { return !pt(r); }]], base0);
        R.sel = "si";
        R.ev = function (p) { return p.esp ? [{ c: l.esp_tit, f: (p.esp_d || {})[lang], t: p.esp }] : []; };
        R.cita = function (r) { return r.es ? "#c-" + r.k + "-q-esp" : null; };
        return R;
      }
      if (parts[1] === "just") {
        var lj = parts[2], jj = function (r) { return (r.j || []).indexOf(lj) !== -1; };
        R.titol = fmt(l.dq_just_tit, { l: l.noms[lj] });
        grups([["si", l.dq_just_si, "g-si", jj], ["no", l.dq_just_no, "g-no", function (r) { return !jj(r); }]], base0);
        R.sel = "si";
        R.ev = function (p) { return (p.j || []).filter(function (x) { return x[0] === lj; }).map(function (x) { return { c: l.noms[lj], t: x[1] }; }); };
        return R;
      }
    }
    return null;
  }

  var calaix = null, origen = null, estat = null, vigia = null;
  function urlFitxa(r, ancora) {
    return arrel + lang + "/" + r.u + "/" + (prev ? "index.html" : "") + (ancora || "#c-" + r.k);
  }
  function crea() {
    var l = DQ.l;
    calaix = document.createElement("div");
    calaix.className = "dq-fons";
    calaix.hidden = true;
    calaix.innerHTML =
      '<aside class="dq-p" role="dialog" aria-modal="true" aria-labelledby="dq-t">' +
      '<header class="dq-h"><div><p class="dq-eb"></p><h2 id="dq-t"></h2><p class="dq-s"></p></div>' +
      '<button type="button" class="dq-x" aria-label="' + esc(l.dq_tancar) + '">×</button></header>' +
      '<div class="dq-nav"></div><ul class="dq-g" role="list"></ul>' +
      '<div class="dq-f"><input type="search" placeholder="' + esc(l.dq_filtre) + '" aria-label="' + esc(l.dq_filtre) + '">' +
      '<select aria-label="' + esc(l.dq_ordre) + '"><option value="barreja">' + esc(l.dq_o_barreja) + '</option>' +
      '<option value="municipi">' + esc(l.dq_o_municipi) + '</option><option value="nom">' + esc(l.dq_o_nom) + '</option></select></div>' +
      '<div class="dq-b"><ol class="dq-l"></ol><button type="button" class="mes-b dq-mes" hidden></button></div></aside>';
    document.body.appendChild(calaix);
    calaix.addEventListener("click", function (ev) { if (ev.target === calaix) tanca(); });
    calaix.querySelector(".dq-x").addEventListener("click", tanca);
    calaix.querySelector(".dq-f input").addEventListener("input", function () { estat.n = 40; llista(); });
    calaix.querySelector(".dq-f select").addEventListener("change", function () { estat.n = 40; llista(); });
    calaix.querySelector(".dq-mes").addEventListener("click", function () { estat.n += 60; llista(); });
    calaix.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") { tanca(); return; }
      if (ev.key !== "Tab") return;
      var f = Array.prototype.slice.call(calaix.querySelectorAll("button:not([hidden]),a[href],input")).filter(function (x) { return x.offsetParent; });
      if (!f.length) return;
      if (ev.shiftKey && document.activeElement === f[0]) { f[f.length - 1].focus(); ev.preventDefault(); }
      else if (!ev.shiftKey && document.activeElement === f[f.length - 1]) { f[0].focus(); ev.preventDefault(); }
    });
    if ("IntersectionObserver" in window) {
      vigia = new IntersectionObserver(function (es) {
        es.forEach(function (en) { if (en.isIntersecting) { vigia.unobserve(en.target); omple(en.target); } });
      }, { root: calaix.querySelector(".dq-b"), rootMargin: "200px 0px" });
    }
  }
  function tanca() {
    if (!calaix || calaix.hidden) return;
    calaix.hidden = true;
    doc.classList.remove("dq-obert");
    if (origen && origen.focus) origen.focus();
  }
  function pinta() {
    var R = estat.R, l = DQ.l, n = R.base.length;
    calaix.querySelector(".dq-eb").textContent = estat.nom;
    calaix.querySelector("#dq-t").textContent = R.titol;
    calaix.querySelector(".dq-s").textContent = fmt(n === 1 ? l.dq_base1 : l.dq_base, { n: n, a: l["dq_ab_" + estat.tot] || "" });
    // navegació curs a curs i entre llengües
    var nav = calaix.querySelector(".dq-nav");
    nav.innerHTML = "";
    if (R.curs) {
      var c = R.curs, html = '<div class="dq-ll" role="group">';
      LL4.forEach(function (x) {
        html += '<button type="button" data-ll="' + x + '" title="' + esc(l.noms[x]) + '" aria-label="' + esc(l.noms[x]) + '" aria-pressed="' + (x === c.l) + '"><span class="xip x-' + x + '"><i>' +
          esc(l.codis[x]) + '</i></span></button>';
      });
      html += '</div><div class="dq-cs" role="group" aria-label="' + esc(l.dq_curs_tria) + '">';
      DQ.etapes.forEach(function (et) {
        var cs = et[1].filter(function (i) { return estat.cursos.indexOf(i) !== -1; });
        if (!cs.length) return;
        html += '<div class="dq-et" style="flex:' + cs.length + '"><span>' + esc(l["et_curt_" + et[0]]) + '</span><div>';
        cs.forEach(function (i) {
          html += '<button type="button" data-ci="' + i + '" aria-pressed="' + (i === c.i) + '" aria-label="' + esc(l.cursos_l[i]) + '">' +
            esc(l.cursos[i]) + '</button>';
        });
        html += '</div></div>';
      });
      nav.innerHTML = html + "</div>";
      nav.querySelectorAll("[data-ll]").forEach(function (b) {
        b.addEventListener("click", function () { obre("curs:" + b.getAttribute("data-ll") + ":" + c.i + (estat.filtre ? "|" + estat.filtre : ""), estat.L, estat.nom); });
      });
      nav.querySelectorAll("[data-ci]").forEach(function (b) {
        b.addEventListener("click", function () { obre("curs:" + c.l + ":" + b.getAttribute("data-ci") + (estat.filtre ? "|" + estat.filtre : ""), estat.L, estat.nom); });
      });
    }
    // grups
    var ul = calaix.querySelector(".dq-g");
    ul.innerHTML = "";
    var maxim = 0;
    R.grups.forEach(function (g) { maxim = Math.max(maxim, g.cs.length); });
    if (!R.sel || !R.grups.some(function (g) { return g.k === R.sel; })) {
      var gran = R.grups.filter(function (g) { return g.cs.length; }).sort(function (a, b) { return b.cs.length - a.cs.length; })[0];
      R.sel = gran ? gran.k : (R.grups[0] && R.grups[0].k);
    }
    R.grups.forEach(function (g) {
      if (!g.cs.length && g.k !== R.sel) return;
      var li = document.createElement("li");
      li.innerHTML = '<button type="button" aria-pressed="' + (g.k === R.sel) + '"><span class="sw ' + esc(g.cls) + '"></span>' +
        '<span class="dq-gl">' + esc(g.lab) + '</span><span class="dq-gt"><i style="width:' + (n ? 100 * g.cs.length / n : 0).toFixed(1) + '%"></i></span>' +
        '<span class="dq-gv"><b>' + pc(g.cs.length, n) + '</b> <small>' + g.cs.length + '</small></span></button>';
      li.firstChild.addEventListener("click", function () { R.sel = g.k; estat.n = 40; pinta(); });
      ul.appendChild(li);
    });
    estat.n = estat.n || 40;
    llista();
  }
  function llista() {
    var R = estat.R, l = DQ.l;
    var g = R.grups.filter(function (x) { return x.k === R.sel; })[0];
    var ol = calaix.querySelector(".dq-l"), mes = calaix.querySelector(".dq-mes");
    var filtre = normalDQ(calaix.querySelector(".dq-f input").value);
    // d'entrada, barrejats (cada vegada que s'obre el panell, un ordre diferent però estable mentre es mira)
    var ordre = calaix.querySelector(".dq-f select").value;
    var cs = (g ? g.cs : []).slice().sort(ordre === "nom" ? function (a, b) { return a.n.localeCompare(b.n); }
      : ordre === "municipi" ? function (a, b) { return a.m.localeCompare(b.m) || a.n.localeCompare(b.n); }
      : function (a, b) { return atzar(a.k) - atzar(b.k); });
    if (filtre) cs = cs.filter(function (r) { return normalDQ(r.n + " " + r.m).indexOf(filtre) !== -1; });
    ol.innerHTML = "";
    if (!cs.length) { ol.innerHTML = '<li class="buit">' + esc(l.dq_cap) + '</li>'; mes.hidden = true; return; }
    var evf = R.evSel ? R.evSel(R.sel) : R.ev;
    var cf = R.citaSel ? R.citaSel(R.sel) : R.cita;
    var mostra = cs.slice(0, estat.n);
    mostra.forEach(function (r) {
      var li = document.createElement("li");
      li.className = "dq-c" + (r.p === 0 ? " dq-priv" : "");
      li.innerHTML = '<div class="dq-ch"><a href="' + esc(urlFitxa(r, cf ? cf(r) : null)) + '">' + esc(r.n) + '</a>' +
        '<span>' + esc(r.m) + (r.p === 0 ? ' · <em>' + esc((r.ti === "c" ? l.dq_concertat : l.dq_privat) || "") + '</em>' : "") + '</span></div>' +
        '<div class="dq-ev"><p class="dq-cr">' + esc(l.dq_carrega) + '</p></div>';
      li._r = r; li._ev = evf;
      ol.appendChild(li);
      if (vigia) vigia.observe(li); else omple(li);
    });
    mes.hidden = cs.length <= estat.n;
    mes.textContent = fmt(l.dq_mes, { n: Math.min(60, cs.length - estat.n) });
  }
  function atzar(k) {
    // un número pseudoaleatori estable per centre i obertura del panell
    var h = estat.llavor ^ 2166136261;
    for (var i = 0; i < k.length; i++) { h ^= k.charCodeAt(i); h = Math.imul(h, 16777619); }
    h ^= h >>> 13; h = Math.imul(h, 1274126177); h ^= h >>> 16;
    return h >>> 0;
  }
  function omple(li) {
    var r = li._r, l = DQ.l, caixa = li.querySelector(".dq-ev");
    prova(r.k).then(function (p) {
      var cites = li._ev ? li._ev(p) : [];
      var html = cites.map(function (x) {
        return '<figure class="dq-q"><figcaption>' + esc(x.c) + '</figcaption>' +
          (x.f ? '<p class="dq-fet">' + esc(x.f) + '</p>' : "") +
          (x.t ? '<blockquote lang="ca">' + esc(x.t) + '</blockquote>' : "") + '</figure>';
      }).join("");
      if (!html) html = '<p class="dq-cr">' + esc(l.dq_sense) + '</p>';
      if (p.doc) html += '<a class="dq-doc" href="' + esc(p.doc) + '" rel="noopener" target="_blank">' + esc(l.dq_doc) + ' ↗</a>';
      caixa.innerHTML = html;
    }).catch(function () { caixa.innerHTML = '<p class="dq-cr">' + esc(l.dq_error) + '</p>'; });
  }
  function obre(qq, L, nom, curs, el) {
    var pf = qq.split("|");
    qq = pf[0];
    carregaDQ().then(function () {
      if (!calaix) crea();
      var tot = abActual();
      FILTRE = pf[1] || null;
      var R = resol(qq, L, tot, curs);
      if (!R) return;
      if (FILTRE && /^a=/.test(FILTRE)) R.titol += " · " + (DQ.l["dr_g_" + FILTRE.slice(2)] || "");
      if (R.solapa && !R.curs) {
        var fix = { "*": 1, cap: 1, no: 1, ind: 1, si: 1 };
        var mobils = R.grups.filter(function (g) { return !fix[g.k]; }).sort(function (a, b) { return b.cs.length - a.cs.length; });
        R.grups = R.grups.filter(function (g) { return fix[g.k] && g.k !== "cap" && g.k !== "no"; }).concat(mobils)
          .concat(R.grups.filter(function (g) { return g.k === "cap" || g.k === "no"; }));
      }
      estat = { R: R, L: L, nom: nom, tot: tot, n: 40, filtre: FILTRE, llavor: (Math.random() * 4294967296) >>> 0 };
      if (R.curs) {
        estat.cursos = [];
        for (var i = 0; i < 15; i++) {
          var b = resol("curs:" + R.curs.l + ":" + i, L, tot);
          if (b.base.length) estat.cursos.push(i);
        }
      }
      calaix.querySelector(".dq-f input").value = "";
      pinta();
      var obert = !calaix.hidden;
      calaix.hidden = false;
      doc.classList.add("dq-obert");
      calaix.querySelector(".dq-b").scrollTop = 0;
      if (!obert) calaix.querySelector(".dq-x").focus();
    }).catch(function () {
      if (el) { el.setAttribute("data-tip", (DQ && DQ.l.dq_error) || "Error"); mostra(el); }
    });
  }
  function activa(el, ev) {
    var qq = el.getAttribute("data-q");
    var scope = el.closest("[data-lloc]");
    var L = el.hasAttribute("data-l") ? el.getAttribute("data-l") : (scope ? scope.getAttribute("data-lloc") : "");
    var nom = scope ? scope.getAttribute("data-lloc-n") : "";
    if (el.hasAttribute("data-l")) {
      var fila = el.closest("tr");
      var th = fila && fila.querySelector("th");
      if (th) nom = th.textContent.trim();
    }
    var curs = null, m = /^curs:\w+:(\d+)-(\d+)$/.exec(qq);
    if (m) {
      var a = +m[1], b = +m[2];
      curs = a;
      var rc = el.getBoundingClientRect();
      if (ev && ev.clientX != null && b > a && rc.width > 0) {
        var f = Math.min(0.999, Math.max(0, (ev.clientX - rc.left) / rc.width));
        curs = a + Math.floor(f * (b - a + 1));
      }
    }
    origen = el;
    amaga();
    obre(qq, L, nom, curs, el);
  }
  // la fitxa d'un centre: un bloc del calendari porta a la cita que ho diu
  function aCita(el) {
    var p = el.getAttribute("data-qc").split(":");
    var art = document.getElementById("c-" + p[0]);
    if (!art) return;
    var cands = ["c-" + p[0] + "-q-" + p[1] + (p[2] === "s" ? "-s" : ""), "c-" + p[0] + "-q-" + p[1] + (p[2] === "s" ? "" : "-s")];
    var fig = null;
    cands.some(function (id) { fig = document.getElementById(id); return fig; });
    destaca(fig || art.querySelector(".fx-q"));
  }
  function destaca(el) {
    if (!el) return;
    var d = el.closest("details");
    if (d && !d.open) d.open = true;
    if (el.tagName === "DETAILS") el.open = true;
    el.scrollIntoView({ block: "center", behavior: "smooth" });
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }
  document.addEventListener("click", function (ev) {
    var bq = ev.target.closest && ev.target.closest(".dq-q blockquote");
    if (bq) { bq.classList.toggle("obert"); return; }
    var el = ev.target.closest && ev.target.closest("[data-q]");
    if (el) { ev.preventDefault(); activa(el, ev); return; }
    var c = ev.target.closest && ev.target.closest("[data-qc]");
    if (c) { aCita(c); }
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    var el = ev.target.closest && ev.target.closest("[data-q],[data-qc]");
    if (!el || el !== ev.target) return;
    ev.preventDefault();
    if (el.hasAttribute("data-q")) activa(el, null); else aCita(el);
  });
  // en arribar a una cita (des del panell), s'obre i es marca
  function vesCita() {
    var id = location.hash.slice(1);
    if (!/^c-\w+-(q|t)-/.test(id)) return;
    var el = document.getElementById(id) || document.getElementById(id.split("-").slice(0, 2).join("-"));
    if (!el) return;
    if (amagat(el)) posa("tot");
    setTimeout(function () { destaca(el); }, 60);
  }
  vesCita();
  window.addEventListener("hashchange", vesCita);

  // ---- cercador
  var caixesCerca = document.querySelectorAll("[data-cerca]");
  if (!caixesCerca.length) return;
  var index = null, carregant = null;
  function normal(s) {
    return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/l·l/g, "ll").replace(/[^a-z0-9]+/g, " ").trim();
  }
  function carrega() {
    if (index) return Promise.resolve(index);
    if (!carregant) {
      carregant = fetch(arrel + "cerca.json").then(function (r) { return r.json(); }).then(function (d) {
        index = d.map(function (it) {
          it.k_n = normal(it.n);
          it.k_t = normal(it.n + " " + (it.m || "") + " " + (it.c || ""));
          return it;
        });
        return index;
      });
    }
    return carregant;
  }
  var T = {
    ca: { co: "Comarca", m: "Municipi", d: "Districte", a: "analitzat", e: "centres", c: "concertat", p: "privat" },
    es: { co: "Comarca", m: "Municipio", d: "Distrito", a: "analizado", e: "centros", c: "concertado", p: "privado" }
  }[lang] || {};
  var PES = { co: 120, m: 100, d: 90, c: 0 };

  function busca(q) {
    var nq = normal(q);
    if (nq.length < 2) return [];
    var paraules = nq.split(" ");
    var res = [];
    index.forEach(function (it) {
      if (!paraules.every(function (p) { return it.k_t.indexOf(p) !== -1; })) return;
      var punts = PES[it.t] + (it.k_n.indexOf(nq) === 0 ? 50 : 0) + (it.k_n.indexOf(nq) !== -1 ? 20 : 0) + (it.a ? 5 : 0);
      res.push([punts, it]);
    });
    res.sort(function (a, b) { return b[0] - a[0] || a[1].n.localeCompare(b[1].n); });
    return res.slice(0, 9).map(function (r) { return r[1]; });
  }

  caixesCerca.forEach(function (caixa) {
    var input = caixa.querySelector("input");
    var llista = caixa.querySelector(".cerca-r");
    var buit = caixa.querySelector(".cerca-buit");
    var actual = -1, resultats = [];

    function tanca() { llista.hidden = true; input.setAttribute("aria-expanded", "false"); actual = -1; input.removeAttribute("aria-activedescendant"); }
    function ves(it) {
      if (!it) return;
      if (it.t === "c" && TIPUS_AB[abActual()].indexOf(it.tp || "") === -1) desa("abast", "tot");
      location.href = arrel + it.u[lang];
    }
    function pinta() {
      llista.innerHTML = "";
      buit.hidden = !(input.value.trim().length >= 2 && resultats.length === 0);
      if (!resultats.length) return tanca();
      resultats.forEach(function (it, i) {
        var li = document.createElement("li");
        li.id = input.id + "-o" + i;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", i === actual ? "true" : "false");
        var nom = document.createElement("span"); nom.className = "rn"; nom.textContent = it.n;
        var meta = document.createElement("span"); meta.className = "rm";
        if (it.t === "c") {
          meta.textContent = it.m + (it.e && it.e[lang] ? " · " + it.e[lang] : "") + (it.p === false ? " · " + (it.tp === "c" ? T.c : T.p) : "") + (it.a ? " · " + T.a : "");
        } else {
          meta.textContent = T[it.t] + (it.c ? " · " + it.c : "") + " · " + it.k + " " + T.e;
        }
        li.appendChild(nom); li.appendChild(meta);
        li.addEventListener("mousedown", function (ev) { ev.preventDefault(); ves(it); });
        llista.appendChild(li);
      });
      llista.hidden = false;
      input.setAttribute("aria-expanded", "true");
      if (actual >= 0) input.setAttribute("aria-activedescendant", input.id + "-o" + actual);
    }
    input.addEventListener("focus", function () { carrega(); });
    input.addEventListener("input", function () {
      carrega().then(function () { resultats = busca(input.value); actual = resultats.length ? 0 : -1; pinta(); })
        .catch(function () { buit.hidden = false; });
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown" && resultats.length) { actual = (actual + 1) % resultats.length; pinta(); ev.preventDefault(); }
      else if (ev.key === "ArrowUp" && resultats.length) { actual = (actual - 1 + resultats.length) % resultats.length; pinta(); ev.preventDefault(); }
      else if (ev.key === "Enter") { ves(resultats[actual >= 0 ? actual : 0]); ev.preventDefault(); }
      else if (ev.key === "Escape") { tanca(); }
    });
    input.addEventListener("blur", function () { setTimeout(tanca, 120); });
  });
})();
