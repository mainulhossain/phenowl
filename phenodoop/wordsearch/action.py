import sys
import os
from ..hadoop import run_hadoop_example

def search_word(input, output, expr):
    run_hadoop_example('grep', input, output, expr)