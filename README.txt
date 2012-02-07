oscodepoint.py
==============

An interface to Ordnance Survey's CodePoint-Open. CodePoint-Open is a free
dataset that maps UK postcodes to coordinates.

`oscodepoint` reads in this data, whether in the original zip or decompressed,
parses the data, and converts grid references to latitude and longitude.

The dataset can be downloaded from
http://www.ordnancesurvey.co.uk/oswebsite/products/code-point-open/


Example:
--------
    >>> from oscodepoint import open_codepoint
    >>> codepoint = open_codepoint('codepo_gb.zip')
    >>> for entry in codepoint.entries():
    ...    print entry['Postcode'], entry['Latitude'], entry['Longitude']
    ...    break  # Over 1.6 million rows
    AB101AA 57.1482995075 -2.09663094048


Too much data? Try limiting the postcode areas:
-----------------------------------------------
    >>> from oscodepoint import open_codepoint
    >>> codepoint = open_codepoint('codepo_gb.zip')
    >>> for entry in codepoint.entries(areas=['NR', 'IP']):
    ...    print entry['Postcode'], entry['Eastings'], entry['Northings']
    ...    break
    NR1 1AA 624068 308352


Want the postcode's county?
---------------------------
Postcode entries have a `Admin_country_code` field. `Doc/Codelist.xls` maps
these codes to county names, and `codepoint.codelist` can be used to access
this file. For example:

    >>> from oscodepoint import open_codepoint
    >>> codepoint = open_codepoint('codepo_gb.zip')
    >>> county_list = codepoint.codelist['County']
    >>> for entry in codepoint.entries(areas=['NR']):
    ...    print entry['Postcode'], entry['Latitude'], entry['Longitude'], county_list.get(entry['Admin_county_code'])
    ...    break
    NR1 1AA 52.6266175146 1.30932087485 Norfolk County


Get the total number of postcodes for your progress bar:
--------------------------------------------------------
    >>> from oscodepoint import open_codepoint
    >>> codepoint = open_codepoint('codepo_gb.zip')
    >>> print codepoint.metadata['area_counts']['NR']
    22730
    >>> print codepoint.metadata['total_count']
    1692241
