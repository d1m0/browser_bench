NRUNS       = 50
BENCHMARKS  = sunspider kraken octane html5 line-layout balls
TYPES       = vanilla ivtbl ivtbl_no_check ovtbl ovtbl_no_check llvmcfi
CHROMES_DIR = $(HOME)/chromes

LOG_DIR  = logs
DATE     = $(shell date +"%m-%d_%H-%M")
ALL_LOGS = $(LOG_DIR)/all_logs.txt
LOG_FILE = $(LOG_DIR)/$(DATE).log
BROWSERS = $(patsubst %,$(CHROMES_DIR)/%/chrome,$(TYPES))
SHELL    = /bin/bash

all:

run: log-folder
	rm -rf $(HOME)/.cache/chromium
	. bin/activate ; \
	./benchmark.py run-benchmark \
		--browser $(BROWSERS) \
		--labels $(TYPES) \
		--browser_args=--disable-setuid-sandbox \
		--benchmark $(BENCHMARKS) \
		--nruns $(NRUNS) \
		--out $(LOG_FILE)
	@echo "# $(DATE)"                 >> $(ALL_LOGS)
	@echo "BENCHMARKS: $(BENCHMARKS)" >> $(ALL_LOGS)
	@echo "TYPES:      $(TYPES)"      >> $(ALL_LOGS)
	@echo "NRUNS:      $(NRUNS)"      >> $(ALL_LOGS)

upload: check-upload-env
	. bin/activate; \
	./build_worksheet.py \
		--key "sd benchmarks-f2d25d8cd7e4.json" \
		--title $(title) \
		--sheet $(sheet) \
		$(log)

upload-last:
	. bin/activate; \
	./build_worksheet.py \
		--key "sd benchmarks-f2d25d8cd7e4.json" \
		--title "test" \
		--sheet "test" \
		$(shell ls -1t $(LOG_DIR)/*.log | head -1)

check-upload-env: $(patsubst %,check-env-%,title sheet log)

check-env-%:
	@ if [[ "${${*}}" == "" ]]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

log-folder:
	mkdir -p $(LOG_DIR)

# log any defined variable
print-%:
	@echo "$* = $($*)"
