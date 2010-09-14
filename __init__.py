#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
# Copyright © 2010 Andrew D. Yates
# All Rights Reserved.
"""HTTP POST multipart/form-data request encoder for browser style file uploads.

References:
  http://en.wikipedia.org/wiki/MIME#Form_Data
  http://www.ietf.org/rfc/rfc2388.txt
  http://code.activestate.com/recipes/146306/
"""
__authors__ = ['"Andrew D. Yates", <andrew.yates@hhmds.com>']


import base64
import mimetypes
import os
import urllib


class Multipart(object):
  """An HTTP POST multipart/form-data request encoder.

  Attributes:
    body: str of encoded HTTP contents for this request
    content_type: str of MIME HTTP header for this object
    length: str of number of bytes in body

  Example:
    Add a browser-style file upload.
      >>> upload = Multipart()
      ... upload.add("b", "BINARY STRING", "filename.pdf")

    Add a standard HTTP POST key and value variable.
      >>> upload.add("a", "hello")

    Use the populated Multipart upload instance to build HTTP fetch
    request parameters like for google.appengine.api.urlfetch.fetch().

      >>> request = {
      ...   'payload': upload.body,
      ...   'headers': {
      ...     'Content-Type': upload.content_type,
      ...     'Content-Length': upload.length,
      ...     },
      ...   'method': 'POST',
      ...   }
  """
  
  def __init__(self):
    """Initialize HTTPMulipart to new request.

    Args:
      fields = list of Field instances or None
    """
    # prepend 5 dashes to boundary to satisfy legacy ASP web servers
    self._boundary = "-----%s" % base64.urlsafe_b64encode(os.urandom(33))
    self.content_type = "multipart/form-data; boundary=%s" % self._boundary
    self._fields = []
    self._body = None
    self._update_body = True

  @property
  def body(self):
    # Refresh body cache; return body cache
    if not self._body or self._update_body:
      self._body = self.get_body()
      self._update_body = False
    return self._body

  @property
  def length(self):
    return str(len(self.body))

  def add(self, name, value, filename=None, content_type=None):
    """Add a variable or file to this request.

    Args: 
      name: str of HTTP POST name, default is `filename`  
      value: str of binary data of file contents
      filename: str of operating system provided name or None if not a file
      content_type: str of user-defined MIME file type if a file or None
    """
    self._update_body = True
    field = _Field(name, value, filename, content_type)
    self._fields.append(field)

  def get_body(self):
    """Return body content for the current state of HTTP mulitpart object.

    Returns:
      str of encoded multipart form-data for this request object
    """
    var_lines = []
    file_lines = []

    for field in self._fields:
      if field.filename:
        # Add as a file
        file_lines.extend([
            "--%s" % self._boundary,
            'Content-Disposition: form-data; name="%s"; filename="%s"' % \
              (field.name, field.filename),
            "Content-Type: %s" % field.content_type,
            "",
            field.value,
            ])
      else:
        # Add as a variable
        var_lines.extend([
            "--%s" % self._boundary,
            'Content-Disposition: form-data; name="%s"' % field.name,
            "",
            field.value,
            ])

    lines = []
    lines.extend(var_lines)
    lines.extend(file_lines)
    lines.extend([
        '--%s--' % self._boundary,
        '',
        ])
    body = '\r\n'.join(lines)
    return body


class _Field(object):
  """An HTTP POST variable; represents a "file" if filename is set.

  Attributes:
    content_type: str of MIME type for `filename` or None
    filename: str of operating system style file name for file uploads or None
    name: str of HTTP POST name, default is `filename`  
    value: str of value content
  """
  
  def __init__(self, name, value, filename=None, content_type=None):
    """Initialize Field.

    See Field Attributes for argument descriptions

    Args:
      name: str
      value: str
      filename: str
      content_type: str
    """
    self.name = urllib.quote(name)
    self.value = value
    
    if filename:
      self.filename = urllib.quote(filename)
    else:
      self.filename = None

    if not content_type and filename:
      self.content_type = mimetypes.guess_type(filename)[0] or \
        "application/octet-stream"
    elif content_type and filename:
      self.content_type = content_type
    else:
      self.content_type = None
      
