import type { Lang } from "./types";

type Dict = Record<string, string | ((p: Record<string, string | number>) => string)>;

const ru: Dict = {
  // авторизация
  unlinked_prompt: "👋 Здравствуйте!\n\nДля входа введите ваш <b>email</b> от админ-панели:",
  login_password_prompt: "Теперь введите <b>пароль</b>:",
  login_invalid: "❌ Неверный email или пароль. Попробуйте ещё раз — введите email:",
  login_role_denied: "❌ У вашего аккаунта нет доступа к боту. Обратитесь к директору.",
  unlinked_role_denied: "❌ У вашего аккаунта нет доступа к боту. Обратитесь к директору.",
  linked_success: ({ name }) => `✅ Здравствуйте, ${name}!\nГотово к работе.`,

  // главное меню
  main_menu_title: ({ name }) => `👋 ${name}\n\nЧто делаем?`,
  btn_start_visit: "➕ Начать визит",
  btn_my_visits: "📋 Мои визиты",
  btn_lang: "🌐 RU/UZ",
  btn_back: "↩️ Назад",
  btn_cancel: "❌ Отмена",
  btn_done: "✅ Готово",
  btn_skip: "⏭ Пропустить",

  // визит — выбор клиники
  visit_already_active: "У вас уже открыт визит. Завершите или отмените его сначала.",
  pick_clinic_prompt: "🔎 Введите название клиники для поиска (минимум 2 символа):",
  pick_clinic_no_match: "Клиник по запросу не найдено.",
  pick_clinic_too_short: "Введите минимум 2 символа.",
  btn_new_clinic: "➕ Добавить новую клинику",
  new_clinic_name_prompt: "Введите название новой клиники:",
  new_clinic_address_prompt: "Введите адрес (или нажмите «Пропустить»):",
  visit_started: ({ clinic }) => `🏥 Визит начат: <b>${clinic}</b>\n\nИспользуйте меню ниже.`,

  // меню активного визита
  visit_menu_title: ({ clinic }) => `🏥 <b>${clinic}</b>`,
  stage_arrival: "1. Подход",
  stage_specialist: "2. Специалист",
  stage_briefing: "3. Брифинг",
  stage_completion: "4. Завершение",
  btn_finish_visit: "🏁 Завершить визит",
  btn_cancel_visit: "❌ Отменить визит",
  btn_open_main: "↩️ В главное меню",
  finish_blocked: "Чтобы завершить визит, нужно заполнить все 4 этапа.",
  visit_cancelled: "Визит отменён.",
  visit_completed: ({ clinic }) => `✅ Визит «${clinic}» завершён. Спасибо!`,
  visit_cancel_confirm: "Точно отменить визит? Все данные будут удалены.",
  btn_yes_cancel: "Да, отменить",

  // этапы — общее
  stage_already_done: "Этот этап уже заполнен. Открыть его и обновить?",
  btn_edit_stage: "✏️ Изменить",
  stage_send_text_or_photo: "Пришлите текст и/или фото. Когда закончите — нажмите «Готово».",
  stage_saved: "✅ Сохранено.",
  more_to_add: "Добавить ещё или закончить?",
  photo_received: ({ count }) => `📷 Фото добавлено (${count}).`,
  photo_limit_reached: "Достигнут лимит 10 фото для этапа.",

  // этап specialist
  specialist_name_prompt: "Введите ФИО специалиста:",
  specialist_position_prompt: "Введите должность специалиста (или пропустите):",
  specialist_phone_prompt: "Телефон специалиста (или пропустите):",
  specialist_extras_prompt: "Можете добавить заметку и/или фото. Нажмите «Готово» когда закончите.",

  // этап briefing
  briefing_prompt: "Опишите содержание встречи (текст), можно добавить фото. Нажмите «Готово».",

  // этап completion
  completion_outcome_prompt: "Какой итог визита?",
  outcome_success: "✅ Успех (договорились)",
  outcome_interested: "🤔 Интерес (думают)",
  outcome_rejected: "❌ Отказ",
  outcome_postponed: "📅 Перенос",
  completion_comment_prompt: "Кратко опишите итог (или пропустите):",

  // история
  my_visits_empty: "У вас пока нет визитов.",
  my_visits_title: "📋 Последние визиты:",

  // язык
  lang_changed: "🌐 Язык переключён на русский.",

  // ошибки/неизвестное
  unknown_input: "Не понял. Используйте кнопки ниже.",
};

const uz: Dict = {
  unlinked_prompt: "👋 Salom!\n\nKirish uchun admin paneldagi <b>emailingizni</b> kiriting:",
  login_password_prompt: "Endi <b>parolni</b> kiriting:",
  login_invalid: "❌ Email yoki parol noto'g'ri. Yana urinib ko'ring — emailni kiriting:",
  login_role_denied: "❌ Akkauntingizda botga ruxsat yo'q. Direktorga murojaat qiling.",
  unlinked_role_denied: "❌ Akkauntingizda botga ruxsat yo'q. Direktorga murojaat qiling.",
  linked_success: ({ name }) => `✅ Salom, ${name}!\nIshga tayyor.`,

  main_menu_title: ({ name }) => `👋 ${name}\n\nNima qilamiz?`,
  btn_start_visit: "➕ Tashrifni boshlash",
  btn_my_visits: "📋 Mening tashriflarim",
  btn_lang: "🌐 RU/UZ",
  btn_back: "↩️ Orqaga",
  btn_cancel: "❌ Bekor qilish",
  btn_done: "✅ Tayyor",
  btn_skip: "⏭ O'tkazib yuborish",

  visit_already_active: "Sizda allaqachon ochiq tashrif bor. Avval uni tugating yoki bekor qiling.",
  pick_clinic_prompt: "🔎 Klinika nomini kiriting (kamida 2 belgi):",
  pick_clinic_no_match: "So'rov bo'yicha klinika topilmadi.",
  pick_clinic_too_short: "Kamida 2 belgi kiriting.",
  btn_new_clinic: "➕ Yangi klinika qo'shish",
  new_clinic_name_prompt: "Yangi klinika nomini kiriting:",
  new_clinic_address_prompt: "Manzilini kiriting (yoki «O'tkazib yuborish» tugmasini bosing):",
  visit_started: ({ clinic }) => `🏥 Tashrif boshlandi: <b>${clinic}</b>\n\nQuyidagi menyudan foydalaning.`,

  visit_menu_title: ({ clinic }) => `🏥 <b>${clinic}</b>`,
  stage_arrival: "1. Kelish",
  stage_specialist: "2. Mutaxassis",
  stage_briefing: "3. Brifing",
  stage_completion: "4. Yakunlash",
  btn_finish_visit: "🏁 Tashrifni tugatish",
  btn_cancel_visit: "❌ Tashrifni bekor qilish",
  btn_open_main: "↩️ Bosh menyuga",
  finish_blocked: "Tashrifni tugatish uchun barcha 4 bosqichni to'ldirish kerak.",
  visit_cancelled: "Tashrif bekor qilindi.",
  visit_completed: ({ clinic }) => `✅ «${clinic}» tashrifi tugatildi. Rahmat!`,
  visit_cancel_confirm: "Tashrifni bekor qilishni tasdiqlaysizmi? Barcha ma'lumotlar o'chiriladi.",
  btn_yes_cancel: "Ha, bekor qilish",

  stage_already_done: "Bu bosqich allaqachon to'ldirilgan. Ochib yangilash kerakmi?",
  btn_edit_stage: "✏️ O'zgartirish",
  stage_send_text_or_photo: "Matn va/yoki rasm yuboring. Tugatgach «Tayyor» tugmasini bosing.",
  stage_saved: "✅ Saqlandi.",
  more_to_add: "Yana qo'shasizmi yoki tugatasizmi?",
  photo_received: ({ count }) => `📷 Rasm qo'shildi (${count}).`,
  photo_limit_reached: "Bosqich uchun 10 ta rasmga limit yetdi.",

  specialist_name_prompt: "Mutaxassis FISHini kiriting:",
  specialist_position_prompt: "Mutaxassis lavozimini kiriting (yoki o'tkazib yuboring):",
  specialist_phone_prompt: "Mutaxassis telefoni (yoki o'tkazib yuboring):",
  specialist_extras_prompt: "Izoh va/yoki rasm qo'shishingiz mumkin. Tugatgach «Tayyor» tugmasini bosing.",

  briefing_prompt: "Uchrashuv mazmunini matnda yozing, rasm qo'shishingiz mumkin. «Tayyor» tugmasini bosing.",

  completion_outcome_prompt: "Tashrif natijasi qanday?",
  outcome_success: "✅ Muvaffaqiyat (kelishildi)",
  outcome_interested: "🤔 Qiziqish (o'ylashmoqda)",
  outcome_rejected: "❌ Rad etish",
  outcome_postponed: "📅 Keyinga qoldirildi",
  completion_comment_prompt: "Natijani qisqa yozing (yoki o'tkazib yuboring):",

  my_visits_empty: "Sizda hali tashriflar yo'q.",
  my_visits_title: "📋 Oxirgi tashriflar:",

  lang_changed: "🌐 Til o'zbekchaga o'zgartirildi.",

  unknown_input: "Tushunmadim. Quyidagi tugmalardan foydalaning.",
};

const dicts: Record<Lang, Dict> = { ru, uz };

export function t(
  lang: Lang,
  key: keyof typeof ru,
  params?: Record<string, string | number>
): string {
  const dict = dicts[lang] ?? ru;
  const entry = dict[key] ?? ru[key];
  if (typeof entry === "function") return entry(params ?? {});
  return entry as string;
}

export function normLang(value: string | null | undefined): Lang {
  return value === "uz" ? "uz" : "ru";
}
