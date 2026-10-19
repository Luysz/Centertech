# CenterTech — pacote para Vercel + Neon

## Arquivos
- `app.py`: FastAPI usando `DATABASE_URL` (não contém senha embutida).
- `mapa.html`: mapa com atualização das vagas a cada 5 segundos.
- `historico.html`: página de histórico.
- `requirements.txt`: dependências de produção.

## Configuração na Vercel
1. Envie estes arquivos para um repositório privado no GitHub (não inclua `.env`, backups ou senhas).
2. Importe o repositório na Vercel.
3. Em Project Settings → Environment Variables, adicione `DATABASE_URL` com a connection string do Neon. Use a string pooled do Neon, com `sslmode=require`. Marque Production (e Preview, se for usar).
4. Faça redeploy depois de salvar a variável.
5. Teste `/`, `/health`, `/vagas`, `/mapa`, `/historico` e `/docs`.

## Importante
O banco Neon precisa ter as tabelas `vagas`, `sensores` e `historico_status` com as colunas esperadas pelo `app.py`. O pacote não migra dados nem cria tabelas automaticamente. Importe o banco original antes de considerar o site pronto.

## ESP32
Depois de publicar, altere no sketch do ESP32 a URL para `https://SEU-DOMINIO.vercel.app/sensores`. O ESP32 precisa enviar HTTPS (não HTTP) para a URL pública.

## Segurança
A connection string deve ficar somente na variável de ambiente `DATABASE_URL` da Vercel. Não a coloque no código nem em repositório. Como a senha foi compartilhada anteriormente, redefina-a no Neon e atualize a variável com a nova connection string.
