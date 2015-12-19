#!/bin/bash

date=$(date +"%m-%d_%H-%M")
TEST_COUNT=50

# --benchmark sunspider octane kraken html5 \

benchmark_sd_chrome() {
./benchmark.py run-benchmark \
	--browser ~/chromes/vanilla/chrome ~/chromes/ovtbl/chrome ~/chromes/ivtbl/chrome \
	--labels vanilla ovtbl ivtbl \
	--browser_args=--disable-setuid-sandbox \
	--benchmark line-layout html5 balls \
	--nruns $TEST_COUNT \
	--out "sd_all_$date.log"
}

benchmark_llvm_cfi_chrome() {
./benchmark.py run-benchmark \
	--browser ~/chromes/llvm_vanilla/chrome ~/chromes/llvm_cfi/chrome \
	--labels llvm_vanilla llvm_cfi \
	--browser_args=--disable-setuid-sandbox \
	--benchmark sunspider octane kraken \
	--nruns $TEST_COUNT \
	--out "llvm_all_$date.log"
}

benchmark_sd_chrome

#benchmark_llvm_cfi_chrome
