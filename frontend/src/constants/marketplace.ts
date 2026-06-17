/** Категории в стиле Kwork: https://kwork.ru/ */
export interface MarketplaceCategory {
  slug: string
  label: string
  icon: string
  serviceTypes: string[]
}

export const MARKETPLACE_CATEGORIES: MarketplaceCategory[] = [
  {
    slug: 'design',
    label: 'Дизайн',
    icon: '🎨',
    serviceTypes: ['landing_page', 'design_banner'],
  },
  {
    slug: 'development',
    label: 'Разработка и IT',
    icon: '💻',
    serviceTypes: ['python_script', 'telegram_bot', 'data_processing'],
  },
  {
    slug: 'texts',
    label: 'Тексты и переводы',
    icon: '✍️',
    serviceTypes: ['copywriting', 'document_analysis'],
  },
  {
    slug: 'seo',
    label: 'SEO и трафик',
    icon: '📈',
    serviceTypes: ['seo_audit'],
  },
  {
    slug: 'marketing',
    label: 'Соцсети и маркетинг',
    icon: '📣',
    serviceTypes: ['copywriting', 'design_banner', 'landing_page'],
  },
  {
    slug: 'business',
    label: 'Бизнес и жизнь',
    icon: '💼',
    serviceTypes: ['document_analysis', 'data_processing'],
  },
]

export function categoryBySlug(slug: string): MarketplaceCategory | undefined {
  return MARKETPLACE_CATEGORIES.find((c) => c.slug === slug)
}

export function serviceTypesForCategory(slug: string | null | undefined): string[] | null {
  if (!slug) return null
  return categoryBySlug(slug)?.serviceTypes ?? null
}

export function formatBudget(min: number | null, max: number | null): string {
  if (min != null && max != null) return `${min.toLocaleString('ru-RU')} – ${max.toLocaleString('ru-RU')} ₽`
  if (min != null) return `от ${min.toLocaleString('ru-RU')} ₽`
  if (max != null) return `до ${max.toLocaleString('ru-RU')} ₽`
  return 'Бюджет не указан'
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'только что'
  if (mins < 60) return `${mins} мин. назад`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} ч. назад`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} дн. назад`
  return new Date(iso).toLocaleDateString('ru-RU')
}
