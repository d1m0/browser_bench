#!/bin/bash

date=$(date +"%m-%d_%H-%M")
TEST_COUNT=100

benchmark_all() {
	if [[ "$#" -ne 1 ]]; then
		echo "usage: $FUNCNAME <benchmark>"
		return 1
	fi

	local BMK="$1"
	./benchmark.py run-benchmark \
		--browser "$HOME/chromes/vanilla/chrome" "$HOME/chromes/ivtbl/chrome" "$HOME/chromes/ovtbl/chrome" "$HOME/chromes/llvmcfi/chrome" \
		--labels vanilla ivtbl ovtbl llvmcfi \
		--browser_args=--disable-setuid-sandbox \
		--benchmark $BMK \
		--nruns $TEST_COUNT \
		--out "logs/all_${BMK}_${date}.log"
}

benchmark_bmk_html5() {
	if [[ "$#" -ne 1 ]]; then
		echo "usage: $FUNCNAME <chrome-type>"
		return 1
	fi

	local BMK="$1"
	./benchmark.py run-benchmark \
		--browser "$HOME/chromes/$BMK/chrome" \
		--labels $BMK \
		--browser_args=--disable-setuid-sandbox \
		--benchmark html5 \
		--nruns $TEST_COUNT \
		--out "logs/${BMK}_html5_$date.log"
}

benchmark_all $@
#benchmark_bmk_html5 $@
