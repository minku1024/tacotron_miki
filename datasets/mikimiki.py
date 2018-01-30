import io
import os
import sys
import json
import string
import argparse
import operator
import numpy as np
from pprint import pprint

jsonlist = list()

for root, dirs, files in os.walk('miki2/audio'):
    for fname in files:
        full_fname = os.path.join(root, fname)
        if full_fname.endswith(".txt"):
            f = open(full_fname, 'r')
            lines = f.readlines()
            for line in lines:
#                print(line)
                if line.find('{') != -1:
                    continue;
                elif line.find('}') != -1:
                    continue;
                elif line.find(":"):
                    jsonlist.append(line)
            f.close()

jsonlist.sort()
#print(jsonlist)

fw = open("mikimiki.json", 'w')
fw.write("{\n")
for line in jsonlist:
    fw.write("  " + line + ",")

fw.write("}")
fw.close()

