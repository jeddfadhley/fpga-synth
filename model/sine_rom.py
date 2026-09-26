import math

def sine_table(addr_w, data_w):
    """function to create a list of sine values for given widths"""
    sine_list = []
    amplitude = 2**(data_w -1)-1
    for i in range(2**addr_w):
        sine_list.append(round(amplitude * math.sin(i * ((2* math.pi)/2**addr_w))))
    return sine_list


def write_hex(path, values, data_w):
    """function to write signed integers to path as two's complement hex, one per line for $readmemh"""
    digits = (data_w + 3) // 4
    with open(path, "w") as f:
        for value in values:
            hex_text = f"{(value & (2**data_w-1)):0{digits}x}"
            f.write(hex_text + "\n")


if __name__ == "__main__":
    write_hex("/Users/jedd/IdeaProjects/FPGA_synth/rtl/mem/sine_1024x16.hex", sine_table(10, 16), 16)


