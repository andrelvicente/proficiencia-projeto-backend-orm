# Gerenciador de Projetos IoT (Backend FastAPI)

Este é um sistema backend robusto para gerenciamento de projetos de Internet das Coisas (IoT), desenvolvido em Python com **FastAPI** e **SQLAlchemy**. Ele atende aos requisitos de proficiência da disciplina, incluindo operações CRUD completas, suporte a HATEOAS, mapeamento ORM, controle de transações ACID e autenticação baseada em tokens.

-----

## Data de Apresentação e Local (aprovadoo🎉🎉🎉)

  * **Data:** 09/07/2025
  * **Hora:** 18:10
  * **Local:** Laboratório 6

-----

## Visão Geral do Projeto

O sistema permite que usuários gerenciem seus projetos de IoT, associando dispositivos, sensores e coletando dados. A organização é facilitada pelo uso de tags, que podem ser aplicadas tanto a projetos quanto a dispositivos.

### Entidades Principais:

  * **Usuário (`User`):** Gerencia o acesso ao sistema e é proprietário dos projetos.
  * **Projeto (`Project`):** Representa um projeto lógico de IoT, agrupando dispositivos e tags.
  * **Dispositivo (`Device`):** Componente de hardware físico (sensor, atuador, gateway, etc.) associado a um projeto.
  * **Sensor (`Sensor`):** Uma especialização de `Device` que coleta dados.
  * **Dado do Sensor (`SensorData`):** Registra as leituras temporais de um sensor.
  * **Tag (`Tag`):** Rótulos flexíveis para categorizar `Project`s e `Device`s (relacionamento Many-to-Many).

### Mapeamentos e Relacionamentos:

  * **Many-to-One:**
      * `Project` para `User`
      * `Device` para `Project`
      * `Sensor` para `Device`
      * `SensorData` para `Sensor`
  * **Many-to-Many:**
      * `Project` para `Tag` (via tabela `project_tags`)
      * `Device` para `Tag` (via tabela `device_tags`)

-----

## Requisitos Técnicos Atendidos:

1.  **API RESTful Completa (CRUD):** Implementa operações de `Criar` (POST), `Atualizar` (PUT), `Excluir` (DELETE), `Listar Todos` (GET) e `Buscar por ID` (GET) para todas as entidades. Pesquisas por campos textuais também estão disponíveis em alguns endpoints.
2.  **Suporte a HATEOAS:** As respostas dos endpoints incluem links de hipermídia (`_links`) que guiam a navegação da API, seguindo o padrão HATEOAS.
3.  **Mapeamento Objeto-Relacional (ORM):** Utiliza **SQLAlchemy** como ORM para mapear as entidades Python para o banco de dados PostgreSQL, abstraindo a camada de persistência.
4.  **Controle de Transações ACID:** A camada de serviço (`app/services/`) garante a atomicidade e integridade dos dados através do uso de transações explícitas do SQLAlchemy (`db.begin_nested()` e `db.commit()`), assegurando que operações complexas (ex: criar um projeto com tags) sejam revertidas em caso de falha.
5.  **Autenticação Baseada em Tokens:** Implementa um mecanismo de autenticação via **JWT (JSON Web Tokens)** para proteger os endpoints da aplicação. Usuários se registram, fazem login para obter um token de acesso, e este token é necessário para acessar a maioria dos recursos.

-----

## Estrutura do Projeto

O projeto segue um padrão de arquitetura em camadas para melhor organização, separação de responsabilidades e manutenibilidade:

```
├── .env                  # Variáveis de ambiente
├── Dockerfile            # Configuração para construir a imagem Docker da API
├── docker-compose.yml    # Orquestração de serviços (API e Banco de Dados)
├── main.py               # Ponto de entrada da aplicação FastAPI
├── requirements.txt      # Dependências do projeto Python
└── app/
    ├── api/
    │   └── v1/
    │       └── endpoints/  # Definição dos endpoints da API (rotas)
    ├── core/               # Configurações globais, segurança (JWT, hash de senha), dependências
    ├── db/                 # Modelos SQLAlchemy e configuração de sessão do banco de dados
    ├── schemas/            # Modelos Pydantic para validação e serialização de dados (DTOs)
    ├── repositories/       # Camada de acesso a dados (operações CRUD diretas no DB)
    └── services/           # Lógica de negócio, orquestração e controle de transações ACID
```

-----

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado:

  * **Python 3.11+**
  * **Docker** e **Docker Compose** (altamente recomendado para setup de DB e API)
  * **pip** (gerenciador de pacotes Python)

-----

## Como Executar o Projeto

Siga os passos abaixo para configurar e iniciar a aplicação.

### 1\. Clonar o Repositório

```bash
git clone https://github.com/andrelvicente/proficiencia-projeto-backend-orm.git
cd proficiencia-projeto-backend-orm # Ou o nome da sua pasta
```

### 2\. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto e preencha com suas credenciais:

```dotenv
# .env
DATABASE_URL="postgresql://user:password@db:5432/iot_db"
SECRET_KEY="sua_chave_secreta_super_segura_aqui_para_jwt"
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Importante:**

  * A `DATABASE_URL` deve usar `db` como host, pois a API estará se comunicando com o serviço `db` dentro da rede Docker Compose.
  * Altere `SECRET_KEY` para uma string aleatória e segura.

### 3\. Construir e Iniciar os Containers

Execute este comando na raiz do seu projeto. Ele construirá a imagem da sua API (usando o `Dockerfile`), iniciará o PostgreSQL e a API.

```bash
docker compose up --build
```

Você verá os logs de ambos os serviços no seu terminal. O container da API (`api-1`) deve iniciar e reportar que o Uvicorn está rodando na porta `8000`.

-----

## Acessando a API

Com os containers rodando, sua API estará disponível:

  * **Documentação Interativa (Swagger UI):** Acesse `http://localhost:8000/docs` no seu navegador. Aqui você pode explorar todos os endpoints e testá-los.

### Fluxo de Teste Básico:

1.  **Registro:**
      * Acesse o endpoint `POST /api/v1/auth/register`.
      * Crie um novo usuário (`username`, `email`, `password`).
2.  **Login e Token:**
      * Acesse o endpoint `POST /api/v1/auth/token`.
      * Use as credenciais do usuário recém-criado.
      * A resposta conterá um `access_token`. **Copie este token.**
3.  **Autorização na Swagger UI:**
      * No canto superior direito da Swagger UI, clique no botão "Authorize" (ou ícone de cadeado).
      * Cole seu `access_token` no campo `Value` no formato: `Bearer SEU_TOKEN_AQUI` (substitua `SEU_TOKEN_AQUI` pelo token copiado).
      * Clique em "Authorize" e depois em "Close".
4.  **Testar Endpoints Protegidos:**
      * Agora você pode testar outros endpoints (ex: `POST /api/v1/projects`, `GET /api/v1/users/me`) que exigem autenticação.

-----

## Contato

Se tiver alguma dúvida ou encontrar problemas durante a execução ou avaliação do projeto, sinta-se à vontade para perguntar.
