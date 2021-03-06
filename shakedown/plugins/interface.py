import abc

class PluginInterface(object):
    """
    This class represents the base interface needed from plugin classes.
    """
    __metaclass__ = abc.ABCMeta


    def configure_argument_parser(self, parser):
        """
        Gives a chance to the plugin to add options received from comand-line
        """
        pass

    def configure_from_parsed_args(self, args):
        """
        Called after successful parsing of command-line arguments
        """
        pass

    def get_description(self):
        """
        Retrieves a quick description for this plugin, mostly used in command-line help or online documentation.
        It is not mandatory to override this method.
        """
        return None

    def get_name(self):
        """
        Returns the name of the plugin class. This name is used to register, disable and address
        the plugin during runtime.

        Note that the command-line switches (``--with-...``) are derived from this name.

        Any implemented plugin must override this method.
        """
        raise NotImplementedError() # pragma: no cover
