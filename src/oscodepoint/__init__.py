"""
oscodepoint.py
==============

An interface to Ordnance Survey's CodePoint-Open. CodePoint-Open is a free
dataset that maps UK postcodes to coordinates.

`oscodepoint` reads in this data, whether in the original zip or decompressed,
parses the dataset, and converts grid references to latitude and longitude.

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
Try `codepoint.codelist`, an interface to `Doc/Codelist.xls`. For example:

    >>> from oscodepoint import open_codepoint
    >>> codepoint = open_codepoint('codepo_gb.zip')
    >>> county_list = codepoint.codelist['County']
    >>> for entry in codepoint.entries(areas=['NR']):
    ...    print entry['Postcode'], entry['Latitude'], entry['Longitude'], county_list.get(entry['Admin_county_code'])
    ...    break
    NR1 1AA 52.6266175146 1.30932087485 Norfolk County
"""


import csv
import fnmatch
import glob
import os.path
import pyproj
import re
import xlrd
import zipfile


def open_codepoint(filename):
    """
    Open a CodePoint directory or zip file. Returns a CodePointDir or
    CodePointZip object.
    """

    if os.path.isdir(filename):
        return CodePointDir(filename)
    else:
        return CodePointZip(filename)


class lazyproperty(object):
    """
    Memoizing property. Calls `fget()` once, then stores the result.
    """

    def __init__(self, fget):
        self.fget = fget
    
    def __get__(self, obj, type=None):
        value = self.fget(obj)
        setattr(obj, self.fget.func_name, value)
        return value


class BaseCodePoint(object):
    """
    Abstract access to CodePoint data. You should use `CodePointZip`,
    `CodePointDir`, or just forget about the difference and use `open_codepoint()`.
    """

    root = 'Code-Point Open/'
    headers_name = 'Doc/Code-Point_Open_Column_Headers.csv'
    codelist_name = 'Doc/Codelist.xls'
    nhs_codelist_name = 'Doc/NHS_Codelist.xls'
    data_name_format = 'Data/%s.csv'
    
    def entries(self, areas=None, to_proj=pyproj.Proj(init='epsg:4326')):
        """
        Iterate over postcode entries.

        Limit the postcode areas with the `areas` parameter. Set to `None`
        (the default) to iterate over everything.

        Grid references are converted to latitude and longitude - the target
        coordinate system is defined by the `to_proj` parameter. Set it to a
        `pyproj.Proj` instance to change from the default of WGS84, or use
        `None` if you don't want coordinate conversion.
        """

        from_proj = pyproj.Proj(init='epsg:27700') # British National grid

        if areas is None:
            areas = self.areas

        for area in areas:
            if not re.search(r'^[A-Za-z]{1,2}$', area):
                raise ValueError('Incorrect format for area: '
                                 'expected 1 or 2 letters, got "%s"' % (area,))
            
            for row in self._get_name_rows(self.data_name_format % area.lower()):
                entry = dict(zip(self.long_headers, row))

                if to_proj is not None:
                    eastings, northings = float(entry['Eastings']), float(entry['Northings'])
                    lng, lat = pyproj.transform(from_proj, to_proj, eastings, northings)
                    entry['Longitude'], entry['Latitude'] = lng, lat

                yield entry

    @lazyproperty
    def areas(self):
        return list(self._get_areas())

    @lazyproperty
    def long_headers(self):
        return self._get_headers()['long']

    @lazyproperty
    def codelist(self):
        return self._get_codelist()
    
    @lazyproperty
    def nhs_codelist(self):
        return self._get_nhs_codelist()
    
    def _areas_from_names(self, names):
        pattern = re.compile(r'[\\/]([a-z]{1,2})\.csv$')
        for name in names:
            match = pattern.search(name)
            if match:
                yield match.group(1)


class CodePointZip(BaseCodePoint):
    """
    Read CodePoint data from a zip file.
    """

    def __init__(self, zip_filename):
        self.zip_file = zipfile.ZipFile(zip_filename)
    
    def _open(self, name):
        return self.zip_file.open(self.root + name)
    
    def _read(self, name):
        return self.zip_file.read(self.root + name)

    def _get_areas(self):
        pattern = self.root + (self.data_name_format % '*')
        return self._areas_from_names(
            name for name in self.zip_file.namelist()
            if fnmatch.fnmatch(name, pattern)
        )
    
    def _get_name_rows(self, name):
        return csv.reader(self._open(name))

    def _get_headers(self):
        short_headers, long_headers = csv.reader(self._open(self.headers_name))
        return dict(
            short=short_headers,
            long=long_headers,
        )
 
    def _get_codelist(self):
        return CodeList(self.codelist_name, file_contents=self._read(self.codelist_name))
    
    def _get_nhs_codelist(self):
        return NHSCodeList(self.codelist_name, file_contents=self._read(self.nhs_codelist_name))


class CodePointDir(BaseCodePoint):
    """
    Read CodePoint data from a decompressed zip file.
    """

    def __init__(self, path):
        self.path = path
        if os.path.isdir(os.path.join(self.path, self.root)):
            self.path = os.path.join(self.path, self.root)
    
    def _get_areas(self):
        return self._areas_from_names(glob.glob(os.path.join(self.path, self.data_name_format % '*')))
    
    def _get_name_rows(self, name):
        return csv.reader(open(os.path.join(self.path, name)))

    def _get_headers(self):
        short_headers, long_headers = csv.reader(open(os.path.join(self.path, self.headers_name)))
        return dict(
            short=short_headers,
            long=long_headers,
        )
 
    def _get_codelist(self):
        return CodeList(os.path.join(self.path, self.codelist_name))
    
    def _get_nhs_codelist(self):
        return NHSCodeList(os.path.join(self.path, self.nhs_codelist_name))


class CodeList(dict):
    """
    The CodePoint download has a Doc/Codelist.xls Excel-format spreadsheet.
    This has multiple worksheets, with one lookup table per sheet.
    `CodeList` reads in those lookup tables. Use it via `codepoint.codelist`.
    """

    def __init__(self, filename, file_contents=None):
        book = xlrd.open_workbook(filename, file_contents=file_contents)

        lookup_aliases = {}
        for sheet in book.sheets():
            if sheet.name == 'Metadata':
                # The metadata sheet doesn't have any lookups.
                continue
            
            self[sheet.name] = dict(
                (key, value)
                for (value, key) in (
                    sheet.row_values(row_index)
                    for row_index in xrange(sheet.nrows)
                )
            )

            if sheet.name == 'AREA_CODES':
                # The AREA_CODES sheet has a mapping of sheet names to
                # friendlier names. We'll use these at the end of the loop.
                lookup_aliases = self[sheet.name]
        
        for alias, lookup_name in lookup_aliases.iteritems():
            self[alias] = self[lookup_name]


class NHSCodeList(dict):
    """
    Similar to `CodeList`, but:
      * No Metadata or AREA_CODES worksheet.
      * The key and value columns are in the opposite order.
    """

    def __init__(self, filename, file_contents=None):
        book = xlrd.open_workbook(filename, file_contents=file_contents)

        for sheet in book.sheets():
            self[sheet.name] = dict(
                (key, value)
                for (key, value) in (
                    sheet.row_values(row_index)
                    for row_index in xrange(sheet.nrows)
                )
            )
