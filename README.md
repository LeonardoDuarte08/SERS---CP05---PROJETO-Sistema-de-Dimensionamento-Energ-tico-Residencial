# SERS — Sistema de Dimensionamento Energético Residencial - CP 04, 05 e 06

Projeto desenvolvido para a disciplina de **Prompt and Artificial Intelligence**, com o objetivo de criar uma aplicação web capaz de realizar o dimensionamento energético de uma residência e simular cenários de geração fotovoltaica com e sem armazenamento em bateria.

A aplicação foi desenvolvida em **Python com Flask** e utiliza arquivos JSON para persistência de dados e arquivos CSV como base para seleção de módulos fotovoltaicos, inversores e baterias.

## Funcionalidades

O sistema permite:

- cadastro de usuários;
- login e logout;
- cadastro de múltiplas residências;
- cadastro de equipamentos elétricos por residência;
- cálculo do consumo mensal e diário;
- cálculo da potência instalada;
- cálculo do custo mensal estimado de energia;
- dimensionamento do sistema fotovoltaico;
- utilização de HSP (Horas de Sol Pleno);
- aplicação do PR (Performance Ratio);
- seleção automática de módulos fotovoltaicos;
- seleção de inversores tecnicamente compatíveis;
- verificação de tensão, corrente, potência e faixa de MPPT;
- cálculo da geração diária e mensal estimada;
- comparação entre geração e consumo;
- cálculo da energia compensada e excedente;
- criação de cenário sem bateria;
- criação de cenário com bateria;
- dimensionamento automático da bateria de acordo com a autonomia escolhida;
- comparação técnica entre os dois cenários;
- cálculo do orçamento detalhado;
- cálculo da economia mensal e anual estimada;
- cálculo do payback simples;
- tela final consolidada;
- persistência dos dimensionamentos realizados;
- recuperação de dimensionamentos anteriores;
- exportação do relatório final em PDF;
- validação de campos e tratamento de erros.

## Tecnologias utilizadas

- Python
- Flask
- HTML
- CSS
- JSON
- CSV
- ReportLab

## Estrutura do projeto

```text
SERS/
│
├── app.py
├── dimensionamento.py
├── calculadora_consumo.py
│
├── dados/
│   ├── logins.json
│   ├── residencias.json
│   └── arquivos CSV de módulos, inversores e baterias
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── cadastro.html
│   ├── nova_residencia.html
│   ├── residencia.html
│   ├── novo_equipamento.html
│   ├── solar.html
│   └── resultado_final.html
│
└── README.md
```

## Como instalar

É necessário ter o **Python 3** instalado.

Clone o repositório:

```bash
git clone https://github.com/LeonardoDuarte08/SERS---CP04---PROJETO-Sistema-de-Dimensionamento-Energ-tico-Residencial.git
```

Entre na pasta do projeto:

```bash
cd SERS---CP04---PROJETO-Sistema-de-Dimensionamento-Energ-tico-Residencial
```

Instale as bibliotecas necessárias:

```bash
py -m pip install flask reportlab
```

Caso esteja utilizando Linux ou macOS:

```bash
python3 -m pip install flask reportlab
```

## Como executar

No terminal, dentro da pasta do projeto, execute:

```bash
py app.py
```

Ou, em Linux/macOS:

```bash
python3 app.py
```

A aplicação será iniciada localmente.

Acesse pelo navegador:

```text
http://127.0.0.1:5001
```

## Fluxo de utilização

1. Criar uma conta de usuário.
2. Fazer login.
3. Cadastrar uma residência.
4. Informar área, número de moradores e tarifa de energia.
5. Cadastrar os equipamentos elétricos utilizados na residência.
6. Acessar o recurso de dimensionamento solar.
7. Informar HSP, fonte utilizada para a HSP, PR, utilização ou não de bateria e autonomia desejada quando aplicável.
8. Solicitar o dimensionamento.
9. Visualizar os resultados técnicos e econômicos.
10. Abrir a tela de resultado final consolidado.
11. Exportar o relatório em PDF.

## Cálculo do consumo

O consumo mensal de cada equipamento é calculado considerando:

```text
Potência × Quantidade × Horas de uso por dia × 30 dias
```

O resultado é convertido de Wh para kWh.

A soma dos equipamentos representa o consumo mensal estimado da residência.

## Dimensionamento fotovoltaico

A potência fotovoltaica necessária é calculada utilizando:

```text
Potência FV = Consumo diário / (HSP × PR)
```

Onde:

- **Consumo diário** é o consumo médio da residência em kWh/dia;
- **HSP** representa as Horas de Sol Pleno;
- **PR** representa o Performance Ratio do sistema.

Após o cálculo da potência necessária, o sistema seleciona automaticamente uma combinação de módulos e inversores.

## Seleção de módulos e inversores

Os equipamentos são carregados a partir dos datasets em CSV.

O sistema verifica a compatibilidade do inversor com o arranjo fotovoltaico considerando critérios como:

- potência máxima de entrada FV;
- tensão máxima;
- faixa de operação do MPPT;
- tensão de circuito aberto;
- tensão de máxima potência;
- corrente de curto-circuito;
- compatibilidade com bateria quando necessária.

O objetivo é evitar a escolha de equipamentos apenas pelo menor preço sem considerar a compatibilidade técnica.

## Geração de energia

Após a seleção dos equipamentos, o sistema estima:

- geração diária;
- geração mensal;
- percentual de atendimento do consumo;
- percentual real de atendimento;
- energia compensada;
- energia excedente.

A energia compensada é limitada ao consumo mensal da residência.

## Cenários analisados

### Cenário sem bateria

Utiliza módulos fotovoltaicos e inversor on-grid compatível.

### Cenário com bateria

Utiliza módulos fotovoltaicos, inversor compatível com armazenamento e bateria dimensionada de acordo com a autonomia escolhida.

O sistema procura uma combinação tecnicamente compatível entre módulo, inversor e bateria.

## Dimensionamento da bateria

Quando o usuário escolhe utilizar bateria, o sistema considera:

- consumo diário;
- autonomia desejada em horas;
- capacidade nominal;
- profundidade de descarga (DoD);
- eficiência;
- quantidade de baterias necessária.

A aplicação seleciona automaticamente uma opção disponível no dataset.

## Orçamento

O orçamento apresenta:

- equipamento;
- fabricante e modelo;
- quantidade;
- preço unitário;
- subtotal;
- custo total do cenário.

São apresentados valores independentes para os cenários com e sem bateria.

## Economia e payback

A economia mensal estimada utiliza a tarifa de energia da residência e a energia mensal compensada.

A economia anual corresponde à economia mensal multiplicada por 12.

O sistema também calcula o **payback simples**:

```text
Payback simples = Investimento inicial / Economia anual estimada
```

O cálculo não considera inflação, reajustes futuros da tarifa, manutenção ou custo de capital.

## Persistência dos dados

Os dados são associados ao usuário e à residência.

O sistema mantém:

- usuários cadastrados;
- residências;
- equipamentos;
- dimensionamentos;
- cenários calculados;
- orçamento;
- dados econômicos.

Ao acessar novamente uma residência, o dimensionamento salvo pode ser recuperado sem a necessidade de realizar todo o processo novamente.

## Relatório em PDF

Na tela de resultado final existe a opção **Exportar relatório em PDF**.

O relatório contém:

- dados da residência;
- informações de consumo;
- dados do dimensionamento solar;
- geração estimada;
- cenário sem bateria;
- cenário com bateria;
- equipamentos selecionados;
- orçamento;
- economia estimada;
- payback simples.

A geração do PDF utiliza a biblioteca **ReportLab**.

## Validações

A aplicação possui validações para:

- campos obrigatórios;
- HSP maior que zero;
- PR entre 1% e 100%;
- autonomia entre 1 e 24 horas;
- residência sem equipamentos;
- consumo inválido;
- ausência de módulo compatível;
- ausência de inversor compatível;
- ausência de inversor compatível com bateria;
- ausência de bateria disponível.

Quando ocorre algum problema, o sistema apresenta uma mensagem para o usuário em vez de interromper a aplicação.

## Integrantes

- Leonardo Duarte — RM 569029
- Enzo de Nadai — RM 569985
- Eduardo Oliveira — RM 570374
- João Pedro Conturbia — RM 569788