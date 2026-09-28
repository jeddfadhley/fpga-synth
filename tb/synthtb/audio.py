"""Pitch and spectrum measurement for captured audio samples.

All functions take a sequence of samples (ints or floats) and the sample rate
in Hz. Use at least a few thousand samples: frequency resolution is fs / N
before interpolation.
"""

import math

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal.windows import blackmanharris

A4_HZ = 440.0
A4_NOTE = 69


def note_hz(note: int, a4_hz: float = A4_HZ) -> float:
    """Equal-tempered frequency of a MIDI note number."""
    return a4_hz * 2.0 ** ((note - A4_NOTE) / 12)


def cents(f_measured: float, f_expected: float) -> float:
    """Pitch error in cents (1/100 of a semitone); positive means sharp."""
    return 1200.0 * math.log2(f_measured / f_expected)


def _spectrum(samples, window):
    x = np.asarray(samples, dtype=float)
    x = x - x.mean()
    return np.abs(np.fft.rfft(x * window(len(x))))


def _fit_residual(x: np.ndarray, fs: float, f: float) -> float:
    """Residual of the best least-squares fit a*sin + b*cos + c at frequency f."""
    n = np.arange(len(x))
    basis = np.column_stack([np.sin(2 * np.pi * f * n / fs),
                             np.cos(2 * np.pi * f * n / fs),
                             np.ones(len(x))])
    _, res, *_ = np.linalg.lstsq(basis, x, rcond=None)
    return float(res[0]) if len(res) else 0.0


def measure_frequency(samples, fs: float) -> float:
    """Dominant frequency in Hz.

    Coarse: peak of the Hann-windowed FFT, refined by a parabola through the
    log magnitudes of the peak bin and its neighbours. Fine: the frequency
    whose best-fit sinusoid leaves the least residual, searched within one bin
    of the coarse estimate. The FFT estimate alone is biased when the capture
    holds only a few cycles (low notes); the fit is not.
    """
    x = np.asarray(samples, dtype=float)
    mag = _spectrum(x, np.hanning)
    k = int(np.argmax(mag[1:])) + 1          # skip DC
    bin_hz = fs / len(x)
    coarse = k * bin_hz
    if 0 < k < len(mag) - 1:
        a, b, c = np.log(mag[k - 1:k + 2] + 1e-30)
        coarse = (k + 0.5 * (a - c) / (a - 2 * b + c)) * bin_hz
    fine = minimize_scalar(lambda f: _fit_residual(x, fs, f),
                           bounds=(max(coarse - bin_hz, 1e-9), coarse + bin_hz),
                           method="bounded", options={"xatol": bin_hz * 1e-6})
    return float(fine.x)


def sfdr_db(samples, fs: float, guard_bins: int = 6) -> float:
    """Spurious-free dynamic range: carrier level over the largest other
    spectral line, in dB.

    Uses a 4-term Blackman-Harris window (sidelobes about -92 dB) so window
    leakage does not masquerade as spurs; its main lobe is about 4 bins wide
    each side, so guard_bins either side of the carrier and of DC are excluded.
    Keep the capture to a few thousand samples or more.

    For a phase-truncated NCO this measures about 6.02 dB per ROM address bit
    (checked: 8, 10, 12 bits -> 48.1, 60.1, 72.3 dB).
    """
    mag = _spectrum(samples, blackmanharris)
    k = int(np.argmax(mag[1:])) + 1
    others = mag.copy()
    others[max(0, k - guard_bins):k + guard_bins + 1] = 0
    others[:guard_bins + 1] = 0
    return float(20 * np.log10(mag[k] / max(others.max(), 1e-30)))


def write_wav(samples, path, fs: int = 48_000, data_w: int = 16) -> None:
    """Save signed DATA_W-bit samples as a 16-bit mono WAV, to listen to.

    Wider or narrower samples are shifted to 16 bits. Play with
    `afplay <path>` (macOS) or any audio player.
    """
    import wave

    x = np.asarray(samples, dtype=np.int64)
    x = x << (16 - data_w) if data_w <= 16 else x >> (data_w - 16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(x.astype("<i2").tobytes())


def check_pitch(samples, fs: float, expected_hz: float, tol_cents: float) -> dict:
    """Measure pitch and compare. Returns a record for the assert message:

        r = check_pitch(samples, FS, note_hz(69), tol_cents=1.0)
        assert r["ok"], f"pitch {r}"
    """
    measured = measure_frequency(samples, fs)
    err = cents(measured, expected_hz)
    return {
        "ok": abs(err) <= tol_cents,
        "expected_hz": round(expected_hz, 4),
        "measured_hz": round(measured, 4),
        "error_cents": round(err, 3),
        "tol_cents": tol_cents,
        "n_samples": len(samples),
    }
