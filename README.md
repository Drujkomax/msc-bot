# MSC Visits Bot

Telegram-бот для логирования обхода клиник полевыми сотрудниками.
Все визиты, фото, специалисты и лиды пишутся в общую с админкой Supabase:

- `profiles` / `user_roles` — авторизация по email/паролю, привязка `telegram_id`
- `bot_sessions` — состояние диалога
- `visits` / `visit_stages` — визиты и 4 этапа (arrival → specialist → briefing → completion)
- bucket `visits` — фото с этапов
- `clients` — клиники из поиска
- `leads` — карточки лидов, создаются автоматически при заполнении этапа «Специалист»

Стек: Python 3.12, **aiogram 3**, **supabase-py 2**, **httpx**, **python-dotenv**.

---

## Локальный запуск

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить токены
python -m bot.main
```

Long-polling, webhook не нужен.

---

## Деплой на Railway

1. Открой [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
2. Выбери этот репозиторий. Railway сам подхватит `railway.json` (NIXPACKS, start = `python -m bot.main`) и `runtime.txt` (Python 3.12).
3. В разделе **Variables** добавь:
   - `TELEGRAM_BOT_TOKEN` — токен от @BotFather
   - `SUPABASE_URL` — `https://<project>.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` — Supabase Dashboard → Settings → API → `service_role`
   - `SUPABASE_ANON_KEY` — там же, `anon` ключ
4. Деплой стартанёт автоматически. В логах должно появиться `Bot @<name> is up.`
5. Бот long-polling — публичный URL/домен на Railway **не нужен**, никакой webhook настраивать тоже не нужно.

### Если используешь Railway CLI

```bash
railway login
railway link        # привязать локальный репо к проекту
railway up          # пушнуть и задеплоить
railway logs        # смотреть логи
```

### Альтернатива: свой VPS через systemd

```ini
# /etc/systemd/system/msc-bot.service
[Unit]
Description=MSC Visits Bot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/msc-bot
EnvironmentFile=/opt/msc-bot/.env
ExecStart=/opt/msc-bot/.venv/bin/python -m bot.main
Restart=on-failure
RestartSec=5s
User=msc-bot

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now msc-bot
sudo journalctl -u msc-bot -f
```

---

## Привязка сотрудника

1. В админке сотрудник нажимает «Привязать Telegram» → получает email/пароль.
2. В Telegram открывает бота → `/start` → бот спрашивает email и пароль.
3. После проверки `auth.users` и роли (`salesperson` / `sales_manager` / `director` / `admin`) бот привязывает `telegram_id` к профилю.

---

## Поток визита

1. **Начать визит** → поиск клиники в `clients` (по подстроке) или создание `pending_clinic`.
2. **Подход** — текст / фото, опционально.
3. **Специалист** — ФИО → должность → телефон → email → оборудование → бюджет → сроки → качество (A/B/C) → заметка/фото. По завершении автоматически создаётся запись в `public.leads` (`source=manual`, `stage=new`, `assigned_to` = сотрудник, `company`/`city` = из клиники), идемпотентно через маркер `[visit:<uuid>]` в `notes`.
4. **Брифинг** — категория (🩺 Диагностика / 🧪 Лаборатория / 🦷 Стоматология), затем текст + фото.
5. **Завершение** — итог (success / interested / rejected / postponed) + опциональный комментарий.

Когда все 4 этапа закрыты — кнопка «Завершить визит» проставляет `status='completed'` и `completed_at`.

---

## Структура

```
bot/
  main.py            # Dispatcher (aiogram), routing, polling
  config.py          # env через python-dotenv
  db.py              # service-role + anon supabase клиенты
  types.py           # dataclasses
  i18n.py            # переводы RU/UZ
  keyboards.py       # InlineKeyboardMarkup билдеры
  auth.py            # login / link / can_start_visit
  session.py         # bot_sessions
  visits.py          # visits + visit_stages + clients
  leads.py           # public.leads upsert
  storage.py         # httpx → Telegram getFile → Supabase Storage
  handlers/
    start.py main_menu.py history.py language.py
    visit_start.py visit_actions.py stages.py
railway.json         # Railway build/start config
Procfile             # дублирует startCommand (worker)
runtime.txt          # Python 3.12 для Railway/Heroku-like nixpacks
.python-version      # подсказка для локального pyenv
requirements.txt
.env.example
```
