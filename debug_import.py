import os
import sys

print("PWD =", os.getcwd())
print("PYTHONPATH =", sys.path)

# test import
from logic.text_seleccion import elegir_no_repetido
print("IMPORT OK")
