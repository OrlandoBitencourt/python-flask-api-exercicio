"""
    Exercício 2
    Escola:
        A escola deve ser capaz de criar uma prova, onde cada questão dela tenha um peso exato.
        A soma de todos os pesos não poderá passar de 10 (nota máxima). Caso passe de 10, a prova não deverá ser salva e o
        usuário deverá ser avisado que há um erro nos pesos.
        Nenhuma questão poderá ter peso 0.
        Os pesos poderão ser números decimais, porém com no máximo 3 casas decimais.
        Essa prova poderá ter de 1 a 20 questões e todas são de múltipla escolha.
        Cada prova deverá ser salva com um id (que pode ser gerado pelo banco).
        Não será possível alterar um prova depois de salva.
        Deve-se ter em banco todos os alunos que estão matriculados na escola.
        Apenas alunos que estão matriculados poderão fazer as provas.

        Rotas Escola:
        Para acessar cada uma das rotas, a escola deve usar uma chave de acesso.
        Ter um rota para conseguir listar todos os alunos matriculados.
        Terá uma rota onde será possível criar a prova. O usuário deverá entrar com um json contendo Nome da prova,
        número da questão, resposta correta da questão e peso da questão.
        Ex: {
            "Nome":"Ciências - Reprodução humana",
            "1":{
                "Resposta correta":"A",
                "Peso":5},
            "2":{
                "Resposta correta":"C",
                "Peso":5}
            }
        Ter uma rota onde é possível listar todas as provas (Somente mostrar o id e o nome da prova na listagem)

    Aluno:
    O aluno deverá conseguir se matricular na escola com seu Nome, data de nascimento (o banco deverá gerar um número de
    matricula, e esse número deve ser retornado ao aluno após concluir a matricula).
    O aluno precisa selecionar uma prova para fazer
    Ao fazer a prova, o aluno poderá "assinalar" somente uma alternativa por questão da prova.

    Rotas Aluno:
    Para acessar qualquer uma das rotas, o aluno deverá usar seu número de matricula.
    Ter uma rota onde é possível listar todas as provas (Somente mostrar o id e o nome da prova na listagem)
    Ter uma rota onde o aluno coloque o id da prova e liste todas as questões e alternativas da prova.
    Ex de retorno:
    1 - A, B, C
    2 - 1, 2, 3, 4, 5
    Não será necessário mostrar um enunciado para as questões.

    Terá uma rota onde o aluno fará a prova. Ele precisa mandar o id da prova desejada, o número da questão e a
    resposta.
    Ex: {
        "id":"1234",
        "1":"C",
        "2":"B"
        }
    Obs: O aluno é obrigado a mandar todas as questões da prova com resposta, mesmo que ela seja nula (string vazia).
    Caso o aluno não responda alguma das questões, deve retornar um erro.
    Caso a alternativa de resposta escolhida esteja fora das existentes, deve se considerar que ele errou a resposta.
    Caso não haja erro no json, a nota do aluno deve ser retornada.

"""

import pymongo
from flask import Flask, request, Response
from bson import ObjectId
import json
import uuid

app = Flask(__name__)

conn = pymongo.MongoClient("mongodb://localhost:27017/")
db = conn['escola_alf']
escola = db['escola']
alunos = db['alunos']
provas = db['provas']
respostas = db['respostas']


@app.route("/")
def index():
    return "HELLO WORLD!"


@app.route("/cadastro-aluno", methods=['POST'])
def cadastrar_aluno():
    raw_request = request.data.decode("utf-8")
    dict_values = json.loads(raw_request)

    dict_values['matricula'] = str(uuid.uuid4().int)

    try:
        alunos.insert_one({'nome': dict_values['nome'], 'nascimento': dict_values['idade'], 'matricula': dict_values['matricula']})

        return gera_response(201, "matricula", dict_values['matricula'], "Criado com sucesso.")
    except Exception as erro:
        print(str(erro), str(erro.args))

        return gera_response(400, "aluno", {}, "Erro ao cadastrar")


@app.route("/provas/<matricula>", methods=['GET'])
def provas(matricula):
    if valida_matricula(matricula):
        provas_disponiveis = []
        lista_provas = db.provas.find({})

        for prova in lista_provas:
            provas_disponiveis.append({'id': str(prova['_id']), "nome": prova['nome']})

        return gera_response(200, "provas", provas_disponiveis, "ok")

    return gera_response(400, "provas", {}, "matricula inválida")


@app.route("/prova/<matricula>/<id>", methods=['GET'])
def prova(matricula, id):
    if valida_matricula(matricula):
        provas_disponiveis = []

        try:
            lista_provas = db.provas.find({'_id': ObjectId(id)})

            for prova in lista_provas:

                for item in prova['questoes']:
                    del prova['questoes'][item]['correta']

                provas_disponiveis.append({'id': str(prova['_id']),
                                           'nome': prova['nome'],
                                           'questoes': prova['questoes']})

            return gera_response(200, "prova", provas_disponiveis, "ok")
        except:
            return gera_response(400, "prova", {}, "Erro localizar prova")

    return gera_response(400, "prova", {}, "Erro localizar matricula")


@app.route("/prova/<matricula>/<id>", methods=['POST'])
def responder_prova(matricula, id):
    matriculas_lst = []
    provas_lst = []
    resposta = []

    if valida_matricula(matricula):
        if valida_prova(id):
            raw_request = request.data.decode("utf-8")
            dict_values = json.loads(raw_request)

            lista_provas = db.provas.find({'_id': ObjectId(id)})
            lista_respostas = db.respostas.find({})

            for prova in lista_provas:
                nota_aluno = 0

                for resposta_prova in lista_respostas:
                    matriculas_lst.append(str(int(resposta_prova['matricula'])))
                    provas_lst.append(str(resposta_prova['prova']))
                    resposta.append(resposta_prova)

                    if str(dict_values['matricula']) == str(int(resposta_prova['matricula'])) and str(id) == str(resposta_prova['prova']):
                        return gera_response(400, "prova", {}, "Você já respondeu a prova")

                if len(prova['questoes']) == len(dict_values['respostas_aluno']) and len(prova['questoes']) != 0:
                    for questao in range(1, len(prova['questoes'])):
                        if dict_values['respostas_aluno'][f'{questao}'] in prova['questoes'][f'{questao}']['alternativas']:
                            if str(dict_values['respostas_aluno'][f'{questao}']) == str(prova['questoes'][f'{questao}']['correta']):
                                nota_aluno += float(prova['questoes'][f'{questao}']['peso'])

                    db.respostas.insert_one({"matricula": dict_values["matricula"],
                                            "prova": id,
                                            "nota": nota_aluno,
                                            "respostas_aluno": dict_values["respostas_aluno"]})

                    return gera_response(201, "prova", prova['nome'], f"Respondida com sucesso, nota: {nota_aluno}")
                else:
                    return gera_response(400, "prova", {}, "Erro responder prova, alternativa nao localizada na questao.")

            return gera_response(400, "prova", {}, "Erro responder prova, numero de questoes respondidas incorreto.")

        return gera_response(400, "prova", {}, "Erro responder prova, id prova incorreto")

    return gera_response(400, "prova", {}, "Erro responder prova, matricula inválida")


@app.route("/alunos/<chave>", methods=['GET'])
def alunos(chave):
    if valida_chave_escola(chave):
        alunos_disponiveis = []
        lista_alunos = db.alunos.find({})
        for aluno in lista_alunos:
            alunos_disponiveis.append({"id": str(aluno['_id']),
                                       "matricula": aluno['matricula'],
                                       "nome": aluno['nome'],
                                       "nascimento": aluno['nascimento']})

        return gera_response(200, "alunos", alunos_disponiveis, "ok")

    return gera_response(400, "alunos", {}, "chave escola inválida")


@app.route("/cadastro-provas/<chave>", methods=['POST'])
def cadastro_provas(chave: str):
    if valida_chave_escola(chave):

        raw_request = request.data.decode("utf-8")
        dict_values = json.loads(raw_request)
        peso_questoes = 0
        try:
            for questao in dict_values['questoes']:
                peso_questoes += float(dict_values['questoes'][f'{questao}']['peso'])

            if peso_questoes > 10 or peso_questoes < 0:
                return gera_response(400, "cadastro-provas", {}, "peso incorreto")
        except:
            return gera_response(400, "cadastro-provas", {}, "peso incorreto")

        db.provas.insert_one({"nome": dict_values["nome"],
                              "questoes": dict_values["questoes"]})

        return gera_response(200, "cadastro-provas", dict_values, "ok")

    return gera_response(400, "cadastro-provas", {}, "chave escola inválida")


def valida_chave_escola(chave: str) -> bool:
    escola = db.escola.find({'_id': ObjectId(chave)})
    try:
        if escola[0] is not None:
            return True
    except:
        return False


def valida_prova(id: str) -> bool:
    prova = db.provas.find({'_id': ObjectId(id)})
    try:
        if prova[0] is not None:
            return True
    except:
        return False


def valida_matricula(matricula: int) -> bool:
    aluno = db.alunos.find({'matricula': matricula})
    try:
        if aluno[0] is not None:
            return True
    except:
        return False


def gera_response(status, nome_conteudo, conteudo, mensagem=False):
    body = {nome_conteudo: conteudo}
    if mensagem:
        body["mensagem"] = mensagem

    return Response(json.dumps(body), status=status, mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)
