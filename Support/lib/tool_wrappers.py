# encoding: utf-8

import os
import sys
import json
import exit_codes as exit
import webpreview as wp
import calvin.Tools.cscompiler as cc

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

    print wp.html_header('CalvinScript Syntax Check', os.environ.get('TM_FILENAME', 'unsaved'))
    issue_report(errors, warnings, line_offset)
    print wp.html_footer()


def compile_source():
    source, line_offset = get_source()
    deployable, errors, warnings = cc.compile(source)

    print wp.html_header('CalvinScript Compile', os.environ.get('TM_FILENAME', 'unsaved'))
    issue_report(errors, warnings, line_offset)
    format_heading('Deployable:')
    print '<pre>'
    print json.dumps(deployable, indent=4)
    print '</pre>'
    print wp.html_footer()


