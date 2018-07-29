==========================================================
Wrap ``subl`` and ``code`` for project/workspace discovery
==========================================================

I grew tired typing ``subl --project path_to_project`` and
``code path_to_my.code-workspace``.

This automatically parse the passed argument (only one), aod do the following:

* If it is a directory…
    * Find a project in it, and open it instead of the directory.
    * Find a project in its *parent*, and open it instead of the directory.
    * If a project is not found, open the directory.
* Otherwise, open it as a file.

``subl`` is found via ``mdfind``, and ``code`` via registry if they are not in
PATH.
