#!/bin/bash

date=$(date +"%m-%d_%H:%M")

./benchmark.py run-benchmark \
	--browser ~/chromes/vanilla/chrome ~/chromes/interleaved/chrome ~/chromes/checked/chrome \
	--labels vanilla_2 interleaved_2 checked_1 \
	--browser_args=--disable-setuid-sandbox \
	--benchmark sunspider octane kraken html5 \
	--nruns 100 \
	--out "all_$date.log"
