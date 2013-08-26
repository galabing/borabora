#!/usr/local/bin/python3

import os

input_dir = '../data/financial'
pattern = "All amounts in Millions of \t\tUS Dollars<font face='arial' size='2'> except per share items"

folders = os.listdir(input_dir)
for i in range(len(folders)):
  folder = folders[i]
  print('%d/%d: %s' % (i+1, len(folders), folder))
  files = os.listdir('%s/%s' % (input_dir, folder))
  for f in files:
    input_path = '%s/%s/%s' % (input_dir, folder, f)
    print('\t%s' % input_path)
    with open(input_path, 'r') as fp:
      content = fp.read()
    assert content.find(pattern) >= 0

