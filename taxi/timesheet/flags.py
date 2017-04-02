class FlaggableMixin(object):
    """
    A `FlaggableMixin` instance has a :class:`set` of flags that should be
    changed with the :meth:`add_flag` and :meth:`remove_flag` methods::

        >>> my_flaggable_object.add_flag('ignored')
        >>> my_flaggable_object.has_flag('ignored')
        True
    """

    def __init__(self, *args, **kwargs):
        self._flags = set()
        super(FlaggableMixin, self).__init__(*args, **kwargs)

    def add_flag(self, flag):
        """
        Add the given `flag` to the set of flags.
        """
        self._flags.add(flag)

    def remove_flag(self, flag):
        """
        Remove the given `flag` from the set of flags.
        """
        self._flags.remove(flag)

    def has_flag(self, flag):
        """
        Return True if the given `flag` is set, False otherwise.
        """
        return flag in self._flags

    def _add_or_remove_flag(self, flag, add):
        """
        Add the given `flag` if `add` is True, remove it otherwise.
        """
        meth = self.add_flag if add else self.remove_flag
        meth(flag)
