#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Obfuscation.main import main

if __name__ == '__main__':
    # 手动设置参数而不是通过命令行传递
    args = {
        "input": "bytecode",
        "bytecode":"bytecode",
        "optimize": False,
        "no_split_functions": False,
        "verbosity": "None",
        "supplemental_cfg_file": None,
        "stdout_to": None
    }

    main()
