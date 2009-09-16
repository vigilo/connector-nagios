NAME := connector_nagios
include ../glue/Makefile.common
all: build
lint: lint_pylint
tests: tests_nose
