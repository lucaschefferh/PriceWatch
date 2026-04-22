# PriceWatch Sentinel

Monitor automatizado de preços para e-commerces brasileiros. Roda 24/7 em servidor local, detecta quedas de preço e envia alertas por e-mail.

**Lojas suportadas:** Amazon, Magalu, Mercado Livre, InTheBox

---

## Como funciona

A cada execução o sistema:
1. Busca todos os produtos ativos no banco de dados
2. Faz scraping do preço atual via Playwright (modo headless + stealth)
3. Compara com o último preço registrado
4. Envia e-mail de alerta se o preço caiu
5. Salva o novo preço no histórico

---

## Pré-requisitos

- Python 3.10+
- Git

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/pricewatch.git
cd pricewatch

# Crie o ambiente virtual e instale as dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Instale o browser do Playwright
playwright install chromium
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# E-mail (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASS=sua-app-password
EMAIL_DESTINO=destino@gmail.com

# Banco de dados
DB_PATH=data/prices.db

# Jitter anti-ban em segundos
JITTER_MIN=60
JITTER_MAX=1800
```

> Para Gmail, use uma [App Password](https://myaccount.google.com/apppasswords) no lugar da senha normal.

Crie também a pasta do banco:

```bash
mkdir data
```

---

## Adicionar produtos

```bash
python adicionar_produto.py
```

O script vai pedir o nome, URL e loja do produto interativamente.

---

## Executar manualmente

```bash
python main.py
```

---

## Agendamento com systemd (Linux)

Copie os arquivos de configuração para o systemd do usuário:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/pricewatch.service ~/.config/systemd/user/
cp deploy/pricewatch.timer ~/.config/systemd/user/
```

Edite o `pricewatch.service` e ajuste os caminhos para o diretório do projeto no seu servidor:

```ini
WorkingDirectory=/caminho/para/pricewatch
ExecStart=/caminho/para/pricewatch/.venv/bin/python main.py
```

Ative o timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now pricewatch.timer
loginctl enable-linger $USER
```

Por padrão o sistema executa todo dia às 8h. O jitter configurado no `.env` adiciona um atraso aleatório para evitar bloqueio de IP.

---

## Verificar logs

```bash
# Últimas 50 linhas do log
journalctl --user -u pricewatch.service -n 50

# Próxima execução agendada
systemctl --user status pricewatch.timer
```

Os logs também ficam salvos em `data/pricewatch.log`.
