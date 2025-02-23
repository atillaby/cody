.PHONY: clean setup run logs

clean:
	@echo "Cleaning up..."
	-pkill -f uvicorn || true
	@sleep 2
	rm -rf venv/
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

setup:
	@echo "Setting up virtual environment..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

run:
	@echo "Starting API server..."
	. venv/bin/activate && PYTHONPATH=/workspaces/cody python run.py

logs:
	@echo "Showing logs..."
	tail -f api.log
