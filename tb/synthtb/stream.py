"""Monitor for the voice-slot stream described in docs/interfaces.md.

Every datapath stage emits, per clock, a valid bit, a voice index, a
last-of-frame bit and its data. SlotMonitor records the slots a stage emits
and groups them into frames (one frame = one audio sample period, all voices).

    mon = SlotMonitor(dut.clk, valid=dut.out_valid, voice=dut.out_voice,
                      last=dut.out_last, data={"sample": (dut.out_sample, True)})
    mon.start()
    ...
    frames = mon.frames          # list of frames; each a list of slot dicts
    assert [s["voice"] for s in frames[0]] == list(range(NUM_VOICES))
"""

import cocotb
from cocotb.triggers import FallingEdge


class SlotMonitor:
    """Sample on the falling edge (outputs settled, clear of the active edge).

    data maps a name to (signal, signed). Each recorded slot is a dict with
    "cycle", "voice" and one key per data signal.
    """

    def __init__(self, clk, valid, voice, last=None, data=None):
        self.clk = clk
        self.valid = valid
        self.voice = voice
        self.last = last
        self.data = data or {}
        self.slots: list[dict] = []
        self.frames: list[list[dict]] = []
        self._current: list[dict] = []
        self._task = None
        self.cycle = 0

    def start(self):
        self._task = cocotb.start_soon(self._run())
        return self

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run(self):
        while True:
            await FallingEdge(self.clk)
            self.cycle += 1
            if not self.valid.value.is_resolvable or int(self.valid.value) == 0:
                continue
            slot = {"cycle": self.cycle, "voice": int(self.voice.value)}
            for name, (sig, signed) in self.data.items():
                slot[name] = sig.value.to_signed() if signed else int(sig.value)
            self.slots.append(slot)
            self._current.append(slot)
            if self.last is not None and int(self.last.value):
                self.frames.append(self._current)
                self._current = []

    def voice_series(self, voice: int, name: str) -> list[int]:
        """One data field of one voice across all recorded slots, in order."""
        return [s[name] for s in self.slots if s["voice"] == voice]
