import { AxiosError } from 'axios'

/**
 * Extract a human-readable error message from an Axios error response
 * that follows the QAIP { success: false, error: { message, details } } envelope.
 */
export function getApiErrorMessage(err: unknown, fallback = 'Something went wrong.'): string {
  if (err instanceof AxiosError && err.response?.data) {
    const data = err.response.data

    // QAIP error envelope — check field-level details first (most specific)
    if (data?.error?.details && typeof data.error.details === 'object') {
      const details = data.error.details as Record<string, string[]>
      const entries = Object.entries(details)
      if (entries.length > 0) {
        // Return all field errors joined
        const messages = entries.map(([field, errs]) => {
          const fieldLabel = field === 'non_field_errors' ? '' : `${field}: `
          const errList = Array.isArray(errs) ? errs.join(', ') : String(errs)
          return `${fieldLabel}${errList}`
        })
        return messages.join(' | ')
      }
    }

    // Top-level message from envelope
    if (data?.error?.message) return data.error.message

    // Generic DRF detail field
    if (data?.detail) return String(data.detail)
  }
  return fallback
}

/**
 * Extract field-level errors from an API error response.
 * Returns a map of fieldName → errorMessage for setting form errors.
 */
export function getFieldErrors(err: unknown): Record<string, string> {
  if (err instanceof AxiosError && err.response?.data?.error?.details) {
    const details = err.response.data.error.details as Record<string, string[]>
    const result: Record<string, string> = {}
    for (const [field, errors] of Object.entries(details)) {
      if (Array.isArray(errors) && errors.length > 0) {
        result[field] = errors[0]
      }
    }
    return result
  }
  return {}
}
