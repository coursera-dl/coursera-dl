@echo off
rem Start-up script for Windows systems, ensuring out-of-the-box command execution as for *nix examples.
rem Make sure the containing folder is referenced in %PATH%

rem Usage: see "Running the script" section of the README for sample commands.

rem Run "coursera-dl" in the current folder as working directory (where "%~dp0" is the
rem location of this .bat file) via Python, passing all user-specified arguments ("%*")

rem This command does not work on Windows paths with spaces
rem python %~dp0\coursera-dl %*

rem Changed to this command. That does work with spaces in path. YAY! (Victor Westmann 2015-11-09 1:01 AM)
python coursera-dl %*
