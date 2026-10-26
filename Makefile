# Local RPM builds for the packages in this repo.
#
#   make             build the SRPM of every package
#   make srpm        same as above
#   make rpm         also build the binary RPMs (needs the build deps)
#   make <pkg>-srpm  build a single package
#   make <pkg>-rpm   build the binary RPMs of a single package
#   make lint        run rpmlint on every spec
#   make test        build the RPMs and check them in a Fedora container
#   make clean       remove the build directory
#
# Everything is built inside $(BUILDDIR) (default: ./build, git-ignored).
# rpmbuild's default topdir (~/rpmbuild) is never used.

SHELL := /bin/bash

# The per-package rules are generated below, so pin the default goal.
.DEFAULT_GOAL := all

BUILDDIR ?= build
# An absolute BUILDDIR is used as-is; a relative one lives inside the repo.
ifeq ($(filter /%,$(BUILDDIR)),)
TOPDIR := $(CURDIR)/$(BUILDDIR)
else
TOPDIR := $(BUILDDIR)
endif
RPMBUILD ?= rpmbuild
RPLINT   ?= rpmlint

# The tools come from mise (see mise.toml), fall back to a system install.
MISE := $(shell command -v mise 2>/dev/null)
tool = $(if $(MISE),$(MISE) exec -- $(1),$(shell command -v $(1) 2>/dev/null))

RUFF        ?= $(call tool,ruff)
SHELLCHECK  ?= $(call tool,shellcheck)
YAMLLINT    ?= $(call tool,yamllint)
SHELL_FILES := .github/scripts/smoke-test.sh
YAML_FILES  := .github/workflows/*.yml .pre-commit-config.yaml .yamllint.yaml

# The container the test target runs in. It needs podman or docker.
TEST_IMAGE ?= fedora:44
CONTAINER  ?= $(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)

SPECS := $(wildcard */*.spec)
PKGS   := $(sort $(notdir $(patsubst %/,%,$(dir $(SPECS)))))

$(foreach p,$(PKGS),$(eval SPEC_$(p) := $(wildcard $(p)/*.spec)))

# One pair of rules per package: stage the vendored files into SOURCES/,
# then build with a per-package topdir so packages never mix sources.
define PACKAGE_RULES
$(1)-srpm:
	@echo "==> $(1): SRPM -> $(TOPDIR)/$(1)"
	@rm -rf $(TOPDIR)/$(1)/BUILD
	@rm -f $(TOPDIR)/$(1)/RPMS/x86_64/*.rpm $(TOPDIR)/$(1)/SRPMS/*.src.rpm
	@mkdir -p $(TOPDIR)/$(1)/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	@# Drop the sources of a previous version: the checksum file has no
	@# version in its name, so it has to be fetched again.
	@version=$$(grep -m1 '^Version:' $(1)/*.spec | awk '{print $$2}'); \
	 find $(TOPDIR)/$(1)/SOURCES -maxdepth 1 -type f ! -name "*$$version*" -delete
	@find $(1) -type f ! -name '*.spec' -exec cp -t $(TOPDIR)/$(1)/SOURCES/ {} +
	@cp $(1)/*.spec $(TOPDIR)/$(1)/SPECS/
	@$(RPMBUILD) -bs \
		--define "_topdir $(TOPDIR)/$(1)" \
		--define "_disable_source_fetch 0" \
		$(TOPDIR)/$(1)/SPECS/$(notdir $(SPEC_$(1)))

$(1)-rpm: $(1)-srpm
	@echo "==> $(1): binary RPM -> $(TOPDIR)/$(1)/RPMS"
	@$(RPMBUILD) -ba \
		--define "_topdir $(TOPDIR)/$(1)" \
		--define "_disable_source_fetch 0" \
		$(TOPDIR)/$(1)/SPECS/$(notdir $(SPEC_$(1)))

$(1)-clean:
	@rm -rf $(TOPDIR)/$(1)
endef

$(foreach p,$(PKGS),$(eval $(call PACKAGE_RULES,$(p))))

.PHONY: all srpm rpm lint test clean help \
        $(foreach p,$(PKGS),$(p)-srpm $(p)-rpm $(p)-clean)

all: srpm

srpm: $(foreach p,$(PKGS),$(p)-srpm)

rpm: $(foreach p,$(PKGS),$(p)-rpm)

lint:
	@for s in $(SPECS); do \
		echo "==> rpmlint $$s"; \
		$(RPLINT) $$s || true; \
	done
	@if [ -n "$(RUFF)" ]; then \
		echo "==> ruff"; \
		$(RUFF) check .; \
	else \
		echo "==> ruff: not found, run 'mise install'"; \
	fi
	@if [ -n "$(SHELLCHECK)" ]; then \
		echo "==> shellcheck"; \
		$(SHELLCHECK) $(SHELL_FILES); \
	else \
		echo "==> shellcheck: not found, run 'mise install'"; \
	fi
	@if [ -n "$(YAMLLINT)" ]; then \
		echo "==> yamllint"; \
		$(YAMLLINT) -c .yamllint.yaml $(YAML_FILES); \
	else \
		echo "==> yamllint: not found, run 'mise install'"; \
	fi

# Check the built packages in a throwaway Fedora container: install them
# and see that they work. Local only, it is a sanity check before pushing
# to COPR.
test: rpm
	@if [ -z "$(CONTAINER)" ]; then \
		echo "error: podman or docker is needed for 'make test'" >&2; \
		echo "       (override with CONTAINER=...)" >&2; \
		exit 1; \
	fi
	@rm -rf $(TOPDIR)/test
	@mkdir -p $(TOPDIR)/test/rpms
	@cp $(TOPDIR)/*/RPMS/x86_64/*.rpm $(TOPDIR)/test/rpms/
	@echo "==> testing $$(ls $(TOPDIR)/test/rpms/*.rpm | wc -l) packages in $(TEST_IMAGE)"
	$(CONTAINER) run --rm \
		-v $(TOPDIR)/test/rpms:/packages:ro,z \
		-v $(CURDIR)/.github/scripts:/test:ro,z \
		$(TEST_IMAGE) \
		bash /test/smoke-test.sh /packages

clean:
	@rm -rf $(BUILDDIR)

help:
	@echo "Targets:"
	@echo "  all / srpm   build the SRPM of every package"
	@echo "  rpm          build the binary RPMs of every package"
	@echo "  lint         run rpmlint on every spec"
	@echo "  test         build the RPMs and check them in a $(TEST_IMAGE) container"
	@echo "  clean        remove $(BUILDDIR)/"
	@echo "  <pkg>-srpm   build one package: $(PKGS)"
	@echo "  <pkg>-rpm    build one package's binary RPMs"
	@echo "  <pkg>-clean  remove $(TOPDIR)/<pkg>"
	@echo ""
	@echo "Build dir: $(TOPDIR)  (override with BUILDDIR=...)"
