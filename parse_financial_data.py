#!/usr/local/bin/python3

""" Parses the table of financial data from webpages into csv files.
"""

import argparse
import logging
from bs4 import BeautifulSoup
from os import environ, listdir, mkdir, path, system
from time import tzset

# The table of financial data is located in between the prefix and suffix.
TABLE_PREFIX = ("<table border='0' bgColor='ffffff' cellspacing='1'"
                " cellpadding='2' width='705'  align='left' >")
TABLE_SUFFIX = '</table>'

# We use the value of bgcolor to identify rows with financial data.
# Currently the rows of financial data interleave with two background colors.
DATA_BGCOLORS = set(['#f0f0E7', '#e5e5f3'])
# As a sanity check, we also keep track of non-financial data rows,
# all of which should be headers.
HEADER_BGCOLORS = set(['#6566a3', '#aaaad3'])
# For more sanity, we also check the parsed headers against an expected set.
HEADERS = set(['INDICATORS', 'INCOME STATEMENT', '*',
               'INCOME STATEMENT (YEAR-TO-DATE)', 'BALANCE SHEET', 'ASSETS',
               'EQUITY & LIABILITIES', 'CASH-FLOW STATEMENT',
               'OPERATING ACTIVITIES', 'INVESTING ACTIVITIES',
               'FINANCING ACTIVITIES', 'NET CASH FLOW', 'RATIOS CALCULATIONS',
               'PROFIT MARGINS', 'NORMALIZED RATIOS', 'SOLVENCY RATIOS',
               'EFFICIENCY RATIOS', 'ACTIVITY RATIOS', 'LIQUIDITY RATIOS',
               'CAPITAL STRUCTURE RATIOS', 'PROFITABILITY',
               'AGAINST THE INDUSTRY RATIOS', 'CASH FLOW STATEMENT'])
# TODO: We don't track the titles of financial data, only the total number
# of financial data rows; maybe we should check the titles as well.
FINANCIAL_ROW_COUNTS = set([188, 281])

INPUT_EXT = '.html'
OUTPUT_EXT = '.csv'
DELIMITER = '|'

def stringify(v):
  """ A helper method to convert None to '', leaving non-None strings unchanged.
  """
  if v is None: return ''
  return str(v)

def parse(input_path, output_path):
  """ Parses the raw html file and produces a csv file of financial data.
  """
  with open(input_path, 'r') as fp:
    content = fp.read()
  p = content.find(TABLE_PREFIX)
  assert p > 0
  q = content.find(TABLE_SUFFIX, p)
  assert q > p
  soup = BeautifulSoup('%s%s' % (content[p:q], TABLE_SUFFIX))

  count = 0
  with open(output_path, 'w') as fp:
    # TODO: Any of the assertion error betlow should result in the output file
    # being removed, which is not implemented.
    for row in soup.find_all('tr'):
      if row['bgcolor'] in HEADER_BGCOLORS:
        tds = row.find_all('td')
        assert len(tds) == 1
        td = tds[0]
        # One column for title and the rest for five quarters of financial data.
        # This is true even when the table doesn't have five quarters worth of
        # data, in which case some of the cells have empty value.
        assert td['colspan'] == '6'
        assert td.string in HEADERS
        # TODO: Need to print out the section header to differentiate
        # potentially duplicate financial data titles?
        continue
      assert row['bgcolor'] in DATA_BGCOLORS
      tds = row.find_all('td')
      assert len(tds) == 6
      print(DELIMITER.join([stringify(td.string) for td in tds]), file=fp)
      count += 1
  assert count in FINANCIAL_ROW_COUNTS

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--ticker_file', required=True)
  parser.add_argument('--input_dir', required=True)
  parser.add_argument('--output_dir', required=True)
  parser.add_argument('--overwrite', action='store_true')
  parser.add_argument('--verbose', action='store_true')
  args = parser.parse_args()

  environ['TZ'] = 'US/Pacific'
  tzset()

  level = logging.INFO
  if args.verbose:
    level = logging.DEBUG
  logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s',
                      level=level)

  # Tickers are listed one per line.
  with open(args.ticker_file, 'r') as fp:
    tickers = fp.read().splitlines()
  logging.info('Processing %d tickers' % len(tickers))

  for i in range(len(tickers)):
    ticker = tickers[i]
    logging.info('%d/%d: %s' % (i+1, len(tickers), ticker))

    input_dir = '%s/%s' % (args.input_dir, ticker)
    if not path.isdir(input_dir):
      logging.warning('%s does not exist, skipping' % input_dir)
      continue

    output_dir = '%s/%s' % (args.output_dir, ticker)
    if path.isdir(output_dir):
      logging.warning('Output dir exists: %s' % output_dir)
    else:
      mkdir(output_dir)

    input_files = listdir(input_dir)
    logging.info('  Processing %d files' % len(input_files))
    for j in range(len(input_files)):
      input_file = input_files[j]
      logging.info('  %d/%d: %s' % (j+1, len(input_files), input_file))

      assert input_file.endswith(INPUT_EXT)
      input_path = '%s/%s' % (input_dir, input_file)
      output_path = '%s/%s%s' % (
          output_dir, input_file[:-len(INPUT_EXT)], OUTPUT_EXT)

      if path.isfile(output_path) and not args.overwrite:
        logging.warning('  Output file exists and not overwritable: %s' %
            output_path)
        continue

      parse(input_path, output_path)

if __name__ == '__main__':
  main()

