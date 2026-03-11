# ============================================================================
# RPM Bootstrap - Repo Package Manager for Make
# ============================================================================
# This Makefile provides:
#   1. Auto-inclusion of RPM package Makefiles from .packages/
#   2. rpmConfigure target: installs tooling and syncs packages
#   3. rpmClean target: removes synced packages and repo metadata
#
# Prerequisites: Python 3 and pipx must be available on PATH.
# Install the rpm CLI: pipx install "git+<RPM_CLI_URL>@<RPM_CLI_REV>"
#
# Commit this file and .rpmenv to your project. They rarely change.
# Configuration lives in .rpmenv (Make ?= syntax for env var overrides).
# ============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# 1. Read .rpmenv configuration
# ---------------------------------------------------------------------------
RPMENV ?= .rpmenv
PACKAGES_DIR ?= .packages

ifeq (,$(wildcard $(RPMENV)))
$(error RPM: $(RPMENV) not found. Create it from the caylent-private-rpm example.)
endif
include $(RPMENV)

# ---------------------------------------------------------------------------
# 2. Auto-include package Makefiles from .packages/
# ---------------------------------------------------------------------------
# Only include build packages — marketplace packages (rpm-claude-marketplaces-*)
# have their own Makefiles for CI but those are not consumer targets.
RPM_BUILD_MAKEFILES := $(filter-out $(wildcard $(PACKAGES_DIR)/rpm-claude-marketplaces-*/Makefile), \
                          $(wildcard $(PACKAGES_DIR)/*/Makefile))
-include $(RPM_BUILD_MAKEFILES)

# ---------------------------------------------------------------------------
# 3. rpmConfigure target
# ---------------------------------------------------------------------------
.PHONY: rpmConfigure
rpmConfigure: ## Sync RPM packages from manifest sources
	@rpm configure $(RPMENV)

# ---------------------------------------------------------------------------
# 4. rpmClean target
# ---------------------------------------------------------------------------
.PHONY: rpmClean
rpmClean: ## Remove RPM packages and state
	@rpm clean $(RPMENV)

# ---------------------------------------------------------------------------
# 5. help target
# ---------------------------------------------------------------------------
.PHONY: help
help: ## Show available targets
	@echo "RPM Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@if [ -n "$(RPM_BUILD_MAKEFILES)" ]; then \
		echo "Package Targets:"; \
		echo ""; \
		for makefile in $(RPM_BUILD_MAKEFILES); do \
			if [ -f "$$makefile" ]; then \
				grep -E '^[a-zA-Z_-]+:.*?## .*$$' "$$makefile" | \
					awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'; \
			fi; \
		done; \
	else \
		echo "No packages synced. Run 'make rpmConfigure' first."; \
	fi
