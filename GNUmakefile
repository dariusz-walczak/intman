# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

FIND ?= find
PYLINT ?= pylint3


PATH_DATA = ./data
PATH_SCRIPT = ./script


pylint:
	$(FIND) $(PATH_SCRIPT) -type f -a -name '*.py' -print0 | xargs -0 $(PYLINT) --rcfile=$(PATH_DATA)/pylint.rc
