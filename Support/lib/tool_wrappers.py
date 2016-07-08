# encoding: utf-8

import os
import sys
import json
import subprocess
import socket
import time
import exit_codes as exit
import webpreview as wp
from calvin.csparser.codegen import calvin_codegen
# import calvin.Tools.cscompiler as cc
import calvin.Tools.csruntime as csruntime
# import calvin.Tools.csviz as csviz
# from calvin.csparser.parser import calvin_parser
from calvin.actorstore.store import DocumentationStore
import calvin.utilities.calvinconfig as calvinconfig


def format_heading(heading):
    print '<h3>{}</h3>'.format(heading)

def issue_report(issuetracker, line_offset):
    if issuetracker.issue_count == 0:
        format_heading("No issues!")
        return
    
    # Handle offset if any
    if line_offset:
        for issue in issuetracker.issues():
            if 'line' in issue:
                issue['line'] += line_offset
    
    extra = {
        'path': os.environ.get('TM_FILEPATH'),
        'filename': os.environ.get('TM_FILENAME'),
        'line': 0, 'col': 0
    }
    fmt = issue_format()  
    if issuetracker.error_count:
        format_heading("Errors:")
        for issue in issuetracker.formatted_errors(sort_key='line', custom_format=fmt, **extra):
            print issue
    if issuetracker.warning_count:
        format_heading("Warnings:")
        for issue in issuetracker.formatted_warnings(sort_key='line', custom_format=fmt, **extra):
            print issue


def issue_format():
    if 'TM_FILEPATH' in os.environ:
        fmt = '<p>{reason} <a href="txmt://open?url=file://{path}&line={line}&column={col}">{filename} {line}:{col}</a></p>'
    else:
        fmt = '<p>{reason} {line}:{col}</p>'
    return fmt

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

def get_source(filepath=None):
    source = ""
    if filepath:
        with open(filepath, 'r') as f:
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


def check_syntax(filepath=None):
    source_text, line_offset = get_source(filepath)
    appname = os.environ.get('TM_FILENAME', 'untitled')
    # Prevent . from appearing in appname (crashes deployer)
    appname = appname.split('.')[0]
    deployable, issuetracker = calvin_codegen(source_text, appname)
    issue_report(issuetracker, line_offset)
    return deployable, issuetracker


def compile_source(filepath=None):
    deployable, issuetracker = check_syntax(filepath)
    format_heading('Deployable:')
    print json.dumps(deployable, indent=4)


def _get_ip_address():
    return socket.gethostbyname(socket.gethostname())

def run(script, timeout):
    deployable, issuetracker = check_syntax(script)

    if issuetracker.error_count:
        return
        
    ip = _get_ip_address()
    uris = ["calvinip://{}:5000".format(ip)]
    control_uri = "http://{}:5001".format(ip)
    attr = {'indexed_public': {'node_name': {'name': 'TextMate'}}}
    try:
        csruntime.dispatch_and_deploy(deployable, timeout, uris, control_uri, attr, None)
    except KeyboardInterrupt:
        # User terminated the runtime (CTRL-C)
        pass
    except:
        print "Could not start runtime and/or application"


def run_debug(script, timeout):
    import logging
    config = calvinconfig.get()
    debug_modules = config.get('developer', 'debug_modules')
    if not debug_modules:
        print "No 'debug_modules' option in 'developer' section of config => output verbosity is INFO everywhere."
    else:
        for m in debug_modules:
            csruntime.get_logger(m).setLevel(logging.DEBUG)
    print "\n{0}\n{1}\n{0}".format("-"*80, config)
    run(script, timeout)


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
