/**
 * Secure logger utility for development-only logging
 * Prevents sensitive data exposure in production
 */

const isDevelopment = process.env.NODE_ENV === 'development'

interface Logger {
  log: (...args: any[]) => void
  info: (...args: any[]) => void
  warn: (...args: any[]) => void
  error: (...args: any[]) => void
  debug: (...args: any[]) => void
}

/**
 * Development-only logger that prevents console logging in production
 * Use this instead of console.log to avoid exposing sensitive data
 */
export const logger: Logger = {
  log: (...args: any[]) => {
    if (isDevelopment) {
      console.log(...args)
    }
  },
  
  info: (...args: any[]) => {
    if (isDevelopment) {
      console.info(...args)
    }
  },
  
  warn: (...args: any[]) => {
    // Warnings are allowed in production for debugging
    console.warn(...args)
  },
  
  error: (...args: any[]) => {
    // Errors are allowed in production for debugging
    console.error(...args)
  },
  
  debug: (...args: any[]) => {
    if (isDevelopment) {
      console.debug(...args)
    }
  }
}

/**
 * Sanitize sensitive data from objects before logging
 * Masks tokens, passwords, and API keys
 */
export function sanitizeForLogging(obj: any): any {
  if (!obj || typeof obj !== 'object') {
    return obj
  }
  
  const sensitiveKeys = [
    'token', 'password', 'secret', 'key', 'api_key', 'apiKey',
    'auth', 'authorization', 'credential', 'private'
  ]
  
  const sanitized = Array.isArray(obj) ? [...obj] : { ...obj }
  
  for (const key in sanitized) {
    const lowerKey = key.toLowerCase()
    
    if (sensitiveKeys.some(sensitive => lowerKey.includes(sensitive))) {
      sanitized[key] = '[REDACTED]'
    } else if (typeof sanitized[key] === 'object') {
      sanitized[key] = sanitizeForLogging(sanitized[key])
    }
  }
  
  return sanitized
}

/**
 * Log only in development with automatic sanitization
 */
export function devLog(message: string, data?: any) {
  if (isDevelopment) {
    const sanitized = data ? sanitizeForLogging(data) : undefined
    console.log(message, sanitized || '')
  }
}

export default logger