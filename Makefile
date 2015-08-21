CHROMES_DIR = $(HOME)/chromes
HTML5_URL   = http://localhost:5005/PerformanceTests/Parser/html5-full-render.html
TYPES       = vanilla ovtbl ivtbl llvmcfi
HTML5S      = $(patsubst %,html5-%,$(TYPES))

all:

$(HTML5S): html5-%:
	rm -rf $(HOME)/.cache/chromium
	$(CHROMES_DIR)/$*/chrome --disable-setuid-sandbox $(HTML5_URL)

# log any defined variable
print-%:
	@echo "$* = $($*)"
