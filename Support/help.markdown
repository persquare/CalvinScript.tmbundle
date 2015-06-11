# Introduction

The CalvinScript bundle provides a few tools for working with CalvinScript in TextMate 2.

# Configuration

A few variables need to be set globally or locally for the bundle to work properly:

In `.tm_properties` in your project directory (which you can bring by choosing "Settings…" from the CalvinScript bundle menu):

    projectDirectory="$CWD"

In TextMate's variables, or a `.tm_properties` file somewhere on TextMates path from your $HOME directory:

    TM_CALVIN_DEPLOYER=/path/to/deploy_app.py
    TM_CALVIN_COMPILER=/path/to/compiler.py
    TM_CALVIN_DIR=/path/to/pycalvin/

`CALVIN_ACTORPATH` is a colon-separated list of directories (just like `PATH`) where calvin will look for actors.  
You should set `CALVIN_ACTORPATH` in your general environment, in TextMate's variables, or in a `.tm_properties` file or calvin won't be able to locate any actors, and TextMate won't be able to provide help for actors.  
It is a good idea to place `systemactors` first in the list unless you like surprises. 
  
    CALVIN_ACTORPATH=/path/to/pycalvin/systemactors:/path/to/pycalvin/devactors:/path/to/pycalvin/my_actors


