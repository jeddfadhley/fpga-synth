from phase_accumulator import next_phase
from sine_rom import sine_table

FS = 48828.125      # sample rate, Hz: 100 MHz / 2048 clocks per sample


def increment_for(f_hz, phase_w, fs=FS):
    """function to find the increment that gives f_hz: UQ0.phase_w, fraction of a cycle per sample"""
    return round(f_hz * 2**phase_w / fs) & (2**phase_w - 1)


def frequency_of(increment, phase_w, fs=FS):
    """function to find the frequency an increment really gives, Hz (increment_for rounds)"""
    return increment * fs / 2**phase_w


class Nco:
    """Cycle-accurate model of rtl/nco.v. step() is one rising edge: every register's next value is
    worked out from the values before the edge, then all are updated together, like <=.
    Starts in the state after a reset of 2 clocks or more: phase 0, the ROM showing table[0]."""

    def __init__(self, phase_w, addr_w, data_w):
        self.phase_w = phase_w
        self.addr_w = addr_w
        self.table = sine_table(addr_w, data_w)
        self.phase = 0
        self.valid_dly = 0
        self.sample_valid = 0
        self.sample = self.table[0]

    def step(self, rst, en, increment):
        """function to advance one clock; returns (sample, sample_valid) after the edge"""
        # all from the old state
        sample = self.table[self.phase >> (self.phase_w - self.addr_w)]    # ROM reads the old phase; not reset
        phase = next_phase(self.phase, increment, en, rst, self.phase_w)
        sample_valid = 0 if rst else self.valid_dly
        valid_dly = 0 if rst else en

        # then update together
        self.sample = sample
        self.phase = phase
        self.sample_valid = sample_valid
        self.valid_dly = valid_dly
        return self.sample, self.sample_valid
