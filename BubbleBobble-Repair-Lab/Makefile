PYTHON ?= python3

.PHONY: run test videos before after verify clean

run:
	$(PYTHON) game.py

test:
	$(PYTHON) -m unittest discover -s tests -v

videos: before after

before:
	$(PYTHON) tools/record_demo.py --mode before --out media/before.mp4 --poster media/before_poster.png

after:
	$(PYTHON) tools/record_demo.py --mode after --out media/after.mp4 --poster media/after_poster.png

verify:
	$(PYTHON) tools/verify_submission.py

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache
