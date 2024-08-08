# -*- coding: utf-8 -*-
import pathlib
import json


def read_json(file_path: pathlib.Path) -> dict:
    """
    Reads file and returning ready json dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
