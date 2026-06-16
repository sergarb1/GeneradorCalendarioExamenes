# -*- coding: utf-8 -*-
"""
Lanzador de tests con salida detallada.

Uso:
    python run_tests.py            # Todos los tests
    python run_tests.py -k parcial # Filtra por nombre

Los tests estan en la carpeta tests/ y usan unittest.
"""
import unittest
import sys

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
