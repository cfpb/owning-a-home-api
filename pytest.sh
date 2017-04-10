#!/usr/bin/env bash
set -e

# coverage erase
coverage run manage.py test "$@"
coverage report -m
