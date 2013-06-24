#!/usr/bin/python3

import argparse
import logging
import re
from os import environ, mkdir, path, remove, system
from time import tzset

WGET = '/usr/local/bin/wget'
# TODO(lingyang): This value need to be in sync with reality, maybe add a
# check during data download.
START_STEP = 5  # step for istart_date

# Patterns for analyzing the downloaded pages.
NO_DATA = 'No financial data available from this page.'
SELECT_PREFIX = "<select id='istart_dateid' name='istart_date'"
SELECT_SUFFIX = '</select>'
# Eg,
#     <option  value='0' selected>2001/12</option>
#     <option  value='1'>2002/12</option>
SELECT_DATE_PATTERN = ("<option\s+value='(?P<value>\d+)'(|\s+selected)>"
                       "\d{4}/\d{2}</option>")
SELECT_DATE_PROG = re.compile(SELECT_DATE_PATTERN)

def download(ticker, start, output_dir, overwrite):
  """ Downloads one page of financial data for the specified ticker,
      writes the file to the specified dir; skips downloading if the
      destination file exists, unless overwrite is specified.

      If the download fails, the (probably empty) destination file
      is cleared upon return.

      Returns the path to the destination file, or None if the file
      is cleared.
  """
  output_path = '%s/%s-%d.html' % (output_dir, ticker, start)
  if path.isfile(output_path) and not overwrite:
    logging.warning('File exists and not overwritable: %s' % output_path)
    return output_path
  url = ('http://ih.advfn.com/p.php?pid=financials'
         '&mode=quarterly_reports&symbol=%s&istart_date=%d' % (ticker, start))
  cmd = '%s -q "%s" -O %s' % (WGET, url, output_path)
  if system(cmd) != 0 and path.isfile(output_path):
    remove(output_path)
    return None
  return output_path

def check_and_get_page_count(page_path):
  """ Checks the downloaded page is valid and extracts the page count for
      the corresponding ticker.

      If the downloaded page is invalid, the file is cleared upon return.
      Returns the page count, or 0 if the downloaded page is invalid.
  """
  assert path.isfile(page_path)
  with open(page_path, 'r') as fp:
    content = fp.read()
  if content.find(NO_DATA) >= 0:
    logging.warning('File contains "%s": %s' % (NO_DATA, page_path))
    remove(page_path)
    return 0
  p = content.find(SELECT_PREFIX)
  if p < 0:
    logging.warning('File does not contain "%s": %s' %
                    (SELECT_PREFIX, page_path))
    remove(page_path)
    return 0
  q = content.find(SELECT_SUFFIX, p)
  assert q > p
  hits = SELECT_DATE_PROG.findall(content[p:q])
  values = sorted([int(hit[0]) for hit in hits])
  assert all(values[i] == i for i in range(len(values)))
  # TODO(lingyang): More verifications in page content?
  return values[-1] + 1

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--ticker_file', required=True)
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

    output_dir = '%s/%s' % (args.output_dir, ticker)
    if path.isdir(output_dir):
      logging.warning('Output dir exists: %s' % output_dir)
    else:
      mkdir(output_dir)

    # Download the first page.
    first_page_path = download(ticker, 0, output_dir, args.overwrite)
    page_count = check_and_get_page_count(first_page_path)
    logging.info('%s: %d pages of financial data' % (ticker, page_count))

    # Download the rest of the pages.
    for start in range(START_STEP, page_count, START_STEP):
      logging.info('Downloading %s:%d' % (ticker, start))
      page_path = download(ticker, start, output_dir, args.overwrite)
      # TODO(lingyang): Content verification.
      assert page_path is not None

if __name__ == '__main__':
  main()

