#!/usr/bin/env python
#
# Use of this software is subject to the terms specified in the LICENCE
# file included in the distribution package, and also available via
# http://dbdoc.sourceforge.net/
#

#
# Generates HTML information from a schema and a properties file
#

#
# Valid property file entries are:
#   schema.name
#   schema.notes
#   table.<tablename>.shortdesc
#   table.<tablename>.notes
#   table.<tablename>.column.<columnname>.shortdesc
#   table.<tablename>.index.<indexname>.shortdesc
#

import props, os, string

class StandardDoclet:
    def __init__(self, schema, outdir, descr_file, tables=None):
        self.outdir = outdir
        self.descr_file = descr_file
        self.descs = props.Properties()
        if descr_file:
            f = open(descr_file, 'r')
            self.descs.load(f)
            f.close()
        self.schema = schema
        if not tables:
            self.tables = schema.get_tables()
        else:
            self.tables = []
            for tablename in tables:
                table = schema.get_table(tablename)
                if not table:
                    raise ValueError, "no such table in schema: %s" % tablename
        self._get_fkeys()
        self._generate_pages()

    def _get_fkeys(self):
        self._fkeys = {}
        for table in self.schema.get_tables():
            for col in table.get_columns():
                if col.references:
                    other_table, other_col = col.references
                    refs = self._fkeys.get(other_table, None)
                    if not refs:
                        self._fkeys[other_table] = refs = []
                    refs.append((table.name, col.name))

    def _standard_header(self, title):
        return '<html><head><title>DBDoc: %s (%s)</title></head>\n<body bgcolor=#ffffff">\n' % (title, self.schema.name)

    def _standard_footer(self):
        return '<br><hr size=1 noshade>\n<small>Generated by <a href="http://dbdoc.sourceforge.net/">dbdoc</a>, (c) 2001 Steve Purcell</small>\n</body></html>\n'

    def _generate_pages(self):
        self._generate_table_pages()
        self._generate_front_page()
        self._generate_index()

    def _generate_table_pages(self):
        for table in self.tables:
            print "doing table", table.name
            tablefilename = os.path.join(self.outdir, "table-%s.html" % table.name)
            f = open(tablefilename, 'w')
            f.write(self._standard_header(table.name))
            f.write('<small><a href="index.html">index</a> | %s</small>\n' % table.name)
            f.write('<h1>Table %s</h1>\n' % table.name)
            f.write('<hr noshade size=1>\n')
            shortdesc = self.descs.get('table.%s.shortdesc' % table.name, None)
            if shortdesc:
                f.write('<p>%s</p>\n' % shortdesc)
            notes = self.descs.get('table.%s.notes' % table.name, None)
            if notes:
                f.write('<h2>Notes</h2>\n')
                f.write(notes) # allows html
            f.write('<h2>Columns</h2>\n')
            f.write('<table border=1>\n<tr><th>Column</th><th>Type</th><th>Nullable</th><th>Default</th><th>Description</th></tr>\n')
            for col in table.get_columns():
                f.write('<tr>')
                pkey = (col.name == table.primary_key_name)
                if pkey:
                    name_str = '<strong>%s</strong>' % col.name
                else:
                    name_str = col.name
                if col.references is not None:
                    other_table, other_col = col.references
                    f.write('<td><a href="table-%s.html#col-%s">%s</a></td>' % (other_table, other_col, name_str))
                else:
                    f.write('<td>%s</td>' % name_str)
                f.write('<td>%s (%s)</td>' % (col.type, col.length))
                f.write('<td>%s</td>' % (col.nullable and 'yes' or 'no'))
                f.write('<td>%s</td>' % (col.default_value))
                col_desc = self.descs.get('table.%s.column.%s.shortdesc' % (table.name, col.name), "&nbsp;")
                f.write('<td>%s</td>' % col_desc)
                f.write('</tr>\n')

            f.write('</table>\n')
            if table.primary_key_name:
                f.write('<p>(primary key column name in <strong>bold</strong>)</p>\n')

            f.write('<h2>Referenced by</h2>\n')
            refs = self._fkeys.get(table.name, None)
            if refs:
                f.write('<table border=1>\n<tr><th>Table</th><th>Column</th><th>Description</th></tr>\n')
                for other_table, other_col in refs:
                    ref_table = self.schema.get_table(other_table)
                    ref_col = ref_table.get_column(other_col)
                    col_desc = self.descs.get('table.%s.column.%s.shortdesc' % (other_table, other_col), "&nbsp;")
                    f.write('<tr><td><a href="table-%s.html">%s</a></td><td>%s</td><td>%s</td></tr>\n' % (other_table, other_table, other_col, col_desc))
                f.write('</table>\n')
            else:
                f.write('<p>None.</p>\n')

            f.write('<h2>Indexes</h2>\n')
            indexes = table.get_indexes()
            if indexes:
                f.write('<table border=1>\n<tr><th>Index name</th><th>Unique</th><th>Columns</th><th>Description</th></tr>\n')
                for index in indexes:
                    descr = self.descs.get('table.%s.index.%s.shortdesc' % (table.name, index.name), '&nbsp;')
                    uniquestr = index.unique and 'yes' or 'no'
                    f.write('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' %
                            (index.name, uniquestr, string.join(index.get_column_names(), ', '), descr))
                f.write('</table>\n')
            else:
                f.write('<p>None.</p>\n')

            f.write(self._standard_footer())
            f.close()

    def _generate_front_page(self):
        print "doing front page"
        f = open(os.path.join(self.outdir, 'index.html'), 'w')
        title = self.descs.get('schema.name', None) or "Table index"
        f.write(self._standard_header(title))
        f.write('<h1>%s</h1>\n' % title)
        f.write('<hr noshade size=1>\n')
        notes = self.descs.get('schema.notes', None)
        if notes:
            f.write('<h2>Notes</h2>\n')
            f.write(notes)
        f.write('<h2>Tables</h2>\n')
        f.write('<table border=1><tr><th>Table</th><th>Summary</th></tr>\n')
        for table in self.tables:
            tabledesc = self.descs.get('table.%s.shortdesc' % table.name, "no summary available")
            f.write('<tr><td><a href="table-%s.html">%s</a></td><td>%s</td></tr>\n' % (table.name, table.name, tabledesc))
        f.write('</table>')
        f.write(self._standard_footer())
        f.close()
    
    def _generate_index(self):
        pass

main = StandardDoclet