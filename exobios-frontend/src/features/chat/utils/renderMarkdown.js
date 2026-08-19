import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ breaks: true, gfm: true })

/**
 * Converts assistant markdown (headings, lists, bold, tables) to sanitized
 * HTML. Answers are LLM output over retrieved documents, which the backend's
 * own prompt-injection tests treat as untrusted — sanitize before v-html.
 */
export function renderAssistantMarkdown(text) {
  const html = marked.parse(text ?? '')
  return DOMPurify.sanitize(html, { ALLOWED_ATTR: ['href', 'target', 'rel'] })
}
