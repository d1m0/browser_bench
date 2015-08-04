#!/bin/bash

date=$(date +"%m-%d_%H-%M")
TEST_COUNT=10

benchmark_sd_chrome() {
./benchmark.py run-benchmark \
	--browser ~/chromes/vanilla/chrome ~/chromes/interleaved/chrome ~/chromes/checked/chrome \
	--labels vanilla_2 interleaved_2 checked_1 \
	--browser_args=--disable-setuid-sandbox \
	--benchmark sunspider octane kraken html5 \
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

#benchmark_sd_chrome

benchmark_llvm_cfi_chrome
