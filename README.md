# PriceWatch Sentinel

Monitor automatizado de preços para e-commerces brasileiros. Roda em servidor local via systemd, detecta quedas de preço e envia alertas por e-mail com gráfico de histórico.

**Lojas suportadas:** Amazon, Magalu, Mercado Livre, InTheBox

---

## Como funciona

A cada execução o sistema:
1. Busca todos os produtos ativos no banco de dados
2. Faz scraping do preço atual via Playwright (modo headless + stealth)
3. Compara com o último preço registrado e com o preço alvo configurado
4. Envia e-mail de alerta com gráfico de histórico se o preço caiu ou atingiu o alvo
5. Salva o novo preço no histórico
6. Ao final, envia um resumo diário com todos os produtos monitorados

**Lógica de alerta:**
- **Com preço alvo (`config_alerta`):** notifica apenas quando o preço cruza o alvo vindo de cima, evitando spam em dias consecutivos
- **Sem preço alvo:** notifica em qualquer queda em relação ao dia anterior
- Em ambos os casos, o e-mail indica quando o preço atingiu o menor valor já registrado

---

## Pré-requisitos

- Python 3.10+
- Git

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/lucaschefferh/PriceWatch.git
cd PriceWatch

# Crie o ambiente virtual e instale as dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Instale o browser do Playwright
playwright install chromium --with-deps
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

# Jitter anti-ban em segundos (atraso aleatório antes de iniciar)
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

O script pede o nome, URL, loja e um preço alvo opcional (deixe em branco para alertar em qualquer queda).

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
# Ajuste os caminhos no pricewatch.service antes de copiar
cp deploy/pricewatch.service ~/.config/systemd/user/
cp deploy/pricewatch.timer ~/.config/systemd/user/
```

Edite o `pricewatch.service` ajustando os caminhos para o diretório do projeto:

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

O sistema executa todo dia às **8h (horário de Brasília)**. O jitter adiciona um atraso aleatório configurável para evitar bloqueio de IP.

---

## Verificar logs

```bash
# Log do serviço via systemd
journalctl --user -u pricewatch.service -n 50

# Próxima execução agendada
systemctl --user list-timers pricewatch.timer
```

Os logs também ficam salvos em `data/pricewatch.log`.
