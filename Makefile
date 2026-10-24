# Local RPM builds for the packages in this repo.
#
#   make             build the SRPM of every package
#   make srpm        same as above
#   make rpm         also build the binary RPMs (needs the build deps)
#   make <pkg>-srpm  build a single package
#   make <pkg>-rpm   build the binary RPMs of a single package
#   make lint        run rpmlint on every spec
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

SPECS := $(wildcard */*.spec)
PKGS   := $(sort $(notdir $(patsubst %/,%,$(dir $(SPECS)))))

$(foreach p,$(PKGS),$(eval SPEC_$(p) := $(wildcard $(p)/*.spec)))

# One pair of rules per package: stage the vendored files into SOURCES/,
# then build with a per-package topdir so packages never mix sources.
define PACKAGE_RULES
$(1)-srpm:
	@echo "==> $(1): SRPM -> $(TOPDIR)/$(1)"
	@rm -rf $(TOPDIR)/$(1)/BUILD
	@mkdir -p $(TOPDIR)/$(1)/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
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

.PHONY: all srpm rpm lint clean help \
        $(foreach p,$(PKGS),$(p)-srpm $(p)-rpm $(p)-clean)

all: srpm

srpm: $(foreach p,$(PKGS),$(p)-srpm)

rpm: $(foreach p,$(PKGS),$(p)-rpm)

lint:
	@for s in $(SPECS); do \
		echo "==> rpmlint $$s"; \
		$(RPLINT) $$s || true; \
	done

clean:
	@rm -rf $(BUILDDIR)

help:
	@echo "Targets:"
	@echo "  all / srpm   build the SRPM of every package"
	@echo "  rpm          build the binary RPMs of every package"
	@echo "  lint         run rpmlint on every spec"
	@echo "  clean        remove $(BUILDDIR)/"
	@echo "  <pkg>-srpm   build one package: $(PKGS)"
	@echo "  <pkg>-rpm    build one package's binary RPMs"
	@echo "  <pkg>-clean  remove $(TOPDIR)/<pkg>"
	@echo ""
	@echo "Build dir: $(TOPDIR)  (override with BUILDDIR=...)"
