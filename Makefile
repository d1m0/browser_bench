CHROMES_DIR = $(HOME)/chromes
#TYPES       = vanilla ovtbl ivtbl llvmcfi
TYPES       = vanilla ovtbl ivtbl
HTML5S      = $(patsubst %,html5-%,$(TYPES))
SSS         = $(patsubst %,ss-%,$(TYPES))

HTML5_URL = http://localhost:5005/PerformanceTests/Parser/html5-full-render.html
SS_URL    = http://localhost:5005/sunspider-1.0.2/sunspider-1.0.2/driver.html

all:

$(HTML5S): html5-%:
	rm -rf $(HOME)/.cache/chromium
	$(CHROMES_DIR)/$*/chrome --disable-setuid-sandbox $(HTML5_URL)

$(SSS): ss-%:
	rm -rf $(HOME)/.cache/chromium
	$(CHROMES_DIR)/$*/chrome --disable-setuid-sandbox $(SS_URL)

# log any defined variable
print-%:
	@echo "$* = $($*)"
