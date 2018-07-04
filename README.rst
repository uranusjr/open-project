====================================================
Simple script to wrap ``subl`` for project discovery
====================================================

I grew tired typing ``subl --project path_to_project``.

This automatically parse the passed argument (only one), aod do the following:

* If it is a directory…
    * Find a project in it, and open it instead of the directory.
    * Find a project in its *parent*, and open it instead of the directory.
    * If a project is not found, open the directory.
* Otherwise, open it as a file.

``subl`` is found automatically via ``mdfind`` if it is not in PATH.
