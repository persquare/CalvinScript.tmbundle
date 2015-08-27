# encoding: utf-8

import os
import sys
import json
import subprocess
import time
import exit_codes as exit
import webpreview as wp
import calvin.Tools.cscompiler as cc
import calvin.Tools.csruntime as csruntime
import calvin.Tools.csviz as csviz
from calvin.csparser.parser import calvin_parser
from calvin.actorstore.store import DocumentationStore
import calvin.utilities.calvinconfig as calvinconfig


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

def get_source(file=None):
    source = ""
    if file:
        with open(file, 'r') as f:
           source = f.read()
        return source, 0

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


def check_syntax(file=None):
    source, line_offset = get_source(file)
    deployable, errors, warnings = cc.compile(source)
    if errors or warnings:
        issue_report(errors, warnings, line_offset)
    else:
        format_heading("Success!")

    return deployable, errors, warnings


def compile_source(file=None):
    deployable, _, _ = check_syntax(file)

    format_heading('Deployable:')
    print json.dumps(deployable, indent=4)


def run(script):
    source, line_offset = get_source(script)
    deployable, errors, warnings = cc.compile(source)

    issue_report(errors, warnings, line_offset)
    if errors:
        return

    uri = "calvinip://localhost:5000"
    control_uri = "http://localhost:5001"
    rt = csruntime.runtime(uri, control_uri, None)
    app_id = csruntime.deploy(rt, deployable, None)

    timeout = 2
    time.sleep(timeout)

def run_debug(script):
    import logging
    config = calvinconfig.get()
    debug_modules = config.get('developer', 'debug_modules')
    if not debug_modules:
        print "No 'debug_modules' option in 'developer' section of config => output verbosity is INFO everywhere."
    else:
        for m in debug_modules:
            csruntime.get_logger(m).setLevel(logging.DEBUG)
    print "\n{0}\n{1}\n{0}".format("-"*80, config)
    run(script)

def document(what):
    store = DocumentationStore()
    print store.help(what)

def visualize():
    src = os.environ.get('TM_FILENAME', 'untitled.calvin')
    source_text, line_offset = get_source()
    ir, errors, warnings = calvin_parser(source_text, src)
    dot_src = csviz.ScriptViz(ir).render()
    args = ['dot', '-Tsvg']
    try:
        p = subprocess.Popen(args, stdin=subprocess.PIPE)
        p.stdin.write(dot_src.encode('utf-8'))
        p.stdin.close() # signal end of file
    except:
        print 'Visualization requires \'dot\' command from <a href="http://www.graphviz.org">GraphViz</a>'
