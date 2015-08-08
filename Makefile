CHROMES_DIR = $(HOME)/chromes
HTML5_URL   = http://localhost:5005/PerformanceTests/Parser/html5-full-render.html

all:

html5-%:
	rm -rf $(HOME)/.cache/chromium
	$(CHROMES_DIR)/$*/chrome --disable-setuid-sandbox $(HTML5_URL)

# log any defined variable
print-%:
	@echo "$* = $($*)"
