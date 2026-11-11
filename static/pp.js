/* Observatori Lingüístic Escolar: complements de la web (afegits per postproces.py).
   - carrega a demanda les xifres de concertats i privats (no van a l'HTML inicial)
   - contacte sense l'adreça a l'HTML
   - subnavegació que s'amaga en baixar, al mòbil
   Sense dependències. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var main = document.querySelector("main[data-arrel]");
  var arrel = main ? main.getAttribute("data-arrel") : "/";
  var lang = doc.getAttribute("lang") === "ca" ? "ca" : "es";
  var versio = main ? main.getAttribute("data-v") || "" : "";
  var T = {
    ca: {
      carrega: "Carregant…", error: "No s'han pogut carregar aquestes xifres. Torna-ho a provar.",
      correu: "Escriu un correu"
    },
    es: {
      carrega: "Cargando…", error: "No se han podido cargar estas cifras. Vuelve a intentarlo.",
      correu: "Escribe un correo"
    }
  }[lang];

  // ---------------------------------------------------------------- variants a demanda
  var ABS = ["con", "pri", "pc", "pp", "cp", "tot"];
  var vp = main ? main.getAttribute("data-vp") : null;
  var carregats = {};
  function abActual() {
    for (var i = 0; i < ABS.length; i++) if (doc.classList.contains("ab-" + ABS[i])) return ABS[i];
    return "pub";
  }
  function inicia(arrelEl) {
    // el mateix que fa app.js en carregar la pàgina, per al contingut nou
    arrelEl.querySelectorAll("[data-desplega]").forEach(function (b) {
      b.addEventListener("click", function () {
        var l = b.previousElementSibling;
        if (l) l.classList.add("obert");
        b.hidden = true;
      });
    });
    arrelEl.querySelectorAll("[data-taula]").forEach(function (taula) {
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
  }
  function omple(ab) {
    if (!vp || ab === "pub" || carregats[ab]) return;
    var buits = document.querySelectorAll(".v-" + ab + "[data-vl]");
    if (!buits.length) { carregats[ab] = true; return; }
    carregats[ab] = true;
    buits.forEach(function (el) { el.setAttribute("data-vc", T.carrega); });
    fetch(arrel + vp + "v-" + ab + ".json?v=" + encodeURIComponent(versio)).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (d) {
      document.querySelectorAll("[data-vl]").forEach(function (el) {
        var h = d[el.getAttribute("data-vl")];
        if (h == null) return;
        el.innerHTML = h;
        el.removeAttribute("data-vl");
        el.removeAttribute("data-vc");
        inicia(el);
      });
      // si l'adreça apunta a una secció que acaba d'arribar, hi anem
      var id = decodeURIComponent(location.hash.slice(1));
      if (id) {
        var t = document.getElementById(id + "__" + ab) || document.getElementById(id);
        if (t && t.offsetParent) t.scrollIntoView({ block: "start" });
      }
    }).catch(function () {
      carregats[ab] = false;
      buits.forEach(function (el) { el.setAttribute("data-vc", T.error); });
    });
  }
  if (vp) {
    omple(abActual());
    new MutationObserver(function () { omple(abActual()); })
      .observe(doc, { attributes: true, attributeFilter: ["class"] });
  }

  // ---------------------------------------------------------------- taula de comarques: pestanyes d'etapa
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest("[data-pp-et]");
    if (!b) return;
    var sec = b.closest(".pp-llocs");
    if (!sec) return;
    sec.setAttribute("data-pp-et-on", b.getAttribute("data-pp-et"));
    sec.querySelectorAll("[data-pp-et]").forEach(function (x) { x.setAttribute("aria-selected", x === b ? "true" : "false"); });
  });

  // ---------------------------------------------------------------- contacte (l'adreça no és a l'HTML)
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest("[data-pp-m]");
    if (!b) return;
    ev.preventDefault();
    var u = "";
    try { u = atob(b.getAttribute("data-pp-m")).split("").reverse().join(""); } catch (x) { return; }
    var a = u + String.fromCharCode(64) + ["gm", "ail"].join("") + "." + "com";
    if (b.tagName === "BUTTON") {
      var l = document.createElement("a");
      l.href = "mailto:" + a + "?subject=" + encodeURIComponent("Observatori Lingüístic Escolar");
      l.textContent = a;
      l.className = "pp-m-a";
      b.replaceWith(l);
      l.click();
    }
  });

  // ---------------------------------------------------------------- capçalera: al mòbil s'amaga en baixar i torna en pujar
  var top = document.querySelector(".top");
  if (top && window.matchMedia) {
    var mq = window.matchMedia("(max-width: 720px)");
    var ultim = window.scrollY, pendent = false;
    window.addEventListener("scroll", function () {
      if (pendent) return;
      pendent = true;
      requestAnimationFrame(function () {
        pendent = false;
        var y = window.scrollY, dy = y - ultim;
        var obert = top.querySelector(".pp-abm[open]") || top.contains(document.activeElement) && document.activeElement.tagName === "INPUT";
        if (!mq.matches || y < 200 || obert) top.classList.remove("pp-amaga");
        else if (dy > 6) top.classList.add("pp-amaga");
        else if (dy < -6) top.classList.remove("pp-amaga");
        ultim = y;
      });
    }, { passive: true });
    top.addEventListener("focusin", function () { top.classList.remove("pp-amaga"); });
  }

  // ---------------------------------------------------------------- menú de tipus de centre: «Canvia-ho» l'obre; es tanca en clicar fora o amb Esc
  document.addEventListener("click", function (ev) {
    var obre = ev.target.closest && ev.target.closest("[data-pp-abm-obre]");
    if (obre) {
      var d = document.querySelector(".pp-abm");
      if (d) {
        ev.stopPropagation();
        if (top) top.classList.remove("pp-amaga");
        d.setAttribute("open", "");
        var b = d.querySelector('[aria-pressed="true"]') || d.querySelector("summary");
        if (b) b.focus();
      }
      return;
    }
    document.querySelectorAll(".pp-abm[open]").forEach(function (d) {
      if (!d.contains(ev.target)) d.removeAttribute("open");
    });
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    document.querySelectorAll(".pp-abm[open]").forEach(function (d) {
      d.removeAttribute("open");
      var s = d.querySelector("summary");
      if (s) s.focus();
    });
  });
})();
