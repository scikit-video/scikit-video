"""
Media info code comes largely from pymediainfo:

The MIT License

Copyright (c) 2010-2014, Patrick Altman <paltman@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

    http://www.opensource.org/licenses/mit-license.php

"""

import subprocess as sp

from .._utils import *

def mprobe(filename):
    """get metadata by using mediainfo

    """
    # '-f' gets full output, and --Output=XML is xml formatted output
    command = ["mediainfo", "-f", "--Output=XML", filename]

    # simply get std output
    #xml = sp.check_output(command)
    xml = check_output(command)

    d = xmltodictparser(xml)#, process_namespaces=True)

    assert "Mediainfo" in d
    d = d["Mediainfo"]

    assert "File" in d
    d = d["File"]

    assert "track" in d
    unorderedtracks = d["track"]

    # go through each track to determine what they are
    orderedtracks = {}
    for d in unorderedtracks:
        assert "@type" in d
        assert d["@type"] not in orderedtracks 
        orderedtracks[d["@type"]] = d

    # if there is no video here, what's the point?
    assert "Video" in orderedtracks.keys()

    return orderedtracks

#    print json.dumps(orderedtracks, indent=4)
#    exit(0)

    # parse out the fields into a dictionary
