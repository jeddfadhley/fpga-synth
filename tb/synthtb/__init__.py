"""Shared testbench helpers (harness plumbing, not models).

  synthtb.audio   pitch / spectrum measurement for audio-rate outputs
  synthtb.midi    MIDI message encoding and a UART bit-level driver
  synthtb.stream  monitor for the voice-slot stream (docs/interfaces.md)

Expected values still come from the models in model/; these helpers only
measure what the DUT produced or drive stimulus into it.
"""
