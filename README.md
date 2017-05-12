# CalvinScript.tmbundle
A [CalvinScript][1] bundle for TextMate2

## Introduction

The CalvinScript bundle provides a few tools for working with CalvinScript in TextMate 2, most notably:

- Syntax highlighting
- Syntax checking (via Calvin's tools)
- Documentation for actors (via Calvin's tools)
- Running CalvinScripts inside TextMate, or in a terminal
- Rendering a graph representation of a script

Select `Help` from the CalvinScript submenu in TextMate's Bundles menu for an a full list of commands and documentation.

## Installation
Clone the repository and move the CalvinScript bundle to `~/Library/Application\ Support/TextMate/Bundles/`, or
create a symlink from TextMate's bundle directory to the cloned repository:

    cd ~/Library/Application\ Support/TextMate/Bundles/
    ln -s path/to/CalvinScript.tmbundle .

## Configuration

If you have installed [Calvin][1] on your system using the `setup.py` provided, everything should work out of the box.

If you are running Calvin in a virtualenv, you will need to provide the location of the virtualenv, either in TextMate's preferences or, preferably, in a `.tm_properties` file in the root directory of your project(s):

    TM_VIRTUALENV=$HOME/.virtenvs/calvin-base

Change the path to wherever you keep your virtual environments.

If you have checked out and plan to make changes, use `pip install -e .` in the Calvin's top directory. This is regardless of wether you use a virtualenv or not, but in the latter case you might need to set `TM_CALVINDIR` to point to Calvin's top directory unless you have added Calvin to `PYTHONPATH`.   

At this time, using this bundle with virtualenv is experimental, YMMV.

[1]: https://github.com/EricssonResearch/calvin-base
