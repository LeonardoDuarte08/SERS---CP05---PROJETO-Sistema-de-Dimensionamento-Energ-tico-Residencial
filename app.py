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

    return render_template(
        "index.html",
        usuario_nome=session.get(
            "usuario_nome"
        )
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


if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )