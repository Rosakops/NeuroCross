"use strict";

// Los cuatro archivos del motor de física, en orden de dependencia (los dos
// primeros no dependen de nada más del proyecto; rutas.py importa a los
// otros tres). dataclasses/typing son librería estándar de Python: Pyodide
// ya las trae, no hace falta empaquetarlas.
const ARCHIVOS_MOTOR = [
  "nanotransportador.py",
  "farmaco.py",
  "glicocalix.py",
  "envolvimiento_core.py",
  "rutas.py",
];
const RUTA_MOTOR = "../envolvimiento/";

// Etiquetas de UI para las categorías. Los VALORES vienen siempre del
// catálogo real que expone Python (catalogo_json()); esto solo traduce el
// nombre interno a algo legible. No es una lista propia de categorías.
const ETIQUETA_CATEGORIA = {
  organico: "Orgánico",
  inorganico: "Inorgánico",
  hibrido: "Híbrido",
};

// Metadatos de UI (etiqueta, unidad, valor por defecto) para los parámetros
// que YA existen como campos de rutas.Diseno. No son parámetros nuevos: son
// los mismos nombres que reporta nanotransportador.SUBTIPOS_SOPORTADOS
// (ver parametros de la ficha "liposoma"), con una etiqueta legible.
const CAMPOS_CONOCIDOS = {
  diametro_nm: {etiqueta: "Diámetro", unidad: "nm", paso: "0.1", requerido: true,
                defecto: 100},
  zeta_mV: {etiqueta: "Potencial zeta (ζ)", unidad: "mV", paso: "0.1", requerido: true,
            defecto: -5},
  peg_nm: {etiqueta: "Espesor de PEG", unidad: "nm", paso: "0.1", requerido: false,
           defecto: 0},
  // farmaco_diametro_nm NO se renderiza como número libre: se resuelve
  // eligiendo un fármaco en el fieldset "Fármaco" (ver elegirSubtipo() /
  // poblarFarmacos()), que manda `farmaco` (el nombre) en vez de un
  // diámetro a mano.
};

const NOMBRES_RUTA_CORTOS = {
  "A · pasiva (adhesión y envolvimiento)": "A · Pasiva",
  "B · celular (macrófago de Troya)": "B · Celular (macrófago)",
  "C · adsortiva (carga positiva)": "C · Adsortiva",
  "D · mediada por receptor": "D · Mediada por receptor",
};

let pyodide = null;
let catalogo = null;
let categoriaElegida = null;
let subtipoElegido = null;
let farmacoElegido = null;

const $ = (id) => document.getElementById(id);

function fijarEstado(texto, clase) {
  const el = $("estado");
  el.className = clase;
  $("estado-texto").textContent = texto;
}

async function iniciar() {
  try {
    fijarEstado("Cargando Pyodide…", "cargando");
    pyodide = await loadPyodide();

    fijarEstado("Cargando NumPy…", "cargando");
    await pyodide.loadPackage("numpy");

    fijarEstado("Cargando el motor de física (rutas.py y módulos)…", "cargando");
    for (const archivo of ARCHIVOS_MOTOR) {
      const resp = await fetch(RUTA_MOTOR + archivo);
      if (!resp.ok) {
        throw new Error(`no se pudo cargar ${archivo} (HTTP ${resp.status})`);
      }
      const texto = await resp.text();
      pyodide.FS.writeFile(archivo, texto);
    }

    pyodide.runPython(`
import sys
if "." not in sys.path:
    sys.path.insert(0, ".")
import rutas as R
    `);

    catalogo = JSON.parse(pyodide.runPython("R.catalogo_json()"));

    fijarEstado("Motor de física cargado. Listo para evaluar.", "listo");
    $("seccion-flujo").classList.remove("oculto");
    $("seccion-leyenda").classList.remove("oculto");
    poblarCategorias();
  } catch (err) {
    console.error(err);
    fijarEstado("No se pudo cargar el motor de física: " + err.message, "error");
  }
}

function poblarCategorias() {
  const cont = $("opciones-categoria");
  cont.innerHTML = "";
  for (const cat of catalogo.categorias) {
    const id = `cat-${cat}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="radio" name="categoria" id="${id}" value="${cat}">
      ${ETIQUETA_CATEGORIA[cat] || cat}`;
    label.querySelector("input").addEventListener("change", () => elegirCategoria(cat));
    cont.appendChild(label);
  }
}

function elegirCategoria(cat) {
  categoriaElegida = cat;
  subtipoElegido = null;
  $("fieldset-subtipo").classList.remove("oculto");
  $("fieldset-parametros").classList.add("oculto");
  $("boton-evaluar").disabled = true;

  const subtipos = catalogo.subtipos_por_categoria[cat] || [];
  const contOpciones = $("opciones-subtipo");
  const msgVacio = $("mensaje-sin-subtipos");
  contOpciones.innerHTML = "";

  if (subtipos.length === 0) {
    contOpciones.classList.add("oculto");
    msgVacio.classList.remove("oculto");
    msgVacio.textContent =
      `La categoría "${ETIQUETA_CATEGORIA[cat] || cat}" no tiene ningún subtipo ` +
      `soportado todavía. La lista la entregan Jhovan y Kiel por Bridge ` +
      `(Bridge/pending.md); mientras no llegue, esta categoría no acepta ` +
      `parámetros libres — no hay compuertas calibradas para evaluarlos.`;
    return;
  }

  contOpciones.classList.remove("oculto");
  msgVacio.classList.add("oculto");
  for (const {subtipo} of subtipos) {
    const id = `sub-${subtipo}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="radio" name="subtipo" id="${id}" value="${subtipo}">
      ${subtipo}`;
    label.querySelector("input").addEventListener("change", () => elegirSubtipo(subtipo));
    contOpciones.appendChild(label);
  }
}

function elegirSubtipo(subtipo) {
  subtipoElegido = subtipo;
  const ficha = (catalogo.subtipos_por_categoria[categoriaElegida] || [])
    .find((f) => f.subtipo === subtipo);
  const parametros = ficha ? ficha.parametros : [];

  // farmaco_diametro_nm ya NO se pide como número libre: se resuelve
  // eligiendo un fármaco del catálogo (fieldset "Fármaco"), que rutas.py
  // traduce a su diámetro vía construir_diseno(). El resto de parámetros
  // sigue siendo la rejilla numérica de siempre.
  const pideFarmaco = parametros.includes("farmaco_diametro_nm");
  renderizarParametros(parametros.filter((p) => p !== "farmaco_diametro_nm"));

  if (pideFarmaco) {
    poblarFarmacos();
    $("fieldset-farmaco").classList.remove("oculto");
  } else {
    farmacoElegido = null;
    $("fieldset-farmaco").classList.add("oculto");
  }

  $("fieldset-parametros").classList.remove("oculto");
  $("boton-evaluar").disabled = false;
}

function poblarFarmacos() {
  const farmacos = catalogo.farmacos || [];
  const cont = $("opciones-farmaco");
  cont.innerHTML = "";

  for (const [i, ficha] of farmacos.entries()) {
    const id = `farmaco-${ficha.farmaco}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="radio" name="farmaco" id="${id}" value="${ficha.farmaco}"
        ${i === 0 ? "checked" : ""}>
      ${ficha.farmaco}`;
    label.querySelector("input").addEventListener("change", () => {
      farmacoElegido = ficha.farmaco;
    });
    cont.appendChild(label);
  }

  // El catálogo hoy solo tiene una entrada; se preselecciona igual que
  // categoría/subtipo cuando solo hay una opción disponible, sin obligar a
  // hacer clic. Cuando lleguen más fármacos, seguirá siendo el primero por
  // defecto hasta que el usuario elija otro.
  farmacoElegido = farmacos.length ? farmacos[0].farmaco : null;
}

function renderizarParametros(parametros) {
  const cont = $("rejilla-parametros");
  cont.innerHTML = "";
  for (const nombreCampo of parametros) {
    const meta = CAMPOS_CONOCIDOS[nombreCampo] || {
      etiqueta: nombreCampo, unidad: "", paso: "any", requerido: false, defecto: "",
    };
    const div = document.createElement("div");
    div.className = "campo";
    div.innerHTML = `
      <label for="param-${nombreCampo}">${meta.etiqueta}
        ${meta.unidad ? `<span class="pista">(${meta.unidad})</span>` : ""}
      </label>
      <input type="number" step="${meta.paso}" id="param-${nombreCampo}"
             data-campo="${nombreCampo}" value="${meta.defecto}"
             ${meta.requerido ? "required" : ""}>
    `;
    cont.appendChild(div);
  }
}

function leerParametros() {
  const params = {nombre: $("campo-nombre").value.trim() || "Candidato"};
  for (const input of document.querySelectorAll("#rejilla-parametros input")) {
    const campo = input.dataset.campo;
    const valor = input.value.trim();
    if (valor === "") continue;
    params[campo] = Number(valor);
  }
  // No se manda farmaco_diametro_nm: se manda el NOMBRE del fármaco elegido
  // y rutas.construir_diseno() lo resuelve vía farmaco.FARMACOS_SOPORTADOS
  // (rechaza uno no catalogado antes de construir el diseño).
  if (farmacoElegido !== null) {
    params.farmaco = farmacoElegido;
  }
  return params;
}

function evaluar() {
  $("mensaje-error-evaluacion").classList.add("oculto");
  let params;
  try {
    params = leerParametros();
  } catch (err) {
    mostrarErrorEvaluacion(err.message);
    return;
  }

  pyodide.globals.set("_categoria", categoriaElegida);
  pyodide.globals.set("_subtipo", subtipoElegido);
  pyodide.globals.set("_params_json", JSON.stringify(params));
  const salida = pyodide.runPython("R.evaluar_json(_categoria, _subtipo, _params_json)");
  const resultado = JSON.parse(salida);

  if (resultado.error) {
    mostrarErrorEvaluacion(resultado.error);
    return;
  }
  renderizarResultados(resultado);
}

function mostrarErrorEvaluacion(texto) {
  const el = $("mensaje-error-evaluacion");
  el.textContent = texto;
  el.classList.remove("oculto");
}

function claseVeredicto(v) {
  if (v === "EXCLUIDA") return "veredicto-excluida";
  if (v === "NO EXCLUIDA") return "veredicto-no-excluida";
  return "veredicto-no-evaluable";
}

function claseConfianza(c) {
  if (c === "validada con contraste real") return {clase: "validada", icono: "●"};
  if (c === "prestada por analogía (sin contraste propio)") return {clase: "analogia", icono: "◐"};
  return {clase: "sinfisica", icono: "○"};
}

function renderizarResultados(resultado) {
  const cont = $("resultados");
  cont.innerHTML = "";
  cont.classList.remove("oculto");

  const titulo = document.createElement("h2");
  titulo.textContent = `Resultado para "${resultado.diseno}"`;
  cont.appendChild(titulo);

  for (const [nombreRuta, datos] of Object.entries(resultado.rutas)) {
    const seccion = document.createElement("div");
    seccion.className = "tarjeta ruta";

    const cabeza = document.createElement("div");
    cabeza.className = "cabeza";
    cabeza.innerHTML = `
      <h3>${NOMBRES_RUTA_CORTOS[nombreRuta] || nombreRuta}</h3>
      <span class="badge ${claseVeredicto(datos.veredicto)}">${datos.veredicto}</span>
    `;
    seccion.appendChild(cabeza);

    for (const c of datos.compuertas) {
      const conf = claseConfianza(c.confianza);
      const fila = document.createElement("div");
      fila.className = "compuerta";

      let datosLinea = "";
      if (c.valor !== null && c.umbral !== null) {
        datosLinea = `<div class="datos">valor ${c.valor.toFixed(2)} / umbral ${c.umbral.toFixed(2)} ${c.unidad || ""}</div>`;
      } else if (c.valor !== null) {
        datosLinea = `<div class="datos">valor ${c.valor.toFixed(2)} ${c.unidad || ""}</div>`;
      }

      fila.innerHTML = `
        <div class="fila-1">
          <span class="nombre">${c.compuerta}</span>
          <span class="badges">
            <span class="confianza ${conf.clase}">${conf.icono} ${c.confianza}</span>
            <span class="badge ${c.estado}">${c.estado}</span>
          </span>
        </div>
        ${datosLinea}
        ${c.motivo ? `<div class="motivo">${c.motivo}</div>` : ""}
        ${c.advertencia ? `<div class="advertencia">⚠ ${c.advertencia}</div>` : ""}
        ${c.fuente ? `<div class="fuente">${c.fuente}</div>` : ""}
      `;
      seccion.appendChild(fila);
    }

    cont.appendChild(seccion);
  }

  renderizarQueInvestigar(resultado);
  cont.scrollIntoView({behavior: "smooth", block: "start"});
}

// Prefijo que rutas.py estampa en `que_investigar` para un hueco AGOTADO
// (la pregunta ya se cerró: no repetir la búsqueda). Ver Resultado en
// rutas.py y su comentario junto al campo `que_investigar`.
const PREFIJO_AGOTADO = "AGOTADO";

function renderizarQueInvestigar(resultado) {
  const cont = $("seccion-que-investigar");
  cont.innerHTML = "";
  cont.classList.remove("oculto");

  // Junta las DESCONOCIDA con que_investigar no vacío de las CUATRO rutas,
  // deduplicando por nombre de compuerta (la misma compuerta aparece en más
  // de una ruta con el mismo texto). Fuera de alcance por diseño
  // (que_investigar vacío, p.ej. transcitosis) no entra aquí a propósito.
  const vistos = new Map();
  for (const datos of Object.values(resultado.rutas)) {
    for (const c of datos.compuertas) {
      if (c.estado !== "DESCONOCIDA" || !c.que_investigar) continue;
      if (!vistos.has(c.compuerta)) vistos.set(c.compuerta, c.que_investigar);
    }
  }

  const titulo = document.createElement("h2");
  titulo.textContent = "Qué investigar para este diseño";
  cont.appendChild(titulo);

  if (vistos.size === 0) {
    const p = document.createElement("p");
    p.textContent = "Ninguna compuerta DESCONOCIDA de este diseño tiene un "
      + "experimento pendiente que investigar: los huecos que aparecieron "
      + "arriba, si los hay, son por alcance de diseño o ya están agotados.";
    cont.appendChild(p);
    return;
  }

  const abiertos = [];
  const agotados = [];
  for (const [compuerta, texto] of vistos) {
    if (texto.startsWith(PREFIJO_AGOTADO)) {
      agotados.push([compuerta, texto]);
    } else {
      abiertos.push([compuerta, texto]);
    }
  }

  const grupo = (titulo, items, clase) => {
    if (items.length === 0) return;
    const div = document.createElement("div");
    div.className = `grupo-que-investigar ${clase}`;
    const h3 = document.createElement("h3");
    h3.textContent = titulo;
    div.appendChild(h3);
    for (const [compuerta, texto] of items) {
      const item = document.createElement("div");
      item.className = "item-que-investigar";
      item.innerHTML = `<span class="nombre">${compuerta}</span>
        <div class="texto">${texto}</div>`;
      div.appendChild(item);
    }
    cont.appendChild(div);
  };

  grupo("Huecos abiertos — vale la pena investigar", abiertos, "abierto");
  grupo("Huecos agotados — no repetir búsqueda", agotados, "agotado");
}

$("boton-evaluar").addEventListener("click", evaluar);
iniciar();

const botonMenu = document.getElementById('boton-menu');
const barraLateral = document.getElementById('barra-lateral');
const fondoBarra = document.getElementById('fondo-barra');

function alternarBarra(){
  barraLateral.classList.toggle('abierta');
  fondoBarra.classList.toggle('visible');
}
botonMenu.addEventListener('click', alternarBarra);
fondoBarra.addEventListener('click', alternarBarra);

const enlaces = document.querySelectorAll('.enlace-barra');

enlaces.forEach(enlace => {
  enlace.addEventListener('click', (e) => {
    e.preventDefault();
    const idVista = enlace.dataset.vista;

    document.querySelectorAll('.vista').forEach(v => v.classList.add('oculto'));
    document.getElementById(idVista).classList.remove('oculto');

    enlaces.forEach(el => el.classList.remove('activo'));
    enlace.classList.add('activo');

    alternarBarra(); // cierra la barra al elegir una opción
  });
});
