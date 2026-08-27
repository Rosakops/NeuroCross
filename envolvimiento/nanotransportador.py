#!/usr/bin/env python3
# =============================================================================
#  MODELO DE DATOS: clase de nanotransportador
#  Proyecto BHE. Tarea de ARQUITECTURA (2026-08-27), no de datos ni de física.
# =============================================================================
#
#  QUÉ ES ESTO
#  -----------
#  Tres niveles:
#
#      categoría  (orgánico | inorgánico | híbrido)
#          -> subtipo YA SOPORTADO (lista ABIERTA, hoy solo: liposoma)
#              -> parámetros característicos de ese subtipo
#
#  La lista de categorías es fija (decisión de arquitectura). La lista de
#  SUBTIPOS es deliberadamente abierta y corta: hoy solo tiene el liposoma,
#  porque es el único subtipo con compuertas físicas calibradas en rutas.py.
#  Jhovan y Kiel están investigando el resto de subtipos aparte y los van a
#  entregar por partes vía el protocolo Bridge (Bridge/pending.md en el vault
#  de Obsidian). Añadir un subtipo nuevo cuando llegue por Bridge debe ser
#  UNA entrada en SUBTIPOS_SOPORTADOS, no una reescritura de esta estructura.
#
#  QUÉ NO HACE ESTE ARCHIVO
#  ------------------------
#  No define compuertas físicas ni umbrales. Esas siguen viviendo en rutas.py
#  (y sus metadatos de "para qué subtipo(s) está validada cada compuerta"
#  también, vía el decorador `compuerta_valida_para` de ese archivo), porque
#  son conocimiento de física, no de catálogo. Este archivo solo responde
#  "¿qué subtipos existen y a qué categoría pertenecen", y "¿está soportado
#  el que me están pidiendo".
# =============================================================================

from dataclasses import dataclass
from typing import Sequence


class SubtipoNoSoportado(ValueError):
    """El subtipo pedido no está en el catálogo todavía.

    NO es un bug: es el mensaje explícito que el flujo de entrada debe
    mostrar cuando alguien pide un subtipo que Jhovan y Kiel todavía no han
    entregado por Bridge. Nunca se debe interpretar como luz verde para
    evaluar esos parámetros con las compuertas de otro subtipo.
    """


@dataclass(frozen=True)
class SubtipoNanotransportador:
    """Ficha de catálogo de un subtipo soportado.

    `parametros` es solo la lista de nombres de los parámetros característicos
    que ese subtipo declara (para mostrarlos en el flujo de entrada); no los
    valida ni les pone rango. Esa es tarea de las compuertas de rutas.py el
    día que existan para ese subtipo.
    """
    nombre: str
    categoria: str
    parametros: Sequence[str]
    fuente: str = ""


# =============================================================================
#  NIVEL 1 · CATEGORÍAS
#  Lista fija. Añadir una categoría nueva es una decisión de Jhovan, no un
#  cambio de código libre.
# =============================================================================
CATEGORIAS = ("organico", "inorganico", "hibrido")


# =============================================================================
#  NIVEL 2 · SUBTIPOS SOPORTADOS
#  Lista ABIERTA. Hoy solo el liposoma: es el único subtipo con anclaje
#  experimental y compuertas calibradas en rutas.py (ver Diseno y las
#  compuertas g_* de ese archivo). NO se añaden subtipos nuevos aquí hasta
#  que lleguen por Bridge y Jhovan los valide.
# =============================================================================
SUBTIPOS_SOPORTADOS = {
    "liposoma": SubtipoNanotransportador(
        nombre="liposoma",
        categoria="organico",
        parametros=("diametro_nm", "zeta_mV", "peg_nm", "farmaco_diametro_nm"),
        fuente="único subtipo con compuertas calibradas hoy; ver rutas.Diseno "
               "y las compuertas g_* de rutas.py",
    ),
}


def categoria_de(subtipo: str) -> str:
    """Categoría de un subtipo SOPORTADO. Lanza SubtipoNoSoportado si no lo está."""
    ficha = SUBTIPOS_SOPORTADOS.get(subtipo)
    if ficha is None:
        raise SubtipoNoSoportado(_mensaje_no_soportado(subtipo))
    return ficha.categoria


def subtipos_de_categoria(categoria: str) -> list:
    """Subtipos YA SOPORTADOS dentro de una categoría. Puede devolver vacío:
    eso significa que esa categoría todavía no tiene ningún subtipo
    implementado, no que la categoría no exista.
    """
    if categoria not in CATEGORIAS:
        raise ValueError(f"categoría desconocida: {categoria!r}. "
                         f"Válidas: {', '.join(CATEGORIAS)}")
    return sorted(s for s, f in SUBTIPOS_SOPORTADOS.items()
                  if f.categoria == categoria)


def _mensaje_no_soportado(subtipo: str, categoria: str = None) -> str:
    if categoria is not None:
        disponibles = subtipos_de_categoria(categoria)
        if disponibles:
            return (f"subtipo no soportado todavía: {subtipo!r} en la "
                    f"categoría {categoria!r}. Soportados hoy en esa "
                    f"categoría: {', '.join(disponibles)}. La lista completa "
                    "la entregan Jhovan y Kiel por Bridge (Bridge/pending.md)")
        return (f"subtipo no soportado todavía: {subtipo!r}. La categoría "
                f"{categoria!r} no tiene NINGÚN subtipo soportado todavía. "
                "La lista la entregan Jhovan y Kiel por Bridge "
                "(Bridge/pending.md)")
    return (f"subtipo no soportado todavía: {subtipo!r}. Soportados hoy: "
            f"{', '.join(sorted(SUBTIPOS_SOPORTADOS)) or '(ninguno)'}. La "
            "lista completa la entregan Jhovan y Kiel por Bridge "
            "(Bridge/pending.md)")


def validar_subtipo(categoria: str, subtipo: str) -> SubtipoNanotransportador:
    """Valida categoría + subtipo ANTES de dejar entrar parámetros libres.

    Regla de esta tarea de arquitectura: un subtipo pedido que no esté en
    SUBTIPOS_SOPORTADOS (o que no pertenezca a la categoría indicada) nunca
    debe dejar pasar sus parámetros a las compuertas de otro subtipo. Se
    rechaza aquí, explícitamente, antes de construir ningún diseño.
    """
    if categoria not in CATEGORIAS:
        raise ValueError(f"categoría desconocida: {categoria!r}. "
                         f"Válidas: {', '.join(CATEGORIAS)}")
    ficha = SUBTIPOS_SOPORTADOS.get(subtipo)
    if ficha is None or ficha.categoria != categoria:
        raise SubtipoNoSoportado(_mensaje_no_soportado(subtipo, categoria))
    return ficha


# =============================================================================
#  FLUJO DE ENTRADA: primero categoría, luego solo los subtipos soportados
#  de esa categoría.
# =============================================================================

def flujo_entrada_interactivo(preguntar=input, informar=print):
    """Pide PRIMERO la categoría y LUEGO muestra solo los subtipos ya
    soportados dentro de ella. Si el subtipo pedido no está soportado, lo
    dice explícitamente y no deja avanzar.

    `preguntar` e `informar` son inyectables (por defecto `input`/`print`)
    para poder probar el flujo sin una terminal real.

    Devuelve (categoria, subtipo) si todo es válido, o None si se rechazó
    (el motivo ya se comunicó vía `informar`).
    """
    informar("Categorías disponibles: " + ", ".join(CATEGORIAS))
    categoria = preguntar("Categoría del nanotransportador: ").strip().lower()
    if categoria not in CATEGORIAS:
        informar(f"categoría desconocida: {categoria!r}. "
                f"Válidas: {', '.join(CATEGORIAS)}")
        return None

    disponibles = subtipos_de_categoria(categoria)
    if not disponibles:
        informar(f"la categoría {categoria!r} no tiene ningún subtipo "
                "soportado todavía. La lista la entregan Jhovan y Kiel por "
                "Bridge (Bridge/pending.md)")
        return None

    informar(f"Subtipos soportados en {categoria!r}: {', '.join(disponibles)}")
    subtipo = preguntar("Subtipo: ").strip().lower()
    try:
        validar_subtipo(categoria, subtipo)
    except SubtipoNoSoportado as e:
        informar(str(e))
        return None
    return categoria, subtipo


# =============================================================================
#  VALIDACIÓN DE ESTE MÓDULO
# =============================================================================

def test_nanotransportador(verbose=True):
    ok = []

    def chequeo(nombre, cond, detalle=""):
        ok.append(bool(cond))
        if verbose:
            print(f"  [{'OK ' if cond else 'FALLA'}] {nombre}{'  ' + detalle if detalle else ''}")

    if verbose:
        print("=" * 78)
        print(" VALIDACIÓN DEL MODELO DE CLASE DE NANOTRANSPORTADOR")
        print("=" * 78)

    chequeo("T1 el liposoma está soportado y es 'organico'",
            categoria_de("liposoma") == "organico")
    chequeo("T2 'organico' hoy solo lista liposoma",
            subtipos_de_categoria("organico") == ["liposoma"])
    chequeo("T3 'inorganico' no tiene ningún subtipo soportado todavía",
            subtipos_de_categoria("inorganico") == [])
    chequeo("T4 'hibrido' no tiene ningún subtipo soportado todavía",
            subtipos_de_categoria("hibrido") == [])

    chequeo("T5 validar_subtipo acepta liposoma/organico",
            validar_subtipo("organico", "liposoma").nombre == "liposoma")

    rechazado = False
    try:
        validar_subtipo("inorganico", "nanoparticula_oro")
    except SubtipoNoSoportado:
        rechazado = True
    chequeo("T6 un subtipo inexistente se rechaza con SubtipoNoSoportado",
            rechazado)

    rechazado_categoria_cruzada = False
    try:
        # dendrímero (si existiera) no es "inorganico": debe rechazarse aunque
        # el nombre exista en otra categoría, nunca colarse por la cruzada.
        validar_subtipo("inorganico", "liposoma")
    except SubtipoNoSoportado:
        rechazado_categoria_cruzada = True
    chequeo("T7 un subtipo real pedido bajo la categoría equivocada se rechaza",
            rechazado_categoria_cruzada)

    categoria_invalida = False
    try:
        validar_subtipo("mineral", "liposoma")
    except ValueError:
        categoria_invalida = True
    chequeo("T8 una categoría que no existe se rechaza (ValueError)",
            categoria_invalida)

    # flujo de entrada, con preguntar/informar simulados
    def _flujo(respuestas):
        it = iter(respuestas)
        mensajes = []
        resultado = flujo_entrada_interactivo(
            preguntar=lambda _: next(it), informar=mensajes.append)
        return resultado, mensajes

    r_ok, _ = _flujo(["organico", "liposoma"])
    chequeo("T9 flujo de entrada acepta organico/liposoma",
            r_ok == ("organico", "liposoma"))

    r_no_soportado, msgs = _flujo(["organico", "dendrimero"])
    chequeo("T10 flujo de entrada rechaza un subtipo no soportado, "
            "explícitamente y sin dejar avanzar",
            r_no_soportado is None and any("no soportado" in m for m in msgs))

    r_categoria_vacia, msgs2 = _flujo(["inorganico", "nanoparticula_oro"])
    chequeo("T11 flujo de entrada avisa si la categoría no tiene NINGÚN "
            "subtipo soportado, antes de pedir el subtipo",
            r_categoria_vacia is None
            and any("ningún subtipo" in m for m in msgs2))

    if verbose:
        print("-" * 78)
        print(f" RESULTADO: {sum(ok)}/{len(ok)} pruebas superadas")
        print("=" * 78)
    return all(ok)


if __name__ == "__main__":
    test_nanotransportador()
