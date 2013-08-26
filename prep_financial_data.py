#!/usr/local/bin/python3

""" Prepares financial data for training.  For each merged file,
    1) keep the rows with all valid values,
    2) lower-case the header,
    3) sanitize the values (eg, 123,456 to 123456),
    4) fill in the missing dates, using the most recent available values.

    About 20% of the files are classified as "bad" because they are missing
    some of the required headers (these correspond to
    FINANCIAL_ROW_COUNTS=188 in parse_financial_data.py).
    These tickers are manually collected to data/bad_tickers.txt on 08/25.
"""

import argparse
import logging
from os import environ, path
from time import tzset

DATE_HEADER = 'quarter end date'
REQUIRED_HEADERS = {
    'book value per share',
    'cash flow',
    'cash flow per share',
    'intangibles',
    'preferred dividends',
    'price/cash flow ratio',
    'return on stock equity (roe)',
    'total assets',
    'total debt/equity ratio',
    'total equity',
    'total common shares out',
    'total liabilities',
    'total net income',
    'total revenue',
}

def next_date(date):
  y, m = date.split('/')
  y, m = int(y), int(m)
  m += 1
  if m > 12:
    y += 1
    m = 1
  return '%04d/%02d' % (y, m)

def sanitize(value):
  v = value.replace(',', '')
  try:
    v = float(v)
    return v
  except ValueError:
    return None

def prep(input_path, output_path):
  with open(input_path, 'r') as fp:
    lines = fp.read().splitlines()
  assert len(lines) > 0
  items = lines[0].split('|')
  assert len(items) > 1
  assert items[0] == DATE_HEADER
  dates = [items[1]]
  indexes = [1]
  for i in range(2, len(items)):
    while next_date(dates[-1]) < items[i]:
      dates.append(next_date(dates[-1]))
      indexes.append(indexes[-1])
    assert next_date(dates[-1]) == items[i]
    dates.append(items[i])
    indexes.append(i)
  fp = open(output_path, 'w')
  print('%s|%s' % (DATE_HEADER, '|'.join(dates)), file=fp)
  headers = set()
  for i in range(1, len(lines)):
    items = lines[i].split('|')
    values = []
    ok = True
    for j in indexes:
      v = sanitize(items[j])
      if v is None:
        ok = False
        break
      values.append(v)
    if ok:
      header = items[0].lower()
      print('%s|%s' % (header, '|'.join([str(v) for v in values])), file=fp)
      headers.add(header)
  fp.close()
  return REQUIRED_HEADERS.issubset(headers)

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
  
  bad_tickers = set()
  for i in range(len(tickers)):
    ticker = tickers[i]
    logging.info('%d/%d: %s' % (i+1, len(tickers), ticker))
    input_path = '%s/%s.csv' % (args.input_dir, ticker)
    if not path.isfile(input_path):
      logging.warning('%s does not exist, skipping' % input_path)
      continue
    output_path = '%s/%s.csv' % (args.output_dir, ticker)
    if path.isfile(output_path) and not args.overwrite:
      logging.warning('%s exists and is not overwritable' % output_path)
      continue
    if not prep(input_path, output_path):
      logging.warning('Bad ticker: %s' % ticker)
      bad_tickers.add(ticker)
  logging.info('%d bad tickers: %s' % (len(bad_tickers), bad_tickers))

if __name__ == '__main__':
  main()

