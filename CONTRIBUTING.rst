
Contributing code
=================

How to contribute
-----------------

The preferred way to contribute to scikit-video is to fork the
`main repository <https://github.com/scikit-video/scikit-video>`_ on
GitHub:

1. Fork the `project repository
   <https://github.com/scikit-video/scikit-video>`_:
   click on the 'Fork' button near the top of the page. This creates
   a copy of the code under your account on the GitHub server.

2. Clone this copy to your local disk::

          $ git clone git@github.com:YourLogin/scikit-video.git
          $ cd scikit-video

3. Create a branch to hold your changes::

          $ git checkout -b my-feature

   and start making changes. Never work in the ``master`` branch!

4. Work on this copy on your computer using Git to do the version
   control. When you're done editing, do::

          $ git add modified_files
          $ git commit

   to record your changes in Git, then push them to GitHub with::

          $ git push -u origin my-feature

Finally, go to the web page of your fork of the scikit-video repo,
and click 'Pull request' to send your changes to the maintainers for
review.

(If any of the above seems like magic to you, then look up the
`Git documentation <https://git-scm.com/documentation>`_ on the web.)

It is recommended to check that your contribution complies with the
following rules before submitting a pull request:

-  All public methods should have informative docstrings with sample
   usage presented as doctests when appropriate.

-  The test suite passes. Install in editable mode with the test
   extra and run pytest (FFmpeg must be on the PATH for the io
   tests)::

          $ pip install -e ".[test]"
          $ pytest -v skvideo/tests

   New functionality should come with tests; bug fixes should come
   with a regression test that fails before the fix.

-  When adding additional functionality, consider adding an example to
   the documentation (``doc/examples/``). Examples should demonstrate
   why the new functionality is useful in practice and, if possible,
   compare it to other methods available in scikit-video.

Review cadence: the project is maintained on a part-time basis, with a
focus on bug fixes and compatibility. Expect responses on the scale of
weeks, not days.

Documentation
-------------

We are glad to accept any sort of documentation: function docstrings,
reStructuredText documents (like this one), tutorials, etc.
reStructuredText documents live in the source code repository under the
``doc/`` directory.

You can edit the documentation using any text editor and then generate
the HTML output by typing ``make html`` from the ``doc/`` directory
(requires ``pip install -e ".[docs]"``). The resulting HTML files will
be placed in ``doc/_build/html/`` and are viewable in a web browser.

When you are writing documentation, it is important to keep a good
compromise between mathematical and algorithmic details, and give
intuition to the reader on what the algorithm does. It is best to always
start with a small paragraph with a hand-waving explanation of what the
method does to the data and a figure (coming from an example)
illustrating it.
