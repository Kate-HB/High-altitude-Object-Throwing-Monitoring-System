/** Alarm sound utility — uses HTML5 Audio + WAV blob, no autoplay issues. */

let _audio = null

/** Generate a short 3-beep WAV as blob URL. Called once, cached. */
function _getAudio() {
  if (_audio) return _audio

  const sampleRate = 8000
  const beepDuration = 0.12   // seconds per beep
  const gapDuration = 0.08    // seconds between beeps
  const beeps = 3
  const freq = 880            // Hz

  const beepSamples = Math.floor(sampleRate * beepDuration)
  const gapSamples = Math.floor(sampleRate * gapDuration)

  // Build sample buffer (unsigned 8-bit PCM: 128 = silence)
  const totalSamples = beeps * beepSamples + (beeps - 1) * gapSamples
  const buffer = new Uint8Array(totalSamples)
  buffer.fill(128)

  for (let b = 0; b < beeps; b++) {
    const offset = b * (beepSamples + gapSamples)
    for (let i = 0; i < beepSamples; i++) {
      const t = i / sampleRate
      // Square wave with fade envelope
      const envelope = 1.0 - i / beepSamples
      const sample = Math.sin(2 * Math.PI * freq * t) >= 0 ? 64 : -64
      buffer[offset + i] = 128 + Math.floor(sample * envelope)
    }
    // Gap is silent (already zero)
  }

  // Build WAV file
  const dataSize = totalSamples
  const header = new ArrayBuffer(44)
  const view = new DataView(header)
  writeStr(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(view, 8, 'WAVE')
  writeStr(view, 12, 'fmt ')
  view.setUint32(16, 16, true)           // chunk size
  view.setUint16(20, 1, true)            // PCM
  view.setUint16(22, 1, true)            // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate, true)   // byte rate (mono 8-bit)
  view.setUint16(32, 1, true)            // block align
  view.setUint16(34, 8, true)            // bits per sample
  writeStr(view, 36, 'data')
  view.setUint32(40, dataSize, true)

  const blob = new Blob([header, buffer], { type: 'audio/wav' })
  _audio = new Audio(URL.createObjectURL(blob))
  return _audio
}

function writeStr(view, offset, str) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

/**
 * Play a 3-beep alarm sound.
 */
export function playAlarm() {
  try {
    const audio = _getAudio()
    audio.currentTime = 0
    audio.play().catch(() => {
      // Browser blocked — retry once after next user click
    })
  } catch {
    // Silently ignore
  }
}

/** Must be called from user gesture to unlock HTML5 Audio playback. */
export function unlockAudio() {
  const audio = _getAudio()
  audio.volume = 0
  audio.play().then(() => {
    audio.pause()
    audio.currentTime = 0
    audio.volume = 1
  }).catch(() => {
    // Browser blocked — alarm will work after next user click
  })
}
