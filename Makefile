# Окружения и проверки инструментов.
#
#   make bootstrap — .venv корня и каждого пакета
#   make lint      — prek, затем Pyrefly

UV := uv

.PHONY: help bootstrap lint lint-style lint-types

help:
	$(info make bootstrap   — создать .venv в корне и в каждом пакете)
	$(info make lint        — стиль (prek) и типы (Pyrefly))
	$(info make lint-style  — prek run --all-files)
	$(info make lint-types  — Pyrefly по каталогам инструментов)
	@:

# Корень ставится со всеми extras (plots, lsp). У пакетов группа dev
# входит в sync по умолчанию; сборщику дополнительно нужен extra plots.
bootstrap:
	$(UV) sync --frozen --all-extras
	$(UV) sync --frozen --directory packages/md-gost
	$(UV) sync --frozen --directory packages/md-gost-lint
	$(UV) sync --frozen --directory packages/md-gost-build --extra plots
	$(UV) sync --frozen --directory packages/idef0

lint: lint-style lint-types

lint-style:
	prek run --all-files

lint-types:
	cd packages/idef0 && uvx pyrefly check
	cd packages/md-gost && uvx pyrefly check
	cd packages/md-gost-lint && uvx pyrefly check
	cd packages/md-gost-build && uvx pyrefly check
