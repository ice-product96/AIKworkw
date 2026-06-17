export function renderMarkdown(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  return escaped
    .split('\n\n')
    .map((p) => (p.startsWith('<h') ? p : `<p>${p.replace(/\n/g, '<br>')}</p>`))
    .join('')
}

export function setPageMeta(title: string, description?: string) {
  document.title = title
  let meta = document.querySelector('meta[name="description"]')
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', 'description')
    document.head.appendChild(meta)
  }
  if (description) meta.setAttribute('content', description)
}
