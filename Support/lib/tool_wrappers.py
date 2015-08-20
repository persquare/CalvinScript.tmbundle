# encoding: utf-8

import os
import sys
import json
import subprocess
import exit_codes as exit
import webpreview as wp
import calvin.Tools.cscompiler as cc
import calvin.Tools.csviz as csviz
from calvin.csparser.parser import calvin_parser

def format_heading(heading):
    print '<h3>{}</h3>'.format(heading)

def issue_report(errors, warnings, line_offset):
    if errors:
        format_heading("Errors:")
        for error in errors:
            format_issue(error, line_offset)
    if warnings:
        format_heading("Warnings:")
        for warning in warnings:
            format_issue(warning, line_offset)
    if not errors and not warnings:
        format_heading("Success!")


def format_issue(issue, line_offset):
    issue['line'] += line_offset
    if 'TM_FILEPATH' in os.environ:
        fmt = '<p>{reason} <a href="txmt://open?url=file://{path}&line={line}&column={col}">{file} {line}:{col}</a></p>'
    else:
        fmt = '<p>{reason} {line}:{col}</p>'
    print fmt.format(path=os.environ.get('TM_FILEPATH'), file=os.environ.get('TM_FILENAME'), **issue)

def parse_selection(sel):

    def pos2linecol(pos):
        if ':' in pos:
            line, col = pos.split(':')
        else:
            line, col = pos, 0
        return int(line), int(col)

    # Drop multiple selections after first
    sel = sel.split(',', 1)[0]
    # Split into start and end position
    if '-' in sel:
        start, end = sel.split('-')
    else:
        start, end = sel, sel
    # Convert to int tuples with (line, col)
    start = pos2linecol(start)
    end = pos2linecol(end)
    return start, end

def get_source():
    source = os.environ.get('TM_SELECTED_TEXT', None)
    if source:
        # Now we need to figure out the line number of the first selected line
        (line_offset, _), (_, _) = parse_selection(os.environ.get('TM_SELECTION'))
        line_offset -= 1
    else:
        # Get full document
        source = sys.stdin.read()
        line_offset = 0
    return source, line_offset


def check_syntax():
    source, line_offset = get_source()
    _, errors, warnings = cc.compile(source)
    issue_report(errors, warnings, line_offset)


def compile_source():
    source, line_offset = get_source()
    deployable, errors, warnings = cc.compile(source)

    issue_report(errors, warnings, line_offset)

    format_heading('Deployable:')
    print json.dumps(deployable, indent=4)



def visualize(fmt='pdf'):
    # Get source
    # Generate dot source
    # Pipe to dot
    # Capture result in temp file
    # Render file in HTML view
    src = os.environ.get('TM_FILENAME', 'untitled.calvin')
    # dst = '{0}/{1}.pdf'.format(os.environ.get('TMPDIR', '/Users/eperspe'), src)
    dst = '/Users/eperspe/foo2.pdf'
    dot = os.environ.get('TM_DOT', 'dot')


    # print '<pre>'
    # os.system('which python')
    #
    # for p in sys.path:
    #     print p
    #
    # for k,v in os.environ.iteritems():
    #     print '{} --> {}\n'.format(k, v)
    #
    # print '</pre>'




    source_text, line_offset = get_source()
    ir, errors, warnings = calvin_parser(source_text, src)
    dot_src = csviz.ScriptViz(ir).render()

    # print dot_src
    # print dst

    print dot

    # args = ['dot', '-Tpdf', '-o', '/Users/eperspe/foo.pdf']
    # p = subprocess.Popen(args, stdin=subprocess.PIPE)
    # p.stdin.write(dot_src.encode('utf-8'))
    # p.stdin.close() # signal end of file
    # os.system("dot -Tpdf -o /tmp/dot_foo.pdf")

# # Prepare output window.
# html_header 'Generate Graph' "$FILE"
# SRC=${TM_FILENAME:-untitled.dot}
# DST="${TMPDIR:-/tmp}/dot_${SRC%.*}.pdf"
# ERR="${TMPDIR:-/tmp}/dot_errors"
# DOT="${TM_DOT:-dot}"
#
# # Compile.
# if "$DOT" -Tpdf -o "$DST" /dev/stdin &>"$ERR"; then
#   echo "<meta http-equiv='refresh' content='0; file://$DST'>"
# else
#   pre <"$ERR"
# fi
# rm -f "$ERR"
# html_footer
