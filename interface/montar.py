#!/usr/bin/env python3
"""Monta a página da interface: injeta catálogo (marcas, LUTs com miniaturas, filtros, fontes) no template.
Uso: python3 interface/montar.py dados.json saida.html"""
import json, sys, os
t = open(os.path.join(os.path.dirname(__file__), "grace_studio.template.html")).read()
d = open(sys.argv[1]).read().replace("</", "<\\/")
open(sys.argv[2], "w").write(t.replace("__DADOS__", d))
