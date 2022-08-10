BUILD_DIR = build
PCAP_DIR = pcaps
LOG_DIR = logs


P4C = p4c-bm2-ss
P4C_ARGS += --p4runtime-files $(BUILD_DIR)/$(basename $@).p4.p4info.txt

$(info    P4C_ARGS is $(P4C_ARGS))

RUN_SCRIPT = ../utils/run_solution.py

ifndef TOPO
TOPO = topology.json
endif

ifndef P4_SRC
P4_SRC  = $(DEFAULT_P4_SRC)
endif


source = $(P4_SRC)
compiled_json := $(source:.p4=.json)


ifndef DEFAULT_PROG
DEFAULT_PROG = $(P4_SRC)
endif
DEFAULT_JSON = $(BUILD_DIR)/$(DEFAULT_PROG:.p4=.json)



# Define NO_P4 to start BMv2 without a program
ifndef NO_P4
run_args += -j $(DEFAULT_JSON)
endif

# Set BMV2_SWITCH_EXE to override the BMv2 target
ifdef BMV2_SWITCH_EXE
run_args += -b $(BMV2_SWITCH_EXE)
endif

ifdef TEST_JSON
run_args += -e $(TEST_JSON)
endif



all: run

run: build
	python3 $(CONFIGURE_SCRIPT) -p $(P4_SRC) -t $(TOPO)
	sudo python3 $(RUN_SCRIPT) -t $(TOPO) $(run_args)

stop:
	sudo mn -c

build: dirs $(compiled_json)

%.json: %.p4
	$(P4C) --p4v 16 $(P4C_ARGS) -o $(BUILD_DIR)/$@ $<

dirs:
	mkdir -p $(BUILD_DIR) $(PCAP_DIR) $(LOG_DIR)

clean: stop
	rm -f *.pcap
	rm -rf $(BUILD_DIR) $(PCAP_DIR) $(LOG_DIR)
