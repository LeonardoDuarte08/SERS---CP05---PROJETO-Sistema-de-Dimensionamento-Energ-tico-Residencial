from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dimensionamento import calcular_consumo

from dimensionamento import (
    calcular_consumo,
    calcular_potencia_fv,
    carregar_modulos,
    carregar_inversores,
    carregar_baterias,
    selecionar_modulo,
    selecionar_inversor
)

import json
import os


app = Flask(__name__)

app.secret_key = "sistema-energia-residencial"

ARQUIVO_LOGINS = "dados/logins.json"


def carregar_usuarios():
    if not os.path.exists(ARQUIVO_LOGINS):
        return []

    with open(
        ARQUIVO_LOGINS,
        "r",
        encoding="utf-8"
    ) as arquivo:

        try:
            return json.load(arquivo)

        except json.JSONDecodeError:
            return []


def salvar_usuarios(usuarios):

    os.makedirs(
        os.path.dirname(ARQUIVO_LOGINS),
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


def gerar_novo_id(usuarios):

    if not usuarios:
        return 1

    maior_id = max(
        usuario["id"]
        for usuario in usuarios
    )

    return maior_id + 1


@app.route("/")
def index():

    if "usuario_id" not in session:
        return redirect(
            url_for("login")
        )

    todas_residencias = carregar_residencias()

    residencias_usuario = [
        residencia
        for residencia in todas_residencias
        if residencia["usuario_id"] == session["usuario_id"]
    ]

    return render_template(
        "index.html",
        usuario_nome=session.get("usuario_nome"),
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

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
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

            usuarios = carregar_usuarios()

            email_existente = any(
                usuario["email"] == email
                for usuario in usuarios
            )

            if email_existente:

                mensagem = (
                    "Este e-mail já está cadastrado."
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

        usuarios = carregar_usuarios()

        usuario_encontrado = None

        for usuario in usuarios:

            if usuario["email"] == email:

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

                session["usuario_id"] = (
                    usuario_encontrado[
                        "id"
                    ]
                )

                session["usuario_nome"] = (
                    usuario_encontrado[
                        "nome"
                    ]
                )

                session["usuario_email"] = (
                    usuario_encontrado[
                        "email"
                    ]
                )

                return redirect(
                    url_for("index")
                )

            else:

                mensagem = (
                    "E-mail ou senha "
                    "inválidos."
                )

    return render_template(
        "login.html",
        mensagem=mensagem
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

ARQUIVO_RESIDENCIAS = "dados/residencias.json"


def carregar_residencias():
    if not os.path.exists(ARQUIVO_RESIDENCIAS):
        return []

    with open(
        ARQUIVO_RESIDENCIAS,
        "r",
        encoding="utf-8"
    ) as arquivo:
        try:
            return json.load(arquivo)
        except json.JSONDecodeError:
            return []


def salvar_residencias(residencias):
    os.makedirs(
        os.path.dirname(ARQUIVO_RESIDENCIAS),
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


def gerar_novo_id_residencia(residencias):
    if not residencias:
        return 1

    return max(
        residencia["id"]
        for residencia in residencias
    ) + 1

def buscar_residencia_por_id(residencia_id, usuario_id):
    residencias = carregar_residencias()

    for residencia in residencias:
        if (
            residencia["id"] == residencia_id
            and residencia["usuario_id"] == usuario_id
        ):
            return residencia

    return None

def atualizar_residencia(residencia_atualizada):
    residencias = carregar_residencias()

    for i, residencia in enumerate(residencias):
        if residencia["id"] == residencia_atualizada["id"]:
            residencias[i] = residencia_atualizada
            break

    salvar_residencias(residencias)

@app.route(
    "/residencia/nova",
    methods=["GET", "POST"]
)
def nova_residencia():

    if "usuario_id" not in session:
        return redirect(
            url_for("login")
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
            mensagem = "Preencha todos os campos."

        else:
            try:
                area = float(area)
                moradores = int(moradores)
                tarifa = float(tarifa)

                if area <= 0:
                    mensagem = "A área deve ser maior que zero."

                elif moradores <= 0:
                    mensagem = "Informe pelo menos um morador."

                elif tarifa <= 0:
                    mensagem = "A tarifa deve ser maior que zero."

                else:
                    residencias = carregar_residencias()

                    nova = {
                        "id": gerar_novo_id_residencia(
                            residencias
                        ),
                        "usuario_id": session["usuario_id"],
                        "nome": nome,
                        "cidade": cidade,
                        "area_m2": area,
                        "moradores": moradores,
                        "tarifa_kwh": tarifa,
                        "equipamentos": []
                    }

                    residencias.append(nova)

                    salvar_residencias(residencias)

                    return redirect(
                        url_for("index")
                    )

            except ValueError:
                mensagem = (
                    "Preencha os valores numéricos corretamente."
                )

    return render_template(
        "nova_residencia.html",
        mensagem=mensagem
    )

@app.route("/residencia/<int:residencia_id>")
def residencia(residencia_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    residencia_selecionada = buscar_residencia_por_id(
        residencia_id,
        session["usuario_id"]
    )

    if residencia_selecionada is None:
        return redirect(url_for("index"))

    equipamentos = residencia_selecionada.get(
        "equipamentos",
        []
    )

    resultado_consumo = calcular_consumo(
        equipamentos
    )

    consumo_mensal = resultado_consumo[
        "consumo_mensal"
    ]

    consumo_diario = resultado_consumo[
        "consumo_diario"
    ]

    potencia_instalada = resultado_consumo[
        "potencia_instalada"
    ]

    custo_mensal = (
        consumo_mensal
        * residencia_selecionada["tarifa_kwh"]
    )

    return render_template(
        "residencia.html",
        residencia=residencia_selecionada,
        equipamentos=equipamentos,
        consumo_mensal=consumo_mensal,
        consumo_diario=consumo_diario,
        custo_mensal=custo_mensal,
        potencia_instalada=potencia_instalada
    )

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

@app.route(
    "/residencia/<int:residencia_id>/equipamento/novo",
    methods=["GET", "POST"]
)
def novo_equipamento(residencia_id):

    if "usuario_id" not in session:
        return redirect(
            url_for("login")
        )

    residencia_selecionada = buscar_residencia_por_id(
        residencia_id,
        session["usuario_id"]
    )

    if residencia_selecionada is None:
        return redirect(
            url_for("index")
        )

    mensagem = ""

    if request.method == "POST":

        nome_equipamento = request.form.get(
            "equipamento",
            ""
        )

        quantidade = request.form.get(
            "quantidade",
            ""
        ).strip()

        horas_dia = request.form.get(
            "horas_dia",
            ""
        ).strip()

        equipamento_selecionado = None

        for equipamento in EQUIPAMENTOS_DISPONIVEIS:
            if equipamento["nome"] == nome_equipamento:
                equipamento_selecionado = equipamento
                break

        if equipamento_selecionado is None:
            mensagem = "Selecione um equipamento válido."

        elif not quantidade or not horas_dia:
            mensagem = "Preencha todos os campos."

        else:
            try:
                quantidade = int(quantidade)
                horas_dia = float(horas_dia)

                if quantidade <= 0:
                    mensagem = "A quantidade deve ser maior que zero."

                elif horas_dia <= 0 or horas_dia > 24:
                    mensagem = (
                        "As horas de uso devem estar entre 0 e 24."
                    )

                else:

                    novo = {
                        "nome": equipamento_selecionado["nome"],
                        "potencia_w": equipamento_selecionado["potencia_w"],
                        "quantidade": quantidade,
                        "horas_dia": horas_dia
                    }

                    residencia_selecionada[
                        "equipamentos"
                    ].append(novo)

                    atualizar_residencia(
                        residencia_selecionada
                    )

                    return redirect(
                        url_for(
                            "residencia",
                            residencia_id=residencia_id
                        )
                    )

            except ValueError:
                mensagem = (
                    "Informe valores numéricos válidos."
                )

    return render_template(
        "novo_equipamento.html",
        residencia=residencia_selecionada,
        equipamentos_disponiveis=EQUIPAMENTOS_DISPONIVEIS,
        mensagem=mensagem
    )

@app.route(
    "/residencia/<int:residencia_id>/equipamento/<int:equipamento_indice>/remover"
)
def remover_equipamento(
    residencia_id,
    equipamento_indice
):

    if "usuario_id" not in session:
        return redirect(
            url_for("login")
        )

    residencia_selecionada = buscar_residencia_por_id(
        residencia_id,
        session["usuario_id"]
    )

    if residencia_selecionada is None:
        return redirect(
            url_for("index")
        )

    equipamentos = residencia_selecionada.get(
        "equipamentos",
        []
    )

    if 0 <= equipamento_indice < len(equipamentos):
        equipamentos.pop(equipamento_indice)

        residencia_selecionada[
            "equipamentos"
        ] = equipamentos

        atualizar_residencia(
            residencia_selecionada
        )

    return redirect(
        url_for(
            "residencia",
            residencia_id=residencia_id
        )
    )

@app.route(
    "/residencia/<int:residencia_id>/solar",
    methods=["GET", "POST"]
)
def solar(residencia_id):

    if "usuario_id" not in session:
        return redirect(
            url_for("login")
        )

    residencia_selecionada = buscar_residencia_por_id(
        residencia_id,
        session["usuario_id"]
    )

    if residencia_selecionada is None:
        return redirect(
            url_for("index")
        )

    equipamentos = residencia_selecionada.get(
        "equipamentos",
        []
    )

    resultado_consumo = calcular_consumo(
        equipamentos
    )

    consumo_mensal = resultado_consumo[
        "consumo_mensal"
    ]

    mensagem = ""
    resultado_solar = None

    hsp = ""
    fonte_hsp = ""
    pr_percentual = 80

    if request.method == "POST":

        hsp_texto = request.form.get(
            "hsp",
            ""
        ).strip()

        fonte_hsp = request.form.get(
            "fonte_hsp",
            ""
        ).strip()

        pr_texto = request.form.get(
            "pr",
            ""
        ).strip()

        if (
            not hsp_texto
            or not fonte_hsp
            or not pr_texto
        ):
            mensagem = (
                "Preencha todos os campos."
            )

        else:

            try:
                hsp = float(
                    hsp_texto.replace(",", ".")
                )

                pr_percentual = float(
                    pr_texto.replace(",", ".")
                )

                pr = pr_percentual / 100

                resultado_solar = calcular_potencia_fv(
                    consumo_mensal,
                    hsp,
                    pr
                )

                modulos = carregar_modulos()

                modulo_selecionado = selecionar_modulo(
                    resultado_solar["potencia_fv_kwp"],
                    modulos
                )

                resultado_solar[
                    "modulo"
                ] = modulo_selecionado

                inversores = carregar_inversores()

                inversor_selecionado = selecionar_inversor(
                    modulo_selecionado,
                    inversores
                )

                resultado_solar[
                    "inversor"
                ] = inversor_selecionado

                resultado_solar[
                    "fonte_hsp"
                ] = fonte_hsp

                resultado_solar[
                    "pr_percentual"
                ] = pr_percentual

            except ValueError as erro:
                mensagem = str(erro)

    return render_template(
        "solar.html",
        residencia=residencia_selecionada,
        consumo_mensal=consumo_mensal,
        resultado_solar=resultado_solar,
        mensagem=mensagem,
        hsp=hsp,
        fonte_hsp=fonte_hsp,
        pr_percentual=pr_percentual
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )