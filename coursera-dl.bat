@echo off
rem Start-up script for Windows systems, ensuring out-of-the-box command execution as for *nix examples.
rem Make sure the containing folder is referenced in %PATH%

rem Usage: see "Running the script" section of the README for sample commands.

rem Run "coursera-dl" in the current folder as working directory (where "%~dp0" is the
rem location of this .bat file) via Python, passing all user-specified arguments ("%*")
python %~dp0\coursera-dl %*
