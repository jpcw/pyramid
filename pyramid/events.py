import venusian

from zope.interface import implementer

from pyramid.interfaces import IContextFound
from pyramid.interfaces import INewRequest
from pyramid.interfaces import INewResponse
from pyramid.interfaces import IApplicationCreated
from pyramid.interfaces import IBeforeRender

class subscriber(object):
    """ Decorator activated via a :term:`scan` which treats the
    function being decorated as an event subscriber for the set of
    interfaces passed as ``*ifaces`` to the decorator constructor.

    For example:

    .. code-block:: python

       from pyramid.events import NewRequest
       from pyramid.events import subscriber

       @subscriber(NewRequest)
       def mysubscriber(event):
           event.request.foo = 1

    More than one event type can be passed as a construtor argument.  The
    decorated subscriber will be called for each event type.

    .. code-block:: python

       from pyramid.events import NewRequest, NewResponse
       from pyramid.events import subscriber

       @subscriber(NewRequest, NewResponse)
       def mysubscriber(event):
           print event

    When the ``subscriber`` decorator is used without passing an arguments,
    the function it decorates is called for every event sent:

    .. code-block:: python

       from pyramid.events import subscriber

       @subscriber()
       def mysubscriber(event):
           print event

    This method will have no effect until a :term:`scan` is performed
    against the package or module which contains it, ala:

    .. code-block:: python

       from pyramid.config import Configurator
       config = Configurator()
       config.scan('somepackage_containing_subscribers')

    """
    venusian = venusian # for unit testing

    def __init__(self, *ifaces):
        self.ifaces = ifaces

    def register(self, scanner, name, wrapped):
        config = scanner.config
        for iface in self.ifaces:
            config.add_subscriber(wrapped, iface)

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category='pyramid')
        return wrapped

@implementer(INewRequest)
class NewRequest(object):
    """ An instance of this class is emitted as an :term:`event`
    whenever :app:`Pyramid` begins to process a new request.  The
    event instance has an attribute, ``request``, which is a
    :term:`request` object.  This event class implements the
    :class:`pyramid.interfaces.INewRequest` interface."""
    def __init__(self, request):
        self.request = request

@implementer(INewResponse)
class NewResponse(object):
    """ An instance of this class is emitted as an :term:`event`
    whenever any :app:`Pyramid` :term:`view` or :term:`exception
    view` returns a :term:`response`.

    The instance has two attributes:``request``, which is the request
    which caused the response, and ``response``, which is the response
    object returned by a view or renderer.

    If the ``response`` was generated by an :term:`exception view`, the
    request will have an attribute named ``exception``, which is the
    exception object which caused the exception view to be executed.  If the
    response was generated by a 'normal' view, this attribute of the request
    will be ``None``.

    This event will not be generated if a response cannot be created due to
    an exception that is not caught by an exception view (no response is
    created under this circumstace).

    This class implements the
    :class:`pyramid.interfaces.INewResponse` interface.

    .. note::

       Postprocessing a response is usually better handled in a WSGI
       :term:`middleware` component than in subscriber code that is
       called by a :class:`pyramid.interfaces.INewResponse` event.
       The :class:`pyramid.interfaces.INewResponse` event exists
       almost purely for symmetry with the
       :class:`pyramid.interfaces.INewRequest` event.
    """
    def __init__(self, request, response):
        self.request = request
        self.response = response

@implementer(IContextFound)
class ContextFound(object):
    """ An instance of this class is emitted as an :term:`event` after
    the :app:`Pyramid` :term:`router` finds a :term:`context`
    object (after it performs traversal) but before any view code is
    executed.  The instance has an attribute, ``request``, which is
    the request object generated by :app:`Pyramid`.

    Notably, the request object will have an attribute named
    ``context``, which is the context that will be provided to the
    view which will eventually be called, as well as other attributes
    attached by context-finding code.

    This class implements the
    :class:`pyramid.interfaces.IContextFound` interface.

    .. note::

       As of :app:`Pyramid` 1.0, for backwards compatibility purposes, this
       event may also be imported as :class:`pyramid.events.AfterTraversal`.
    """
    def __init__(self, request):
        self.request = request

AfterTraversal = ContextFound # b/c as of 1.0

@implementer(IApplicationCreated)
class ApplicationCreated(object):    
    """ An instance of this class is emitted as an :term:`event` when
    the :meth:`pyramid.config.Configurator.make_wsgi_app` is
    called.  The instance has an attribute, ``app``, which is an
    instance of the :term:`router` that will handle WSGI requests.
    This class implements the
    :class:`pyramid.interfaces.IApplicationCreated` interface.

    .. note::

       For backwards compatibility purposes, this class can also be imported as
       :class:`pyramid.events.WSGIApplicationCreatedEvent`.  This was the name
       of the event class before :app:`Pyramid` 1.0.
    """
    def __init__(self, app):
        self.app = app
        self.object = app

WSGIApplicationCreatedEvent = ApplicationCreated # b/c (as of 1.0)

@implementer(IBeforeRender)
class BeforeRender(dict):
    """
    Subscribers to this event may introspect and modify the set of
    :term:`renderer globals` before they are passed to a :term:`renderer`.
    This event object iself has a dictionary-like interface that can be used
    for this purpose.  For example::

      from pyramid.events import subscriber
      from pyramid.events import BeforeRender

      @subscriber(BeforeRender)
      def add_global(event):
          event['mykey'] = 'foo'

    An object of this type is sent as an event just before a :term:`renderer`
    is invoked (but *after* the -- deprecated -- application-level renderer
    globals factory added via
    :class:`pyramid.config.Configurator.set_renderer_globals_factory`, if
    any, has injected its own keys into the renderer globals dictionary).

    If a subscriber adds a key via ``__setitem__`` that already exists in
    the renderer globals dictionary, it will overwrite the older value there.
    This can be problematic because event subscribers to the BeforeRender
    event do not possess any relative ordering.  For maximum interoperability
    with other third-party subscribers, if you write an event subscriber meant
    to be used as a BeforeRender subscriber, your subscriber code will need to
    ensure no value already exists in the renderer globals dictionary before
    setting an overriding value (which can be done using ``.get`` or
    ``__contains__`` of the event object).

    The event has an additional attribute named ``rendering_val``.  This is
    the (non-system) value returned by a view or passed to ``render*`` as
    ``value``.  This feature is new in Pyramid 1.2.
    
    For a description of the values present in the renderer globals dictionary,
    see :ref:`renderer_system_values`.

    See also :class:`pyramid.interfaces.IBeforeRender`.
    """
    def __init__(self, system, rendering_val=None):
        dict.__init__(self, system)
        self.rendering_val = rendering_val


