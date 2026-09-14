import '@testing-library/jest-dom'

// jsdom omits several DOM APIs that Radix UI primitives rely on at
// interaction time (Select open/close, focus management). Polyfill the
// minimum surface so user-event driven tests behave like a real browser.

if (typeof window !== 'undefined' && !window.PointerEvent) {
  // Only the members Radix/user-event actually read are materialized; the
  // cast keeps us honest without implementing every spec property.
  class PointerEventPolyfill extends MouseEvent {
    pointerId: number
    pointerType: string
    isPrimary: boolean
    pressure: number

    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params)
      this.pointerId = params.pointerId ?? 0
      this.pointerType = params.pointerType ?? ''
      this.isPrimary = params.isPrimary ?? false
      this.pressure = params.pressure ?? 0
    }
  }
  window.PointerEvent = PointerEventPolyfill as unknown as typeof PointerEvent
}

if (typeof Element !== 'undefined' && !Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false
  Element.prototype.setPointerCapture = () => {}
  Element.prototype.releasePointerCapture = () => {}
}

if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}
