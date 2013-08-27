#!/usr/local/bin/python3

""" Joins financial data in this dir (ie, from ih.advfn.com) with the price
    data in the stockp project.  The output files will be the intersection
    between (russell3000 - bad_tickers) and the samples from stockp, and for
    each output file the rows will be the intersection of dates on which
    both sets of data are available.  One difference between the two projects
    is that, in stockp, the date yyyy-mm indicates the "beginning" of such
    month, while in this dir it indicates the end.  Therefore we join (mm-1)
    in this dir with mm in the stockp project.
"""

