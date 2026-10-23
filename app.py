from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dimensionamento import (
    calcular_consumo,
    calcular_potencia_fv,
    calcular_geracao_fv,
    carregar_modulos,
    carregar_inversores,
    carregar_baterias,
    selecionar_modulo,
    selecionar_inversor,
    selecionar_sistema_com_bateria,
    dimensionar_bateria
)

import json
import os
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


app = Flask(__name__)

app.secret_key = "sistema-energia-residencial"

ARQUIVO_LOGINS = "dados/logins.json"
ARQUIVO_RESIDENCIAS = "dados/residencias.json"


EQUIPAMENTOS_DISPONIVEIS = [
    {
        "nome": "Geladeira",
        "potencia_w": 150
    },
    {
        "nome": "Chuveiro Elétrico",
        "potencia_w": 5500
    },
    {
        "nome": "TV",
        "potencia_w": 100
    },
    {
        "nome": "Ar-condicionado",
        "potencia_w": 900
    },
    {
        "nome": "Computador",
        "potencia_w": 200
    },
    {
        "nome": "Lâmpada LED",
        "potencia_w": 9
    },
    {
        "nome": "Máquina de Lavar",
        "potencia_w": 500
    },
    {
        "nome": "Micro-ondas",
        "potencia_w": 1200
    }
]


def carregar_usuarios():

    if not os.path.exists(
        ARQUIVO_LOGINS
    ):
        return []

    with open(
        ARQUIVO_LOGINS,
        "r",
        encoding="utf-8"
    ) as arquivo:

        try:
            return json.load(
                arquivo
            )

        except json.JSONDecodeError:
            return []


def salvar_usuarios(
    usuarios
):

    os.makedirs(
        os.path.dirname(
            ARQUIVO_LOGINS
        ),
        exist_ok=True
    )

    with open(
        ARQUIVO_LOGINS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            usuarios,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def gerar_novo_id(
    usuarios
):

    if not usuarios:
        return 1

    maior_id = max(
        usuario["id"]
        for usuario in usuarios
    )

    return maior_id + 1


def carregar_residencias():

    if not os.path.exists(
        ARQUIVO_RESIDENCIAS
    ):
        return []

    with open(
        ARQUIVO_RESIDENCIAS,
        "r",
        encoding="utf-8"
    ) as arquivo:

        try:
            return json.load(
                arquivo
            )

        except json.JSONDecodeError:
            return []


def salvar_residencias(
    residencias
):

    os.makedirs(
        os.path.dirname(
            ARQUIVO_RESIDENCIAS
        ),
        exist_ok=True
    )

    with open(
        ARQUIVO_RESIDENCIAS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            residencias,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def gerar_novo_id_residencia(
    residencias
):

    if not residencias:
        return 1

    return max(
        residencia["id"]
        for residencia in residencias
    ) + 1


def buscar_residencia_por_id(
    residencia_id,
    usuario_id
):

    residencias = (
        carregar_residencias()
    )

    for residencia in residencias:

        if (
            residencia["id"]
            == residencia_id
            and residencia["usuario_id"]
            == usuario_id
        ):
            return residencia

    return None


def atualizar_residencia(
    residencia_atualizada
):

    residencias = (
        carregar_residencias()
    )

    for i, residencia in enumerate(
        residencias
    ):

        if (
            residencia["id"]
            == residencia_atualizada["id"]
        ):
            residencias[i] = (
                residencia_atualizada
            )
            break

    salvar_residencias(
        residencias
    )


def criar_orcamento_sem_bateria(modulo, inversor):

    itens = [
        {
            "equipamento": "Módulo fotovoltaico",
            "fabricante": modulo["fabricante"],
            "modelo": modulo["modelo"],
            "quantidade": modulo["quantidade"],
            "preco_unitario": round(
                modulo["preco_unitario"],
                2
            ),
            "subtotal": round(
                modulo["custo_total"],
                2
            )
        },
        {
            "equipamento": "Inversor",
            "fabricante": inversor["fabricante"],
            "modelo": inversor["modelo"],
            "quantidade": 1,
            "preco_unitario": round(
                inversor["preco"],
                2
            ),
            "subtotal": round(
                inversor["preco"],
                2
            )
        }
    ]

    custo_total = sum(
        item["subtotal"]
        for item in itens
    )

    return {
        "itens": itens,
        "custo_total": round(
            custo_total,
            2
        )
    }


def criar_orcamento_com_bateria(
    modulo,
    inversor,
    bateria
):

    itens = [
        {
            "equipamento": "Módulo fotovoltaico",
            "fabricante": modulo["fabricante"],
            "modelo": modulo["modelo"],
            "quantidade": modulo["quantidade"],
            "preco_unitario": round(
                modulo["preco_unitario"],
                2
            ),
            "subtotal": round(
                modulo["custo_total"],
                2
            )
        },
        {
            "equipamento": "Inversor híbrido",
            "fabricante": inversor["fabricante"],
            "modelo": inversor["modelo"],
            "quantidade": 1,
            "preco_unitario": round(
                inversor["preco"],
                2
            ),
            "subtotal": round(
                inversor["preco"],
                2
            )
        },
        {
            "equipamento": "Bateria",
            "fabricante": bateria["fabricante"],
            "modelo": bateria["modelo"],
            "quantidade": bateria["quantidade"],
            "preco_unitario": round(
                bateria["preco_unitario"],
                2
            ),
            "subtotal": round(
                bateria["custo_total"],
                2
            )
        }
    ]

    custo_total = sum(
        item["subtotal"]
        for item in itens
    )

    return {
        "itens": itens,
        "custo_total": round(
            custo_total,
            2
        )
    }


@app.route("/")
def index():

    if "usuario_id" not in session:
        return redirect(
            url_for(
                "login"
            )
        )

    todas_residencias = (
        carregar_residencias()
    )

    residencias_usuario = [
        residencia
        for residencia
        in todas_residencias
        if residencia["usuario_id"]
        == session["usuario_id"]
    ]

    return render_template(
        "index.html",
        usuario_nome=session.get(
            "usuario_nome"
        ),
        residencias=residencias_usuario
    )


@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    mensagem = ""
    sucesso = ""

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar_senha = (
            request.form.get(
                "confirmar_senha",
                ""
            )
        )

        if (
            not nome
            or not email
            or not senha
            or not confirmar_senha
        ):

            mensagem = (
                "Preencha todos os campos."
            )

        elif senha != confirmar_senha:

            mensagem = (
                "As senhas não são iguais."
            )

        elif len(senha) < 6:

            mensagem = (
                "A senha deve possuir "
                "pelo menos 6 caracteres."
            )

        else:

            usuarios = (
                carregar_usuarios()
            )

            email_existente = any(
                usuario["email"]
                == email
                for usuario
                in usuarios
            )

            if email_existente:

                mensagem = (
                    "Este e-mail já está "
                    "cadastrado."
                )

            else:

                senha_hash = (
                    generate_password_hash(
                        senha
                    )
                )

                novo_usuario = {
                    "id": gerar_novo_id(
                        usuarios
                    ),
                    "nome": nome,
                    "email": email,
                    "senha_hash": senha_hash
                }

                usuarios.append(
                    novo_usuario
                )

                salvar_usuarios(
                    usuarios
                )

                sucesso = (
                    "Usuário cadastrado "
                    "com sucesso."
                )

    return render_template(
        "cadastro.html",
        mensagem=mensagem,
        sucesso=sucesso
    )


@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    mensagem = ""

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        usuarios = (
            carregar_usuarios()
        )

        usuario_encontrado = None

        for usuario in usuarios:

            if (
                usuario["email"]
                == email
            ):
                usuario_encontrado = (
                    usuario
                )
                break

        if usuario_encontrado is None:

            mensagem = (
                "E-mail ou senha inválidos."
            )

        else:

            senha_correta = (
                check_password_hash(
                    usuario_encontrado[
                        "senha_hash"
                    ],
                    senha
                )
            )

            if senha_correta:

                session[
                    "usuario_id"
                ] = usuario_encontrado[
                    "id"
                ]

                session[
                    "usuario_nome"
                ] = usuario_encontrado[
                    "nome"
                ]

                session[
                    "usuario_email"
                ] = usuario_encontrado[
                    "email"
                ]

                return redirect(
                    url_for(
                        "index"
                    )
                )

            mensagem = (
                "E-mail ou senha inválidos."
            )

    return render_template(
        "login.html",
        mensagem=mensagem
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for(
            "login"
        )
    )


@app.route(
    "/residencia/nova",
    methods=["GET", "POST"]
)
def nova_residencia():

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    mensagem = ""

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        cidade = request.form.get(
            "cidade",
            ""
        ).strip()

        area = request.form.get(
            "area",
            ""
        ).strip()

        moradores = request.form.get(
            "moradores",
            ""
        ).strip()

        tarifa = request.form.get(
            "tarifa",
            ""
        ).strip()

        if (
            not nome
            or not cidade
            or not area
            or not moradores
            or not tarifa
        ):

            mensagem = (
                "Preencha todos os campos."
            )

        else:

            try:

                area = float(
                    area
                )

                moradores = int(
                    moradores
                )

                tarifa = float(
                    tarifa
                )

                if area <= 0:

                    mensagem = (
                        "A área deve ser "
                        "maior que zero."
                    )

                elif moradores <= 0:

                    mensagem = (
                        "Informe pelo menos "
                        "um morador."
                    )

                elif tarifa <= 0:

                    mensagem = (
                        "A tarifa deve ser "
                        "maior que zero."
                    )

                else:

                    residencias = (
                        carregar_residencias()
                    )

                    nova = {
                        "id": (
                            gerar_novo_id_residencia(
                                residencias
                            )
                        ),
                        "usuario_id": session[
                            "usuario_id"
                        ],
                        "nome": nome,
                        "cidade": cidade,
                        "area_m2": area,
                        "moradores": moradores,
                        "tarifa_kwh": tarifa,
                        "equipamentos": []
                    }

                    residencias.append(
                        nova
                    )

                    salvar_residencias(
                        residencias
                    )

                    return redirect(
                        url_for(
                            "index"
                        )
                    )

            except ValueError:

                mensagem = (
                    "Preencha os valores "
                    "numéricos corretamente."
                )

    return render_template(
        "nova_residencia.html",
        mensagem=mensagem
    )


@app.route(
    "/residencia/<int:residencia_id>"
)
def residencia(
    residencia_id
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    equipamentos = (
        residencia_selecionada.get(
            "equipamentos",
            []
        )
    )

    resultado_consumo = (
        calcular_consumo(
            equipamentos
        )
    )

    consumo_mensal = (
        resultado_consumo[
            "consumo_mensal"
        ]
    )

    consumo_diario = (
        resultado_consumo[
            "consumo_diario"
        ]
    )

    potencia_instalada = (
        resultado_consumo[
            "potencia_instalada"
        ]
    )

    custo_mensal = (
        consumo_mensal
        * residencia_selecionada[
            "tarifa_kwh"
        ]
    )

    return render_template(
        "residencia.html",
        residencia=(
            residencia_selecionada
        ),
        equipamentos=equipamentos,
        consumo_mensal=consumo_mensal,
        consumo_diario=consumo_diario,
        custo_mensal=custo_mensal,
        potencia_instalada=(
            potencia_instalada
        )
    )


@app.route(
    "/residencia/<int:residencia_id>/equipamento/novo",
    methods=["GET", "POST"]
)
def novo_equipamento(
    residencia_id
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    mensagem = ""

    if request.method == "POST":

        nome_equipamento = (
            request.form.get(
                "equipamento",
                ""
            )
        )

        quantidade = (
            request.form.get(
                "quantidade",
                ""
            ).strip()
        )

        horas_dia = (
            request.form.get(
                "horas_dia",
                ""
            ).strip()
        )

        equipamento_selecionado = (
            None
        )

        for equipamento in (
            EQUIPAMENTOS_DISPONIVEIS
        ):

            if (
                equipamento["nome"]
                == nome_equipamento
            ):

                equipamento_selecionado = (
                    equipamento
                )

                break

        if (
            equipamento_selecionado
            is None
        ):

            mensagem = (
                "Selecione um equipamento "
                "válido."
            )

        elif (
            not quantidade
            or not horas_dia
        ):

            mensagem = (
                "Preencha todos os campos."
            )

        else:

            try:

                quantidade = int(
                    quantidade
                )

                horas_dia = float(
                    horas_dia
                )

                if quantidade <= 0:

                    mensagem = (
                        "A quantidade deve ser "
                        "maior que zero."
                    )

                elif (
                    horas_dia <= 0
                    or horas_dia > 24
                ):

                    mensagem = (
                        "As horas de uso devem "
                        "estar entre 0 e 24."
                    )

                else:

                    novo = {
                        "nome": (
                            equipamento_selecionado[
                                "nome"
                            ]
                        ),
                        "potencia_w": (
                            equipamento_selecionado[
                                "potencia_w"
                            ]
                        ),
                        "quantidade": (
                            quantidade
                        ),
                        "horas_dia": (
                            horas_dia
                        )
                    }

                    residencia_selecionada[
                        "equipamentos"
                    ].append(
                        novo
                    )

                    atualizar_residencia(
                        residencia_selecionada
                    )

                    return redirect(
                        url_for(
                            "residencia",
                            residencia_id=(
                                residencia_id
                            )
                        )
                    )

            except ValueError:

                mensagem = (
                    "Informe valores "
                    "numéricos válidos."
                )

    return render_template(
        "novo_equipamento.html",
        residencia=(
            residencia_selecionada
        ),
        equipamentos_disponiveis=(
            EQUIPAMENTOS_DISPONIVEIS
        ),
        mensagem=mensagem
    )


@app.route(
    "/residencia/<int:residencia_id>/equipamento/"
    "<int:equipamento_indice>/remover"
)
def remover_equipamento(
    residencia_id,
    equipamento_indice
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    equipamentos = (
        residencia_selecionada.get(
            "equipamentos",
            []
        )
    )

    if (
        0
        <= equipamento_indice
        < len(
            equipamentos
        )
    ):

        equipamentos.pop(
            equipamento_indice
        )

        residencia_selecionada[
            "equipamentos"
        ] = equipamentos

        atualizar_residencia(
            residencia_selecionada
        )

    return redirect(
        url_for(
            "residencia",
            residencia_id=(
                residencia_id
            )
        )
    )


@app.route(
    "/residencia/<int:residencia_id>/solar",
    methods=["GET", "POST"]
)
def solar(
    residencia_id
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    equipamentos = (
        residencia_selecionada.get(
            "equipamentos",
            []
        )
    )

    resultado_consumo = (
        calcular_consumo(
            equipamentos
        )
    )

    consumo_mensal = (
        resultado_consumo[
            "consumo_mensal"
        ]
    )

    mensagem = ""

    if not equipamentos:
        mensagem = (
            "Cadastre pelo menos um equipamento "
            "antes de realizar o dimensionamento."
        )

    elif consumo_mensal <= 0:
        mensagem = (
            "O consumo mensal da residência deve "
            "ser maior que zero."
        )

    hsp = ""
    fonte_hsp = ""
    pr_percentual = 80

    usar_bateria = "nao"
    autonomia_horas = 8

    resultado_solar = None

    dimensionamento_salvo = (
        residencia_selecionada.get(
            "dimensionamento"
        )
    )

    if dimensionamento_salvo:

        hsp = (
            dimensionamento_salvo.get(
                "hsp",
                ""
            )
        )

        fonte_hsp = (
            dimensionamento_salvo.get(
                "fonte_hsp",
                ""
            )
        )

        pr_percentual = (
            dimensionamento_salvo.get(
                "pr_percentual",
                80
            )
        )

        cenario_com_bateria = (
            dimensionamento_salvo.get(
                "cenario_com_bateria"
            )
        )

        if cenario_com_bateria:

            usar_bateria = "sim"

            bateria_salva = (
                cenario_com_bateria.get(
                    "bateria"
                )
            )

            if bateria_salva:

                autonomia_horas = (
                    bateria_salva.get(
                        "autonomia_horas",
                        8
                    )
                )

        resultado_solar = {

            "consumo_diario": (
                resultado_consumo[
                    "consumo_diario"
                ]
            ),

            "hsp": hsp,

            "fonte_hsp": (
                fonte_hsp
            ),

            "pr_percentual": (
                pr_percentual
            ),

            "potencia_fv_kwp": (
                dimensionamento_salvo.get(
                    "potencia_fv_necessaria_kwp"
                )
            ),

            "geracao_diaria_kwh": (
                dimensionamento_salvo.get(
                    "geracao_diaria_kwh"
                )
            ),

            "geracao_mensal_kwh": (
                dimensionamento_salvo.get(
                    "geracao_mensal_kwh"
                )
            ),

            "atendimento_percentual": (
                dimensionamento_salvo.get(
                    "atendimento_percentual"
                )
            ),

            "atendimento_real_percentual": (
                dimensionamento_salvo.get(
                    "atendimento_real_percentual"
                )
            ),

            "energia_compensada_kwh": (
                dimensionamento_salvo.get(
                    "energia_compensada_kwh"
                )
            ),

            "energia_excedente_kwh": (
                dimensionamento_salvo.get(
                    "energia_excedente_kwh"
                )
            ),

            "modulo": (
                dimensionamento_salvo.get(
                    "modulo"
                )
            ),

            "inversor": (
                dimensionamento_salvo.get(
                    "inversor"
                )
            ),

            "cenario_sem_bateria": (
                dimensionamento_salvo.get(
                    "cenario_sem_bateria"
                )
            ),

            "cenario_com_bateria": (
                dimensionamento_salvo.get(
                    "cenario_com_bateria"
                )
            ),

            "orcamento_sem_bateria": (
                dimensionamento_salvo.get(
                    "orcamento_sem_bateria"
                )
            ),

            "orcamento_com_bateria": (
                dimensionamento_salvo.get(
                    "orcamento_com_bateria"
                )
            ),

            "economia_sem_bateria": (
                dimensionamento_salvo.get(
                    "economia_sem_bateria"
                )
            ),

            "economia_com_bateria": (
                dimensionamento_salvo.get(
                    "economia_com_bateria"
                )
            )
        }

    if request.method == "POST":

        hsp_texto = (
            request.form.get(
                "hsp",
                ""
            ).strip()
        )

        fonte_hsp = (
            request.form.get(
                "fonte_hsp",
                ""
            ).strip()
        )

        pr_texto = (
            request.form.get(
                "pr",
                ""
            ).strip()
        )

        usar_bateria = (
            request.form.get(
                "usar_bateria",
                "nao"
            )
        )

        autonomia_texto = (
            request.form.get(
                "autonomia_horas",
                "8"
            ).strip()
        )

        if (
            not hsp_texto
            or not fonte_hsp
            or not pr_texto
        ):

            mensagem = (
                "Preencha todos os campos obrigatórios."
            )

        elif not equipamentos:

            mensagem = (
                "Cadastre pelo menos um equipamento "
                "antes de realizar o dimensionamento."
            )

        elif consumo_mensal <= 0:

            mensagem = (
                "O consumo mensal da residência deve "
                "ser maior que zero."
            )

        else:

            try:

                hsp = float(
                    hsp_texto.replace(
                        ",",
                        "."
                    )
                )

                pr_percentual = float(
                    pr_texto.replace(
                        ",",
                        "."
                    )
                )

                pr = (
                    pr_percentual
                    / 100
                )

                if hsp <= 0:
                    raise ValueError(
                        "A HSP deve ser maior que zero."
                    )

                if (
                    pr_percentual <= 0
                    or pr_percentual > 100
                ):
                    raise ValueError(
                        "O PR deve estar entre 1% e 100%."
                    )

                if (
                    usar_bateria == "sim"
                    and not autonomia_texto
                ):
                    raise ValueError(
                        "Informe a autonomia desejada."
                    )

                resultado_solar = (
                    calcular_potencia_fv(
                        consumo_mensal,
                        hsp,
                        pr
                    )
                )

                resultado_solar[
                    "fonte_hsp"
                ] = fonte_hsp

                resultado_solar[
                    "pr_percentual"
                ] = pr_percentual


                modulos = (
                    carregar_modulos()
                )

                modulo_selecionado = (
                    selecionar_modulo(
                        resultado_solar[
                            "potencia_fv_kwp"
                        ],
                        modulos
                    )
                )

                resultado_solar[
                    "modulo"
                ] = modulo_selecionado


                inversores = (
                    carregar_inversores()
                )

                inversor_selecionado = (
                    selecionar_inversor(
                        modulo_selecionado,
                        inversores,
                        exigir_bateria=False
                    )
                )

                resultado_solar[
                    "inversor"
                ] = (
                    inversor_selecionado
                )


                resultado_solar[
                    "cenario_sem_bateria"
                ] = {
                    "modulo": (
                        modulo_selecionado
                    ),
                    "inversor": (
                        inversor_selecionado
                    ),
                    "bateria": None
                }

                resultado_solar[
                    "orcamento_sem_bateria"
                ] = criar_orcamento_sem_bateria(
                    modulo_selecionado,
                    inversor_selecionado
                )


                resultado_solar[
                    "cenario_com_bateria"
                ] = None

                resultado_solar[
                    "orcamento_com_bateria"
                ] = None


                if (
                    usar_bateria
                    == "sim"
                ):

                    autonomia_horas = float(
                        autonomia_texto.replace(
                            ",",
                            "."
                        )
                    )

                    if (
                        autonomia_horas <= 0
                        or autonomia_horas > 24
                    ):
                        raise ValueError(
                            "A autonomia deve estar entre "
                            "1 e 24 horas."
                        )

                    baterias = (
                        carregar_baterias()
                    )

                    bateria_selecionada = (
                        dimensionar_bateria(
                            resultado_consumo[
                                "consumo_diario"
                            ],
                            autonomia_horas,
                            baterias
                        )
                    )

                    sistema_com_bateria = (
                        selecionar_sistema_com_bateria(
                            resultado_solar[
                                "potencia_fv_kwp"
                            ],
                            modulos,
                            inversores
                        )
                    )

                    resultado_solar[
                        "cenario_com_bateria"
                    ] = {
                        "modulo": (
                            sistema_com_bateria[
                                "modulo"
                            ]
                        ),
                        "inversor": (
                            sistema_com_bateria[
                                "inversor"
                            ]
                        ),
                        "bateria": (
                            bateria_selecionada
                        )
                    }

                    resultado_solar[
                        "orcamento_com_bateria"
                    ] = criar_orcamento_com_bateria(
                        sistema_com_bateria[
                            "modulo"
                        ],
                        sistema_com_bateria[
                            "inversor"
                        ],
                        bateria_selecionada
                    )


                resultado_geracao = (
                    calcular_geracao_fv(
                        modulo_selecionado[
                            "potencia_instalada_kwp"
                        ],
                        hsp,
                        pr,
                        consumo_mensal
                    )
                )


                resultado_solar[
                    "geracao_diaria_kwh"
                ] = resultado_geracao[
                    "geracao_diaria_kwh"
                ]

                resultado_solar[
                    "geracao_mensal_kwh"
                ] = resultado_geracao[
                    "geracao_mensal_kwh"
                ]

                resultado_solar[
                    "atendimento_percentual"
                ] = resultado_geracao[
                    "atendimento_percentual"
                ]

                resultado_solar[
                    "atendimento_real_percentual"
                ] = resultado_geracao[
                    "atendimento_real_percentual"
                ]

                resultado_solar[
                    "energia_compensada_kwh"
                ] = resultado_geracao[
                    "energia_compensada_kwh"
                ]

                resultado_solar[
                    "energia_excedente_kwh"
                ] = resultado_geracao[
                    "energia_excedente_kwh"
                ]


                tarifa_kwh = residencia_selecionada[
                    "tarifa_kwh"
                ]

                energia_compensada_sem = resultado_solar[
                    "energia_compensada_kwh"
                ]

                economia_mensal_sem = (
                    energia_compensada_sem
                    * tarifa_kwh
                )

                economia_anual_sem = (
                    economia_mensal_sem
                    * 12
                )

                custo_total_sem = resultado_solar[
                    "orcamento_sem_bateria"
                ][
                    "custo_total"
                ]

                if economia_anual_sem > 0:
                    payback_sem = (
                        custo_total_sem
                        / economia_anual_sem
                    )
                else:
                    payback_sem = None

                resultado_solar[
                    "economia_sem_bateria"
                ] = {
                    "tarifa_kwh": round(
                        tarifa_kwh,
                        2
                    ),
                    "energia_compensada_kwh": round(
                        energia_compensada_sem,
                        2
                    ),
                    "economia_mensal": round(
                        economia_mensal_sem,
                        2
                    ),
                    "economia_anual": round(
                        economia_anual_sem,
                        2
                    ),
                    "payback_simples_anos": (
                        round(
                            payback_sem,
                            2
                        )
                        if payback_sem is not None
                        else None
                    )
                }


                resultado_solar[
                    "economia_com_bateria"
                ] = None

                if resultado_solar[
                    "cenario_com_bateria"
                ]:

                    modulo_com_bateria = resultado_solar[
                        "cenario_com_bateria"
                    ][
                        "modulo"
                    ]

                    resultado_geracao_com_bateria = (
                        calcular_geracao_fv(
                            modulo_com_bateria[
                                "potencia_instalada_kwp"
                            ],
                            hsp,
                            pr,
                            consumo_mensal
                        )
                    )

                    energia_compensada_com = (
                        resultado_geracao_com_bateria[
                            "energia_compensada_kwh"
                        ]
                    )

                    economia_mensal_com = (
                        energia_compensada_com
                        * tarifa_kwh
                    )

                    economia_anual_com = (
                        economia_mensal_com
                        * 12
                    )

                    custo_total_com = resultado_solar[
                        "orcamento_com_bateria"
                    ][
                        "custo_total"
                    ]

                    if economia_anual_com > 0:
                        payback_com = (
                            custo_total_com
                            / economia_anual_com
                        )
                    else:
                        payback_com = None

                    resultado_solar[
                        "economia_com_bateria"
                    ] = {
                        "tarifa_kwh": round(
                            tarifa_kwh,
                            2
                        ),
                        "energia_compensada_kwh": round(
                            energia_compensada_com,
                            2
                        ),
                        "economia_mensal": round(
                            economia_mensal_com,
                            2
                        ),
                        "economia_anual": round(
                            economia_anual_com,
                            2
                        ),
                        "payback_simples_anos": (
                            round(
                                payback_com,
                                2
                            )
                            if payback_com is not None
                            else None
                        )
                    }


                residencia_selecionada[
                    "dimensionamento"
                ] = {

                    "hsp": round(
                        hsp,
                        2
                    ),

                    "fonte_hsp": (
                        fonte_hsp
                    ),

                    "pr_percentual": round(
                        pr_percentual,
                        2
                    ),

                    "potencia_fv_necessaria_kwp": round(
                        resultado_solar[
                            "potencia_fv_kwp"
                        ],
                        2
                    ),

                    "geracao_diaria_kwh": round(
                        resultado_solar[
                            "geracao_diaria_kwh"
                        ],
                        2
                    ),

                    "geracao_mensal_kwh": round(
                        resultado_solar[
                            "geracao_mensal_kwh"
                        ],
                        2
                    ),

                    "atendimento_percentual": round(
                        resultado_solar[
                            "atendimento_percentual"
                        ],
                        2
                    ),

                    "atendimento_real_percentual": round(
                        resultado_solar[
                            "atendimento_real_percentual"
                        ],
                        2
                    ),

                    "energia_compensada_kwh": round(
                        resultado_solar[
                            "energia_compensada_kwh"
                        ],
                        2
                    ),

                    "energia_excedente_kwh": round(
                        resultado_solar[
                            "energia_excedente_kwh"
                        ],
                        2
                    ),

                    "modulo": {
                        **resultado_solar[
                            "modulo"
                        ],

                        "potencia_instalada_kwp": round(
                            resultado_solar[
                                "modulo"
                            ][
                                "potencia_instalada_kwp"
                            ],
                            2
                        ),

                        "preco_unitario": round(
                            resultado_solar[
                                "modulo"
                            ][
                                "preco_unitario"
                            ],
                            2
                        ),

                        "custo_total": round(
                            resultado_solar[
                                "modulo"
                            ][
                                "custo_total"
                            ],
                            2
                        )
                    },

                    "inversor": {
                        **resultado_solar[
                            "inversor"
                        ],

                        "voc_total": round(
                            resultado_solar[
                                "inversor"
                            ][
                                "voc_total"
                            ],
                            2
                        ),

                        "vmp_total": round(
                            resultado_solar[
                                "inversor"
                            ][
                                "vmp_total"
                            ],
                            2
                        ),

                        "isc_total": round(
                            resultado_solar[
                                "inversor"
                            ][
                                "isc_total"
                            ],
                            2
                        ),

                        "relacao_dc_ac": round(
                            resultado_solar[
                                "inversor"
                            ][
                                "relacao_dc_ac"
                            ],
                            2
                        )
                    },

                    "cenario_sem_bateria": (
                        resultado_solar[
                            "cenario_sem_bateria"
                        ]
                    ),

                    "cenario_com_bateria": (
                        resultado_solar[
                            "cenario_com_bateria"
                        ]
                    ),

                    "orcamento_sem_bateria": (
                        resultado_solar[
                            "orcamento_sem_bateria"
                        ]
                    ),

                    "orcamento_com_bateria": (
                        resultado_solar[
                            "orcamento_com_bateria"
                        ]
                    ),

                    "economia_sem_bateria": (
                        resultado_solar[
                            "economia_sem_bateria"
                        ]
                    ),

                    "economia_com_bateria": (
                        resultado_solar[
                            "economia_com_bateria"
                        ]
                    )
                }


                atualizar_residencia(
                    residencia_selecionada
                )

            except ValueError as erro:

                mensagem = str(
                    erro
                )

            except KeyError as erro:

                mensagem = (
                    "Não foi possível concluir o dimensionamento "
                    "porque um dado obrigatório não foi encontrado "
                    "nos arquivos de equipamentos: "
                    + str(erro)
                )

            except (FileNotFoundError, OSError):

                mensagem = (
                    "Não foi possível acessar um dos arquivos "
                    "de dados de módulos, inversores ou baterias."
                )

            except Exception:

                mensagem = (
                    "Não foi possível concluir o dimensionamento. "
                    "Verifique os dados informados e tente novamente."
                )

    return render_template(
        "solar.html",
        residencia=(
            residencia_selecionada
        ),
        consumo_mensal=(
            consumo_mensal
        ),
        resultado_solar=(
            resultado_solar
        ),
        mensagem=(
            mensagem
        ),
        hsp=(
            hsp
        ),
        fonte_hsp=(
            fonte_hsp
        ),
        pr_percentual=(
            pr_percentual
        ),
        usar_bateria=(
            usar_bateria
        ),
        autonomia_horas=(
            autonomia_horas
        )
    )


@app.route(
    "/residencia/<int:residencia_id>/relatorio.pdf"
)
def exportar_relatorio_pdf(
    residencia_id
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    dimensionamento = (
        residencia_selecionada.get(
            "dimensionamento"
        )
    )

    if not dimensionamento:

        return redirect(
            url_for(
                "solar",
                residencia_id=residencia_id
            )
        )

    equipamentos = (
        residencia_selecionada.get(
            "equipamentos",
            []
        )
    )

    resultado_consumo = (
        calcular_consumo(
            equipamentos
        )
    )

    consumo_mensal = (
        resultado_consumo[
            "consumo_mensal"
        ]
    )

    consumo_diario = (
        resultado_consumo[
            "consumo_diario"
        ]
    )

    memoria = BytesIO()

    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloSERS",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=18
    )

    subtitulo = ParagraphStyle(
        "SubtituloSERS",
        parent=estilos["Heading2"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=8
    )

    normal = estilos["BodyText"]

    elementos = []

    elementos.append(
        Paragraph(
            "SERS - Sistema de Dimensionamento Energético Residencial",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "Relatório final de dimensionamento fotovoltaico",
            estilos["Heading3"]
        )
    )

    elementos.append(
        Spacer(
            1,
            12
        )
    )

    elementos.append(
        Paragraph(
            "<b>Residência:</b> "
            + str(
                residencia_selecionada[
                    "nome"
                ]
            ),
            normal
        )
    )

    elementos.append(
        Paragraph(
            "<b>Cidade:</b> "
            + str(
                residencia_selecionada[
                    "cidade"
                ]
            ),
            normal
        )
    )

    elementos.append(
        Paragraph(
            "<b>Área:</b> "
            + f'{residencia_selecionada["area_m2"]:.2f} m²',
            normal
        )
    )

    elementos.append(
        Paragraph(
            "<b>Moradores:</b> "
            + str(
                residencia_selecionada[
                    "moradores"
                ]
            ),
            normal
        )
    )

    elementos.append(
        Spacer(
            1,
            12
        )
    )

    elementos.append(
        Paragraph(
            "Consumo da residência",
            subtitulo
        )
    )

    dados_consumo = [
        [
            "Indicador",
            "Valor"
        ],
        [
            "Consumo mensal",
            f"{consumo_mensal:.2f} kWh"
        ],
        [
            "Consumo diário",
            f"{consumo_diario:.2f} kWh/dia"
        ],
        [
            "Tarifa de energia",
            f'R$ {residencia_selecionada["tarifa_kwh"]:.2f} / kWh'
        ]
    ]

    tabela_consumo = Table(
        dados_consumo,
        colWidths=[
            220,
            220
        ]
    )

    tabela_consumo.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )

    elementos.append(
        tabela_consumo
    )

    elementos.append(
        Paragraph(
            "Dimensionamento fotovoltaico",
            subtitulo
        )
    )

    dados_dimensionamento = [
        [
            "Indicador",
            "Valor"
        ],
        [
            "HSP",
            f'{dimensionamento["hsp"]:.2f} h/dia'
        ],
        [
            "Fonte da HSP",
            str(
                dimensionamento[
                    "fonte_hsp"
                ]
            )
        ],
        [
            "PR",
            f'{dimensionamento["pr_percentual"]:.2f}%'
        ],
        [
            "Potência FV necessária",
            f'{dimensionamento["potencia_fv_necessaria_kwp"]:.2f} kWp'
        ],
        [
            "Geração diária",
            f'{dimensionamento["geracao_diaria_kwh"]:.2f} kWh/dia'
        ],
        [
            "Geração mensal",
            f'{dimensionamento["geracao_mensal_kwh"]:.2f} kWh/mês'
        ],
        [
            "Atendimento real",
            f'{dimensionamento["atendimento_real_percentual"]:.2f}%'
        ],
        [
            "Energia compensada",
            f'{dimensionamento["energia_compensada_kwh"]:.2f} kWh/mês'
        ],
        [
            "Energia excedente",
            f'{dimensionamento["energia_excedente_kwh"]:.2f} kWh/mês'
        ]
    ]

    tabela_dimensionamento = Table(
        dados_dimensionamento,
        colWidths=[
            220,
            220
        ]
    )

    tabela_dimensionamento.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )

    elementos.append(
        tabela_dimensionamento
    )

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "Cenário sem bateria",
            subtitulo
        )
    )

    cenario_sem = dimensionamento.get(
        "cenario_sem_bateria"
    )

    if cenario_sem:

        modulo_sem = cenario_sem[
            "modulo"
        ]

        inversor_sem = cenario_sem[
            "inversor"
        ]

        elementos.append(
            Paragraph(
                "<b>Módulos:</b> "
                + str(
                    modulo_sem[
                        "fabricante"
                    ]
                )
                + " "
                + str(
                    modulo_sem[
                        "modelo"
                    ]
                )
                + " - "
                + str(
                    modulo_sem[
                        "quantidade"
                    ]
                )
                + " unidade(s)",
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Inversor:</b> "
                + str(
                    inversor_sem[
                        "fabricante"
                    ]
                )
                + " "
                + str(
                    inversor_sem[
                        "modelo"
                    ]
                ),
                normal
            )
        )

    orcamento_sem = dimensionamento.get(
        "orcamento_sem_bateria"
    )

    if orcamento_sem:

        dados_orcamento_sem = [
            [
                "Equipamento",
                "Fabricante / Modelo",
                "Qtd.",
                "Unitário",
                "Subtotal"
            ]
        ]

        for item in orcamento_sem[
            "itens"
        ]:

            dados_orcamento_sem.append(
                [
                    item[
                        "equipamento"
                    ],
                    item[
                        "fabricante"
                    ]
                    + " "
                    + item[
                        "modelo"
                    ],
                    str(
                        item[
                            "quantidade"
                        ]
                    ),
                    f'R$ {item["preco_unitario"]:.2f}',
                    f'R$ {item["subtotal"]:.2f}'
                ]
            )

        tabela_orcamento_sem = Table(
            dados_orcamento_sem,
            colWidths=[
                105,
                150,
                45,
                75,
                75
            ]
        )

        tabela_orcamento_sem.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    )
                ]
            )
        )

        elementos.append(
            Spacer(
                1,
                8
            )
        )

        elementos.append(
            tabela_orcamento_sem
        )

        elementos.append(
            Paragraph(
                "<b>Total sem bateria:</b> "
                + f'R$ {orcamento_sem["custo_total"]:.2f}',
                normal
            )
        )

    economia_sem = dimensionamento.get(
        "economia_sem_bateria"
    )

    if economia_sem:

        elementos.append(
            Paragraph(
                "<b>Economia mensal:</b> "
                + f'R$ {economia_sem["economia_mensal"]:.2f}',
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Economia anual:</b> "
                + f'R$ {economia_sem["economia_anual"]:.2f}',
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Payback simples:</b> "
                + f'{economia_sem["payback_simples_anos"]:.2f} anos',
                normal
            )
        )

    cenario_com = dimensionamento.get(
        "cenario_com_bateria"
    )

    if cenario_com:

        elementos.append(
            Paragraph(
                "Cenário com bateria",
                subtitulo
            )
        )

        modulo_com = cenario_com[
            "modulo"
        ]

        inversor_com = cenario_com[
            "inversor"
        ]

        bateria = cenario_com[
            "bateria"
        ]

        elementos.append(
            Paragraph(
                "<b>Módulos:</b> "
                + str(
                    modulo_com[
                        "fabricante"
                    ]
                )
                + " "
                + str(
                    modulo_com[
                        "modelo"
                    ]
                )
                + " - "
                + str(
                    modulo_com[
                        "quantidade"
                    ]
                )
                + " unidade(s)",
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Inversor:</b> "
                + str(
                    inversor_com[
                        "fabricante"
                    ]
                )
                + " "
                + str(
                    inversor_com[
                        "modelo"
                    ]
                ),
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Bateria:</b> "
                + str(
                    bateria[
                        "fabricante"
                    ]
                )
                + " "
                + str(
                    bateria[
                        "modelo"
                    ]
                )
                + " - "
                + str(
                    bateria[
                        "quantidade"
                    ]
                )
                + " unidade(s)",
                normal
            )
        )

        elementos.append(
            Paragraph(
                "<b>Autonomia considerada:</b> "
                + f'{bateria["autonomia_horas"]:.2f} horas',
                normal
            )
        )

        orcamento_com = dimensionamento.get(
            "orcamento_com_bateria"
        )

        if orcamento_com:

            dados_orcamento_com = [
                [
                    "Equipamento",
                    "Fabricante / Modelo",
                    "Qtd.",
                    "Unitário",
                    "Subtotal"
                ]
            ]

            for item in orcamento_com[
                "itens"
            ]:

                dados_orcamento_com.append(
                    [
                        item[
                            "equipamento"
                        ],
                        item[
                            "fabricante"
                        ]
                        + " "
                        + item[
                            "modelo"
                        ],
                        str(
                            item[
                                "quantidade"
                            ]
                        ),
                        f'R$ {item["preco_unitario"]:.2f}',
                        f'R$ {item["subtotal"]:.2f}'
                    ]
                )

            tabela_orcamento_com = Table(
                dados_orcamento_com,
                colWidths=[
                    105,
                    150,
                    45,
                    75,
                    75
                ]
            )

            tabela_orcamento_com.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold"
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "PADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        )
                    ]
                )
            )

            elementos.append(
                Spacer(
                    1,
                    8
                )
            )

            elementos.append(
                tabela_orcamento_com
            )

            elementos.append(
                Paragraph(
                    "<b>Total com bateria:</b> "
                    + f'R$ {orcamento_com["custo_total"]:.2f}',
                    normal
                )
            )

        economia_com = dimensionamento.get(
            "economia_com_bateria"
        )

        if economia_com:

            elementos.append(
                Paragraph(
                    "<b>Economia mensal:</b> "
                    + f'R$ {economia_com["economia_mensal"]:.2f}',
                    normal
                )
            )

            elementos.append(
                Paragraph(
                    "<b>Economia anual:</b> "
                    + f'R$ {economia_com["economia_anual"]:.2f}',
                    normal
                )
            )

            elementos.append(
                Paragraph(
                    "<b>Payback simples:</b> "
                    + f'{economia_com["payback_simples_anos"]:.2f} anos',
                    normal
                )
            )

    elementos.append(
        Spacer(
            1,
            16
        )
    )

    elementos.append(
        Paragraph(
            "Observação: o payback apresentado é simples e considera "
            "o investimento inicial dividido pela economia anual estimada, "
            "sem considerar reajustes tarifários, inflação, manutenção "
            "ou custo de capital.",
            normal
        )
    )

    documento.build(
        elementos
    )

    memoria.seek(
        0
    )

    nome_arquivo = (
        "relatorio_sers_"
        + str(
            residencia_selecionada[
                "id"
            ]
        )
        + ".pdf"
    )

    return send_file(
        memoria,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )


@app.route(
    "/residencia/<int:residencia_id>/resultado-final"
)
def resultado_final(
    residencia_id
):

    if "usuario_id" not in session:

        return redirect(
            url_for(
                "login"
            )
        )

    residencia_selecionada = (
        buscar_residencia_por_id(
            residencia_id,
            session["usuario_id"]
        )
    )

    if (
        residencia_selecionada
        is None
    ):

        return redirect(
            url_for(
                "index"
            )
        )

    equipamentos = (
        residencia_selecionada.get(
            "equipamentos",
            []
        )
    )

    resultado_consumo = (
        calcular_consumo(
            equipamentos
        )
    )

    dimensionamento = (
        residencia_selecionada.get(
            "dimensionamento"
        )
    )

    if not dimensionamento:

        return redirect(
            url_for(
                "solar",
                residencia_id=residencia_id
            )
        )

    consumo_mensal = (
        resultado_consumo[
            "consumo_mensal"
        ]
    )

    consumo_diario = (
        resultado_consumo[
            "consumo_diario"
        ]
    )

    potencia_instalada = (
        resultado_consumo[
            "potencia_instalada"
        ]
    )

    custo_mensal_atual = (
        consumo_mensal
        * residencia_selecionada[
            "tarifa_kwh"
        ]
    )

    return render_template(
        "resultado_final.html",
        residencia=residencia_selecionada,
        equipamentos=equipamentos,
        consumo_mensal=consumo_mensal,
        consumo_diario=consumo_diario,
        potencia_instalada=potencia_instalada,
        custo_mensal_atual=custo_mensal_atual,
        dimensionamento=dimensionamento
    )


if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )