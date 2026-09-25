def next_phase(phase, increment, en, rst, width):
    """function to find next phase"""
    if rst == 1:
        output_phase = 0
    else:
        if en == 1:
            output_phase = (phase + increment) & (2**width - 1)
        else:
            output_phase = phase
    return output_phase
