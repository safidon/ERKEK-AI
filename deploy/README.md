# ERKEK AI — VPS-ке орнату

Бір серверде бәрі Docker арқылы жұмыс істейді:

```text
Интернет ──► Caddy (80/443, автоматты HTTPS)
               ├── /api/*  ──► backend (FastAPI) ──► db (PostgreSQL)
               └── /*      ──► frontend (Next.js)
             backup ──► күн сайын pg_dump ──► ./backups
```

## 1. Не керек

- VPS: Ubuntu 22.04/24.04, кемінде 2 GB RAM (1 GB-та frontend build баяу/қиын).
- Домен (мысалы `erkek.kz`).
- OpenAI API кілті.

## 2. Домен (DNS)

Домен тіркеушіңіздің панелінде:

| Түрі | Аты   | Мәні             |
|------|-------|------------------|
| A    | `@`   | серверіңіздің IP |
| A    | `www` | серверіңіздің IP |

DNS тарауы бірнеше минуттан бірнеше сағатқа дейін созылуы мүмкін.
Тексеру: `ping erkek.kz` сервер IP-ін көрсетуі керек.

## 3. Серверді дайындау

```bash
ssh root@SERVER_IP

# Docker
curl -fsSL https://get.docker.com | sh

# Firewall: тек SSH, HTTP, HTTPS
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable
```

## 4. Жобаны орнату

```bash
git clone https://github.com/Safidon/ERKEK-Ai.git /opt/erkek-ai
cd /opt/erkek-ai

cp deploy/.env.example deploy/.env
nano deploy/.env
```

`deploy/.env` ішінде толтыру керек:

- `DOMAIN` — доменіңіз (`www`-сыз), `ACME_EMAIL` — email-іңіз
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY` — `openssl rand -hex 32` командасының нәтижесі
- `POSTGRES_PASSWORD` — `openssl rand -hex 24` командасының нәтижесі
- `SMTP_*` — хат жіберу сервисінің деректері (құпиясөзді қалпына келтіру
  хаттары үшін). Мысалы, [Resend](https://resend.com), [Brevo](https://www.brevo.com)
  немесе Mailgun. `SMTP_FROM` доменіңіздегі мекенжай болғаны дұрыс,
  әйтпесе хаттар «Спам»-ға түсуі мүмкін.

Іске қосу:

```bash
docker compose --env-file deploy/.env up -d --build
docker compose --env-file deploy/.env ps
```

Caddy бірінші сұраныста Let's Encrypt сертификатын өзі алады —
`https://ДОМЕН` ашылуы керек.

## 5. Мониторинг

- `https://ДОМЕН/api/health` — backend тірі ме.
- `https://ДОМЕН/api/health/ready` — backend + database жұмыс істей ме (қате болса 503).
- Сыртқы тегін мониторинг: [UptimeRobot](https://uptimerobot.com) немесе
  [Better Stack](https://betterstack.com)-та `/api/health/ready` адресін
  5 минут сайын тексеретін монитор қосыңыз — сайт құласа email/Telegram келеді.
- Docker контейнерлерді құласа автоматты қайта іске қосады (`restart: unless-stopped`),
  backend-та `HEALTHCHECK` бар.

Логтар:

```bash
docker compose --env-file deploy/.env logs -f backend
docker compose --env-file deploy/.env logs -f caddy
```

## 6. Backup

`backup` сервисі күн сайын `/opt/erkek-ai/backups/` ішіне
`erkek_ai_ДАТА.sql.gz` жасайды, `BACKUP_KEEP_DAYS` (әдепкі 14) күннен
ескісін өшіреді.

Маңызды: backup сол серверде ғана тұрса, сервер жоғалғанда ол да жоғалады.
Анда-санда басқа жерге көшіріп алыңыз, мысалы өз компьютеріңізден:

```bash
scp root@SERVER_IP:/opt/erkek-ai/backups/erkek_ai_*.sql.gz ./
```

Қалпына келтіру:

```bash
gunzip -c backups/erkek_ai_ДАТА.sql.gz | \
  docker compose --env-file deploy/.env exec -T db psql -U erkek -d erkek_ai
```

## 7. Автоматты deploy (CI/CD)

`.github/workflows/ci.yml` — әр push-та: backend тесттері (SQLite және PostgreSQL),
frontend lint + build, Docker image-дер build.

`.github/workflows/deploy.yml` — `main`-ге push болып CI сәтті өткенде
серверге SSH арқылы кіріп, `git pull` + `docker compose up -d --build` жасайды.
Қосу үшін:

1. Серверде deploy кілтін жасаңыз:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
   cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
   cat ~/.ssh/github_deploy          # бұл — VPS_SSH_KEY
   ssh-keyscan SERVER_IP             # бұл — VPS_KNOWN_HOSTS
   ```
2. GitHub → репозиторий → **Settings → Secrets and variables → Actions**:
   - Secrets: `VPS_HOST` (IP), `VPS_USER` (`root`), `VPS_SSH_KEY`, `VPS_KNOWN_HOSTS`
   - Variables: `DEPLOY_ENABLED` = `true`
3. Репозиторий жеке (private) болса, серверде `git pull` жұмыс істеуі үшін
   GitHub-та сол серверге арналған Deploy key қосыңыз.

Қолмен іске қосу: GitHub → **Actions → Deploy → Run workflow**.

## 8. Қауіпсіздік туралы

- Rate limiting: бір IP-ден минутына 10 кіру/тіркелу, 20 чат сұранысы
  (`deploy/.env` арқылы өзгертуге болады). Лимит backend жадында,
  сондықтан backend бір worker-мен жұмыс істейді.
- Production-да `/docs` жабық, HSTS және басқа security header-лер қосылған.
- `JWT_SECRET_KEY` 32 таңбадан қысқа немесе CORS-та localhost болса,
  backend production-да іске қосылмайды.
- `deploy/.env` файлын ешқашан git-ке салмаңыз.

## 9. OpenAI шығыны

- `DAILY_MESSAGES_PER_USER` — бір пайдаланушыға күніне хабарлама (әдепкі 50).
- `DAILY_SITE_TOKEN_BUDGET` — бүкіл сайтқа күніне токен (әдепкі 2 000 000,
  шамамен 450 хабарлама). Бітсе, барлығына «ертең келіңіз» деген хабар шығады.
- Соңғы қорғаныс: [OpenAI баптауларында](https://platform.openai.com/settings/organization/limits)
  ай сайынғы шектеу (budget) және ескерту email-ін қойыңыз.
