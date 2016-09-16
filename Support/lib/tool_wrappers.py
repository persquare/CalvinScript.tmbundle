# encoding: utf-8

import os
import sys
import json
import subprocess
import socket
import time
import exit_codes as exit
import webpreview as wp
import calvin.Tools.csruntime as csruntime
import calvin.utilities.calvinconfig as calvinconfig
from calvin.csparser.codegen import calvin_codegen
from calvin.csparser.visualize import visualize_script, visualize_component, visualize_deployment
from calvin.actorstore.store import DocumentationStore
from calvin.utilities import calvinlogger
from calvin.csparser.complete import Completion
# from plistlib import writePlistToString, readPlistFromString

dialog = os.environ['DIALOG']

def format_heading(heading):
    print '<h3>{}</h3>'.format(heading)

def issue_report(issuetracker, line_offset, report_success=True):
    if issuetracker.issue_count == 0 and report_success:
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

def get_source(filepath=None, return_selection=True):
    source = ""
    if filepath:
        with open(filepath, 'r') as f:
           source = f.read()
        return source, 0

    selection = os.environ.get('TM_SELECTED_TEXT', None)
    if selection and return_selection:
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
        print "No 'debug_modules' option in 'developer' section of config => output verbosity is DEBUG everywhere."
        calvinlogger.get_logger().setLevel(logging.DEBUG)
    else:
        for m in debug_modules:
            calvinlogger.get_logger(m).setLevel(logging.DEBUG)
    print "\n{0}\n{1}\n{0}".format("-"*80, config)
    run(script, timeout)


def document(what):
    store = DocumentationStore()
    print store.help(what or None, compact=False, formatting='md', links=False)


def visualize(deployment, component):
    source_text, line_offset = get_source(return_selection=True)

    if deployment:
        dot_src, issuetracker = visualize_deployment(source_text)
    else:
        if component:
            dot_src, issuetracker = visualize_component(source_text, component)
        else:
            dot_src, issuetracker = visualize_script(source_text)

    args = ['dot', '-Tsvg']
    try:
        p = subprocess.Popen(args, stdin=subprocess.PIPE)
        p.stdin.write(dot_src.encode('utf-8'))
        p.stdin.close() # signal end of file
    except:
        print 'Visualization requires \'dot\' command from <a href="http://www.graphviz.org">GraphViz</a>'
    issue_report(issuetracker, line_offset, report_success=False)

def _call_dialog(command, *args):
    """ Call the Textmate Dialog process

    command is the command to invoke.
    args are the strings to pass as arguments
    a dict representing the plist returned from DIALOG is returned

    """
    popen_args = [dialog, command]
    popen_args.extend(args)
    result = subprocess.check_output(popen_args)
    return result

def present_popup(suggestions, typed='', extra_word_chars='_', return_choice=False):
    retval = _call_dialog('popup',
                          '--suggestions', suggestions,
                          '--alreadyTyped', typed,
                          '--additionalWordCharacters', extra_word_chars,
                          '--returnChoice' if return_choice else '',
                          )
    return retval if return_choice else ''

def present_menu(menu_items):
    selections = [{'title':item} for item in menu_items]
    retval = _call_dialog('menu', '--items', writePlistToString(selections))
    return readPlistFromString(retval) if retval else {}

def present_tooltip(text, is_html=False):
    _call_dialog('tooltip', '--html' if is_html else '--text', text)

def suggestion_arg_strings(info):
    arg_dicts = info['arg_dicts']
    return ["()"]*len(arg_dicts)

def suggestion_plist_string(info):
    suggestions = info['suggestions']
    args = suggestion_arg_strings(info)
    data = zip(suggestions, args)
    plist = ["{{ display = {}; insert = \"{}\";}}".format(s, a) for s, a in data]
    plist_string = "( " + ", ".join(plist) + " )"
    return plist_string

def complete():
    source, _ = get_source(return_selection=False)
    col = int(os.environ['TM_LINE_INDEX'])
    lineno = int(os.environ['TM_LINE_NUMBER'])
    completion = Completion(first_line_is_zero = False)
    completion.set_source(source)
    d = completion.complete(lineno, col)
    if not d['type'] or not d['suggestions']:
        # exit.discard()
        exit.show_tool_tip("No completions")
    if len(d['suggestions']) == 1:
        exit.insert_snippet("{}$0".format(d['completions'][0]))
    n = len(d['suggestions'][0]) - len(d['completions'][0])
    typed = d['suggestions'][0][:n]
    present_popup(suggestion_plist_string(d), typed=typed)
    # exit.insert_snippet("${{1|{}|}}$0".format(",".join(d['completions'])))



