# Convenience wrappers around sim/*.py. The Python needs cocotb, Verilator
# and yowasp-yosys: put that environment first on PATH, or run e.g.
#   make test M=sine_rom PY=~/radioconda/bin/python3

PY ?= python3
M  ?=
C  ?= default
T  ?= ice40
TOP ?=

.PHONY: help test regress lint synth bit prog flash waves clean

help:
	@echo "make test M=<module> [C=<config>]   run one module's tests"
	@echo "make regress                         lint + test every active module"
	@echo "make lint                            lint only"
	@echo "make synth M=<module> [T=ice40|gowin|xilinx|generic]"
	@echo "make bit TOP=<module>                Basys 3 bitstream (openXC7) -> build/<module>/"
	@echo "make prog TOP=<module>               load it onto the Basys 3 (SRAM)"
	@echo "make flash TOP=<module>              write it to the Basys 3 flash"
	@echo "make waves                           open tb/dump.vcd in surfer"
	@echo "make clean                           remove build and result output"

test:
	@test -n "$(M)" || (echo "usage: make test M=<module>"; exit 2)
	$(PY) sim/run.py $(M) --config $(C)

regress:
	$(PY) sim/regress.py

lint:
	$(PY) sim/regress.py --lint-only

synth:
	@test -n "$(M)" || (echo "usage: make synth M=<module>"; exit 2)
	$(PY) sim/synth.py $(M) --config $(C) --target $(T)

bit:
	@test -n "$(TOP)" || (echo "usage: make bit TOP=<module>"; exit 2)
	$(PY) sim/fpga.py build $(TOP)

prog:
	@test -n "$(TOP)" || (echo "usage: make prog TOP=<module>"; exit 2)
	$(PY) sim/fpga.py prog $(TOP)

flash:
	@test -n "$(TOP)" || (echo "usage: make flash TOP=<module>"; exit 2)
	$(PY) sim/fpga.py prog $(TOP) --flash

waves:
	surfer tb/dump.vcd

clean:
	rm -rf sim_build sim/results build tb/dump.vcd tb/results.xml
