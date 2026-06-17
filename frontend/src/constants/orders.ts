export const SERVICE_OPTIONS = [
  { label: 'Лендинг', value: 'landing_page' },
  { label: 'SEO аудит', value: 'seo_audit' },
  { label: 'Python скрипт', value: 'python_script' },
  { label: 'Telegram бот', value: 'telegram_bot' },
  { label: 'Копирайтинг', value: 'copywriting' },
  { label: 'Баннер', value: 'design_banner' },
  { label: 'Обработка данных', value: 'data_processing' },
  { label: 'Анализ документов', value: 'document_analysis' },
]

export const STATUS_OPTIONS = [
  { label: 'Ожидает оценки', value: 'awaiting_estimate' },
  { label: 'Есть оценки', value: 'estimated' },
  { label: 'Ожидает оплаты', value: 'awaiting_payment' },
  { label: 'В работе', value: 'in_progress' },
  { label: 'Сдано', value: 'submitted' },
  { label: 'Доработка', value: 'revision_requested' },
  { label: 'Завершён', value: 'completed' },
  { label: 'Спор', value: 'disputed' },
]

export const STATUS_LABELS: Record<string, string> = Object.fromEntries(
  STATUS_OPTIONS.map((o) => [o.value, o.label]),
)

export function serviceLabel(value: string): string {
  return SERVICE_OPTIONS.find((o) => o.value === value)?.label ?? value
}

export function statusLabel(value: string): string {
  return STATUS_LABELS[value] ?? value
}
