# Convenience wrappers around sim/*.py. The Python needs cocotb, Verilator
# and yowasp-yosys: put that environment first on PATH, or run e.g.
#   make test M=sine_rom PY=~/radioconda/bin/python3

PY ?= python3
M  ?=
C  ?= default
T  ?= ice40

.PHONY: help test regress lint synth waves clean

help:
	@echo "make test M=<module> [C=<config>]   run one module's tests"
	@echo "make regress                         lint + test every active module"
	@echo "make lint                            lint only"
	@echo "make synth M=<module> [T=ice40|gowin|xilinx|generic]"
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

waves:
	surfer tb/dump.vcd

clean:
	rm -rf sim_build sim/results tb/dump.vcd tb/results.xml
