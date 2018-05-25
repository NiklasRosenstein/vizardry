# -*- coding: utf8 -*-
# Copyright (c) 2018 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

__all__ = ['InlineNodeData']

from .. import event
from ..base import BaseSceneNodeData
from ..parameters import Text
import traceback


class InlineNodeData(BaseSceneNodeData):

  def init(self, node):
    self.__scope = None
    self.__gl_init = None
    self.__gl_render = None
    self.__gl_cleanup = None
    self.__gl_init_complete = False
    self.__gl_cleanup_deferred = None
    node.parameters.add(Text('code', 'Python Code', multiline=True, syntax='python'))
    node.parameters['code'].bind(event.VALUE_CHANGED, self.__update)

  def __update(self, _=None):
    # Save the cleanup step for deferred execution since we're going
    # to replace the callbacks.
    if self.__gl_cleanup and self.__gl_init_complete:
      self.__gl_cleanup_deferred = self.__gl_cleanup

    node = self.node
    try:
      code = node.parameters['code'].get_value()
      code = compile(code, 'vizardry:' + node.path, 'exec')
      scope = {'node': node}
      exec(code, scope)
      self.__scope = scope
      self.__gl_init = scope.get('gl_init')
      self.__gl_render = scope.get('gl_render')
      self.__gl_cleanup = scope.get('gl_cleanup')
      self.__gl_init_complete = False
    except:
      traceback.print_exc()
    # TODO: Mark this node as requiring re-execution/re-render.

  def gl_render(self, node):
    if self.__scope is None:
      self.__update()

    # Deferred cleanup if the callbacks have already been replaced.
    if self.__gl_cleanup_deferred:
      try:
        self.__gl_cleanup_deferred()
      except:
        traceback.print_exc()
      self.__gl_cleanup_deferred = None

    if not self.__gl_init_complete:
      self.__gl_init()
      self.__gl_init_complete = True

    if self.__gl_render:
      self.__gl_render()

  def gl_cleanup(self, node):
    if self.__gl_init_complete and self.__gl_cleanup:
      self.__gl_cleanup()
      self.__gl_cleanup = None