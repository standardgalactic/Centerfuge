# ============================================================
# Flyxion Makefile
# ============================================================
APP_NAME = flyxiond
GO_DIR   = go/server
STATIC   = static
ELM_DIR  = elm
PORT     = 8080

.PHONY: all build run clean docker docker-run

all: build

build: $(STATIC)/main.js
	cd $(GO_DIR) && go build -o ../../$(APP_NAME)
	@echo "[Flyxion] ✅ Build complete."

$(STATIC)/main.js:
	cd $(ELM_DIR) && elm make src/Main.elm --optimize --output=../static/main.js

run: build
	./$(APP_NAME)

clean:
	rm -f $(APP_NAME) $(STATIC)/main.js

docker:
	docker build -t flyxion:latest .

docker-run:
	docker run -p $(PORT):8080 flyxion:latest
