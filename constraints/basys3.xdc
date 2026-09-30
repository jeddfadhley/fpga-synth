## Basys 3 (xc7a35tcpg236-1) pin constraints.
## Pins from Digilent's Basys-3-Master.xdc; see docs/hardware.md.
## Port names must match the top-level module. Lines for ports the current top
## doesn't have are skipped by sim/fpga.py, so one file serves every build.

## 100 MHz clock
set_property -dict { PACKAGE_PIN W5  IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports clk]

## LEDs
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS33 } [get_ports {led[0]}]

## USB-UART (from the Mac MIDI bridge)
set_property -dict { PACKAGE_PIN B18 IOSTANDARD LVCMOS33 } [get_ports uart_rx]

## I2S to the MAX98357A on Pmod JA (JA1-3); amp GND/Vin on JA pins 5/6
set_property -dict { PACKAGE_PIN J1  IOSTANDARD LVCMOS33 } [get_ports i2s_bclk]
set_property -dict { PACKAGE_PIN L2  IOSTANDARD LVCMOS33 } [get_ports i2s_lrclk]
set_property -dict { PACKAGE_PIN J2  IOSTANDARD LVCMOS33 } [get_ports i2s_data]

## Configuration
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
