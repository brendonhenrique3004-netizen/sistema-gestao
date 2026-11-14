# Sistema de Gestão — JR Sul Cargas

Aplicação web inicial para controle de fretes, operação e financeiro.

## O que já está incluído
- Cadastro e edição de fretes, motoristas, veículos, placas, produtos e rotas.
- Registro de dados operacionais, pesos, tickets, documentos, temperatura e pendências.
- Controle financeiro: frete total, adiantamento solicitado/autorizado/pago, outros pagamentos, comprovante, pagamento final e saldo calculado.
- Histórico de pagamentos por frete.
- Busca, painel resumido e exportação CSV.
- Proteção de acesso por usuário e senha HTTP Basic.

## Executar localmente
1. Instale Python 3.11 ou superior.
2. `pip install -r requirements.txt`
3. Defina `ADMIN_USER=jradmin` e `ADMIN_PASSWORD` com uma senha forte.
4. `uvicorn main:app --reload`
5. Abra `http://127.0.0.1:8000`.

## Publicar no Render
1. Envie o conteúdo desta pasta para o repositório privado GitHub.
2. No Render, crie um Web Service ligado ao repositório.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Configure `ADMIN_USER` e `ADMIN_PASSWORD` como variáveis secretas.
6. Configure `DATABASE_URL` apontando para um PostgreSQL persistente. Não use SQLite em hospedagem efêmera para dados reais.

## Muito importante sobre armazenamento
SQLite local é usado apenas para testes. O disco do serviço gratuito do Render pode ser efêmero e a aplicação pode perder dados após reinício/redeploy. Para uso real, configure PostgreSQL persistente e backups antes de cadastrar dados verdadeiros. Não coloque senhas, PIX/CNPJ, documentos ou dados pessoais no GitHub.

## Escopo e validação
Esta é uma primeira versão funcional, não uma certificação de segurança nem substituto de backup. Teste os cadastros, pagamentos, exportação e recuperação antes do uso operacional. O registro de pagamento deve ser feito somente depois de confirmar que o dinheiro foi efetivamente pago.
