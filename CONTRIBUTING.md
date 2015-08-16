Please, before sending patches, read these brief comments. They are here to
help the project have both its users happy using the program and the
developers/maintainers feel good when trying to change code that other
people contributed.

For the record, when this document mentions "I", it mostly means Rogério
Brito's (@rbrito) is the one to blame.

# Write good commit messages

When you write your pull request and your commit messages, please, be
detailed, explaining why you are doing what you are doing. Don't be afraid
of being too verbose here.  Also, please follow the highly recommended
guidelines on how to write good [good commit messages][commit-msgs].

When in doubt, follow the model of the Linux kernel commit logs. Their
commit messages are some of the best that I have seen. Also, the ffmpeg has
some good messages that I believe that should be followed. If you are in a
hurry, read the section named
["Contributing" from subsurface's README][contributing].

[commit-msgs]: https://robots.thoughtbot.com/5-useful-tips-for-a-better-commit-message
[contributing]: https://github.com/torvalds/subsurface/blob/master/README#L71-L114


# Test that your changes don't break existing functionality

Make sure that you have all dependencies installed, like via:

    pip install -r requirements.txt
    pip install -r requirements-dev.txt

Run the test suite with

    py.test coursera/test -v --cov coursera --cov-report html

If some test fails, please don't send your changes yet. Fix what broke
before sending your pull request.

If you need to change the test suite, explain in the commit message why it
needs to be changed (e.g., the page layout or the authentication methods
from coursera changed, or they implemented a new kind of course).

# Check for potential bugs

Please, help keep the code tidy by checking for any potential bugs with the
help of [`flake8`][flake8], and [`pylint`][pylint].  If you know of any
other good tools for analyzing the code, let me know about them!

[flake8]: https://pypi.python.org/pypi/flake8
[pylint]: https://pypi.python.org/pypi/pylint

If you happen to find any issue reported by these programs, I welcome you to
fix them.  Many of the issues are usually very easy to fix and they are a
great way to start contributing to this (and other projects in general).
Furthermore, we all benefit from a better code base.

# Changes in the tools that we use

If you are proposing the use of a substitute of a tool that we already use,
take a few paragraphs to tell us why we would like to change.

If we are not using something, it is most likely that one of the following
options applies:

1. I (@rbrito) may know even know that what you are proposing exists or have
   not yet "seen the light" as to why I should use it instead of using what
   I am currently using.
2. Even if I know about the tool, I may not know how to use it, or how it
   would make me more productive.  Educate me and we all will gain from a
   better project.
