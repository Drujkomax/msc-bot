# MSC Visits Bot

Telegram-бот для логирования обхода клиник полевыми сотрудниками.
Все визиты и фото сохраняются в Supabase, отображаются в админ-панели в разделе **Обход** (`/admin/visits`).

## Запуск локально

1. Нужен Node.js 20+ (или [Bun](https://bun.sh)).
2. Скопируйте `.env.example` → `.env` и заполните:
   - `TELEGRAM_BOT_TOKEN` — токен бота от @BotFather (используйте свежий, не из истории чата).
   - `SUPABASE_SERVICE_ROLE_KEY` — service role ключ из Supabase Dashboard → Settings → API.
3. Установите зависимости и запустите:
   ```bash
   npm install
   npm run dev
   ```

Бот работает в режиме long-polling — никаких webhook'ов настраивать не нужно.

## Production

```bash
npm install --production=false
npm run start    # запускает через tsx, без сборки
```

Любая платформа, поддерживающая Node.js (Railway, Fly.io, VPS).
На VPS можно запустить через `pm2` / `systemd`. Бот не требует входящих портов.

## Привязка сотрудника

1. Сотрудник в админке открывает свой профиль и нажимает «Привязать Telegram».
2. Получает 6-значный код (валиден 15 минут).
3. Открывает бота, шлёт `/start <код>` или просто пишет код.
4. Бот привязывает `telegram_id` к профилю и показывает главное меню.
