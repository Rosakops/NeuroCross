#!/usr/bin/env python3
# =============================================================================
#  MODELO DE DATOS: catálogo de fármaco
#  Proyecto BHE. Calcado del patrón de nanotransportador.py (misma tarea de
#  arquitectura), pero de UN solo nivel: el fármaco no tiene categoría, solo
#  nombre -> ficha.
# =============================================================================
#
#  QUÉ ES ESTO
#  -----------
#  FARMACOS_SOPORTADOS es una lista ABIERTA y CORTA: hoy solo tiene el
#  fingolimod, que es el único fármaco con tamaño molecular derivado y
#  verificado (ver tamano_farmaco.py, tarea C9). Añadir un fármaco nuevo NO
#  es rellenar un número a ojo aquí: es calcularlo OFFLINE con
#  tamano_farmaco.py (RDKit no corre en Pyodide, confirmado), verificar la
#  fórmula y la masa molar contra el expediente, y solo entonces añadir UNA
#  entrada a este diccionario. Nunca en vivo en el navegador.
#
#  QUÉ NO HACE ESTE ARCHIVO
#  ------------------------
#  No deriva ningún tamaño molecular. Ese cálculo vive en tamano_farmaco.py.
#  Este archivo solo responde "¿qué fármacos existen" y "¿está soportado el
#  que me están pidiendo".
# =============================================================================

from dataclasses import dataclass


class FarmacoNoSoportado(ValueError):
    """El fármaco pedido no está en el catálogo todavía.

    NO es un bug: es el rechazo explícito que el flujo de entrada debe dar
    cuando alguien pide un fármaco sin tamaño molecular derivado y
    verificado. Nunca se debe interpretar como luz verde para inventar un
    diámetro y dejarlo pasar a las compuertas.
    """


@dataclass(frozen=True)
class FichaFarmaco:
    """Ficha de catálogo de un fármaco soportado."""
    nombre: str
    formula: str
    masa_molar_da: float
    diametro_maximo_nm: float
    fuente: str = ""


# =============================================================================
#  FÁRMACOS SOPORTADOS
#  Lista ABIERTA. Hoy solo el fingolimod: dimensión máxima extremo a extremo
#  (1.683 nm), promedio de 50 confórmeros ETKDGv3 + MMFF94, ver
#  tamano_farmaco.py (tarea C9).
# =============================================================================
FARMACOS_SOPORTADOS = {
    "fingolimod": FichaFarmaco(
        nombre="fingolimod",
        formula="C19H33NO2",
        masa_molar_da=307.48,
        diametro_maximo_nm=1.683,
        fuente="tamano_farmaco.py (tarea C9): dimensión máxima extremo a "
               "extremo, promedio de 50 confórmeros ETKDGv3 + MMFF94",
    ),
}


def _mensaje_no_soportado(farmaco: str) -> str:
    return (f"fármaco no soportado todavía: {farmaco!r}. Soportados hoy: "
            f"{', '.join(sorted(FARMACOS_SOPORTADOS)) or '(ninguno)'}. Un "
            "fármaco nuevo se añade calculando su tamaño offline con "
            "tamano_farmaco.py y verificándolo antes de entrar al catálogo")


def validar_farmaco(farmaco: str) -> FichaFarmaco:
    """Valida un fármaco ANTES de dejar entrar su diámetro a las compuertas.

    Rechaza explícitamente cualquier fármaco que no esté en
    FARMACOS_SOPORTADOS, con FarmacoNoSoportado y su mensaje explícito. Así
    ningún diámetro inventado llega nunca a evaluarse.
    """
    ficha = FARMACOS_SOPORTADOS.get(farmaco)
    if ficha is None:
        raise FarmacoNoSoportado(_mensaje_no_soportado(farmaco))
    return ficha


# =============================================================================
#  VALIDACIÓN DE ESTE MÓDULO
# =============================================================================

def test_farmaco(verbose=True):
    ok = []

    def chequeo(nombre, cond, detalle=""):
        ok.append(bool(cond))
        if verbose:
            print(f"  [{'OK ' if cond else 'FALLA'}] {nombre}{'  ' + detalle if detalle else ''}")

    if verbose:
        print("=" * 78)
        print(" VALIDACIÓN DEL CATÁLOGO DE FÁRMACO")
        print("=" * 78)

    chequeo("T1 el fingolimod está soportado",
            "fingolimod" in FARMACOS_SOPORTADOS)
    chequeo("T2 validar_farmaco acepta fingolimod y devuelve su ficha",
            validar_farmaco("fingolimod").diametro_maximo_nm == 1.683)
    chequeo("T3 la ficha del fingolimod lleva fórmula y masa molar del expediente",
            FARMACOS_SOPORTADOS["fingolimod"].formula == "C19H33NO2"
            and FARMACOS_SOPORTADOS["fingolimod"].masa_molar_da == 307.48)

    rechazado = False
    try:
        validar_farmaco("nocodazol")
    except FarmacoNoSoportado:
        rechazado = True
    chequeo("T4 un fármaco inexistente se rechaza con FarmacoNoSoportado, "
            "nunca se cuela con un diámetro inventado", rechazado)

    if verbose:
        print("-" * 78)
        print(f" RESULTADO: {sum(ok)}/{len(ok)} pruebas superadas")
        print("=" * 78)
    return all(ok)


if __name__ == "__main__":
    test_farmaco()
