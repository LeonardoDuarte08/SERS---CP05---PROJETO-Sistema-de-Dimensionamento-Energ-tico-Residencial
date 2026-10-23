import csv
import math

def calcular_consumo(equipamentos):
    consumo_mensal = 0
    potencia_instalada = 0

    for equipamento in equipamentos:
        potencia_kw = equipamento["potencia_w"] / 1000

        consumo_mensal += (
            potencia_kw
            * equipamento["quantidade"]
            * equipamento["horas_dia"]
            * 30
        )

        potencia_instalada += (
            equipamento["potencia_w"]
            * equipamento["quantidade"]
        )

    consumo_diario = consumo_mensal / 30

    return {
        "consumo_mensal": consumo_mensal,
        "consumo_diario": consumo_diario,
        "potencia_instalada": potencia_instalada
    }

def carregar_csv(caminho):
    dados = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig"
    ) as arquivo:

        leitor = csv.DictReader(
            arquivo,
            delimiter=";"
        )

        for linha in leitor:
            dados.append(linha)

    return dados


def carregar_modulos():
    return carregar_csv(
        "dados/modulos.csv"
    )


def carregar_inversores():
    return carregar_csv(
        "dados/inversores.csv"
    )


def carregar_baterias():
    return carregar_csv(
        "dados/baterias.csv"
    )

def calcular_potencia_fv(
    consumo_mensal,
    hsp,
    pr
):
    if consumo_mensal < 0:
        raise ValueError(
            "O consumo mensal não pode ser negativo."
        )

    if hsp <= 0:
        raise ValueError(
            "A HSP deve ser maior que zero."
        )

    if pr <= 0 or pr > 1:
        raise ValueError(
            "O PR deve estar entre 0 e 1."
        )

    consumo_diario = consumo_mensal / 30

    potencia_fv = (
        consumo_diario
        / (hsp * pr)
    )

    return {
        "consumo_diario": consumo_diario,
        "hsp": hsp,
        "pr": pr,
        "potencia_fv_kwp": potencia_fv
    }

def selecionar_modulo(
    potencia_fv_kwp,
    modulos
):
    if potencia_fv_kwp <= 0:
        raise ValueError(
            "A potência fotovoltaica deve ser maior que zero."
        )

    melhor_opcao = None

    for modulo in modulos:

        potencia_w = float(
            modulo["potencia_wp"]
        )

        potencia_kw = potencia_w / 1000

        quantidade = math.ceil(
            potencia_fv_kwp / potencia_kw
        )

        potencia_instalada_kwp = (
            quantidade * potencia_kw
        )

        preco_unitario = float(
            modulo["preco_brl"]
        )

        custo_total = (
            quantidade * preco_unitario
        )

        opcao = {
            "id": modulo["id"],
            "fabricante": modulo["fabricante"],
            "modelo": modulo["modelo"],
            "potencia_w": potencia_w,
            "voc_v": float(modulo["voc_v"]),
            "isc_a": float(modulo["isc_a"]),
            "vmp_v": float(modulo["vmp_v"]),
            "imp_a": float(modulo["imp_a"]),
            "quantidade": quantidade,
            "potencia_instalada_kwp": potencia_instalada_kwp,
            "preco_unitario": preco_unitario,
            "custo_total": custo_total
        }

        if (
            melhor_opcao is None
            or opcao["custo_total"]
            < melhor_opcao["custo_total"]
        ):
            melhor_opcao = opcao

    if melhor_opcao is None:
        raise ValueError(
            "Nenhum módulo disponível."
        )

    return melhor_opcao

def selecionar_inversor(
    modulo,
    inversores
):
    potencia_instalada_w = (
        modulo["potencia_instalada_kwp"] * 1000
    )

    quantidade_modulos = modulo["quantidade"]

    voc_total = (
        modulo["voc_v"]
        * quantidade_modulos
    )

    vmp_total = (
        modulo["vmp_v"]
        * quantidade_modulos
    )

    isc_total = modulo["isc_a"]

    melhor_inversor = None

    for inversor in inversores:

        potencia_nominal_w = float(
            inversor["potencia_nominal_w"]
        )

        potencia_max_fv_w = float(
            inversor["potencia_max_fv_w"]
        )

        tensao_max_v = float(
            inversor["tensao_max_entrada_v"]
        )

        mppt_min_v = float(
            inversor["faixa_mppt_min_v"]
        )

        mppt_max_v = float(
            inversor["faixa_mppt_max_v"]
        )

        corrente_max_a = float(
            inversor["corrente_max_entrada_a"]
        )

        preco = float(
            inversor["preco_brl"]
        )

        potencia_ok = (
            potencia_instalada_w
            <= potencia_max_fv_w
        )

        tensao_max_ok = (
            voc_total
            <= tensao_max_v
        )

        mppt_ok = (
            mppt_min_v
            <= vmp_total
            <= mppt_max_v
        )

        corrente_ok = (
            isc_total
            <= corrente_max_a
        )

        if not (
            potencia_ok
            and tensao_max_ok
            and mppt_ok
            and corrente_ok
        ):
            continue

        relacao_dc_ac = (
            potencia_instalada_w
            / potencia_nominal_w
        )

        opcao = {
            "id": inversor["id"],
            "fabricante": inversor["fabricante"],
            "modelo": inversor["modelo"],
            "tipo": inversor["tipo"],
            "potencia_nominal_w": potencia_nominal_w,
            "potencia_max_fv_w": potencia_max_fv_w,
            "tensao_max_v": tensao_max_v,
            "mppt_min_v": mppt_min_v,
            "mppt_max_v": mppt_max_v,
            "corrente_max_a": corrente_max_a,
            "numero_mppt": inversor["numero_mppt"],
            "compativel_bateria": inversor[
                "compativel_bateria"
            ],
            "preco": preco,
            "voc_total": voc_total,
            "vmp_total": vmp_total,
            "isc_total": isc_total,
            "relacao_dc_ac": relacao_dc_ac
        }

        if (
            melhor_inversor is None
            or opcao["preco"]
            < melhor_inversor["preco"]
        ):
            melhor_inversor = opcao

    if melhor_inversor is None:
        raise ValueError(
            "Nenhum inversor tecnicamente compatível foi encontrado."
        )

    return melhor_inversor