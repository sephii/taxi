from __future__ import unicode_literals

import copy
import datetime

import six

from .flags import FlaggableMixin


@six.python_2_unicode_compatible
class TextLine(object):
    """
    The TextLine is either a blank line or a comment line.
    """
    def __init__(self, text):
        super(TextLine, self).__init__()
        self._text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<TextLine: "%s">' % str(self.text)

    @property
    def text(self):
        """
        Return the text of the TextLine. This property allows subclasses to
        dynamically get or set the text of the line. This is typically used in
        :class:`EntryLine` to generate the text from the entry.
        """
        return self._text

    @text.setter
    def text(self, value):
        self._text = value


class EntryLine(FlaggableMixin, TextLine):
    """
    The EntryLine is a line representing a timesheet entry, with an alias, a
    duration, a description and some potential flags.
    """
    FLAG_IGNORED = 'ignored'
    FLAG_PUSHED = 'pushed'

    def __init__(self, alias, duration, description, flags=None, text=None):
        """
        `flags` must be a :class:`set` of flags (either :attr:`FLAG_IGNORED` or :attr:`FLAG_PUSHED`).

        If `text` is set, it will be used as a base by the parser, with any necessary modification depending on the
        attributes that have been set on the :class:`EntryLine`. `text` must be a tuple in the following form::

            (flags, space1, alias, space2, duration, space3, description)

        Where `space1`, `space2` and `space3` are just spacing characters (this is used to preserve the number of
        whitespaces when regenerating the line). For the values of `flags`, `alias`, `duration` and `description`,
        refer to the :class:`~taxi.timesheet.parser.TimesheetParser` class.

        """
        super(EntryLine, self).__init__(text=text)

        self.alias = alias
        self.duration = duration
        self.description = description
        self.previous_entry = None

        # Flags *must* be changed through the dedicated methods, or we won't notice it and we won't be able to reflect
        # the change when outputting the line as text
        if flags is not None:
            self._flags = copy.copy(flags)

        # This must come last in the initialization as any attribute set after this one will be recorded in
        # `_changed_attrs`
        self._changed_attrs = set()

    def __repr__(self):
        return '<EntryLine: "%s">' % self.__str__()

    def __str__(self):
        return "{alias} {time} {description}".format(alias=self.alias, time=self.hours, description=self.description)

    def __setattr__(self, attr, value):
        """
        Set the given `attr` to the given `value` and memorize this attribute
        has changed so we can regenerate it when outputting text.
        """
        if hasattr(self, '_changed_attrs') and attr != '_changed_attrs':
            self._changed_attrs.add(attr)

        super(EntryLine, self).__setattr__(attr, value)

    @property
    def hours(self):
        """
        Return the number of hours this entry has lasted. If the duration is a tuple with a start and an end time,
        the difference between the two times will be calculated. If the duration is a number, it will be returned
        as-is.
        """
        if not isinstance(self.duration, tuple):
            return self.duration

        if self.duration[1] is None:
            return 0

        time_start = self.get_start_time()

        # This can happen if the previous entry has a non-tuple duration
        # and the current entry has a tuple duration without a start time
        if time_start is None:
            return 0

        now = datetime.datetime.now()
        time_start = now.replace(
            hour=time_start.hour,
            minute=time_start.minute, second=0
        )
        time_end = now.replace(
            hour=self.duration[1].hour,
            minute=self.duration[1].minute, second=0
        )
        total_time = time_end - time_start
        total_hours = total_time.seconds / 3600.0

        return total_hours

    def get_start_time(self):
        """
        Return the start time of the entry as a :class:`datetime.time` object.
        If the start time is `None`, the end time of the previous entry will be
        returned instead. If the current entry doesn't have a duration in the
        form of a tuple, if there's no previous entry or if the previous entry
        has no end time, the value `None` will be returned.
        """
        if not isinstance(self.duration, tuple):
            return None

        if self.duration[0] is not None:
            return self.duration[0]
        else:
            if (self.previous_entry and
                    isinstance(self.previous_entry.duration, tuple) and
                    self.previous_entry.duration[1] is not None):
                return self.previous_entry.duration[1]

        return None

    @property
    def hash(self):
        """
        Return a value that's used to uniquely identify an entry in a date so we can regroup all entries that share the
        same hash.
        """
        return u''.join([
            self.alias,
            self.description,
            str(self.ignored),
            str(self.flags),
        ])

    def add_flag(self, flag):
        """
        Add flag to the flags and memorize this attribute has changed so we can
        regenerate it when outputting text.
        """
        super(EntryLine, self).add_flag(flag)
        self._changed_attrs.add('flags')

    def remove_flag(self, flag):
        """
        Remove flag to the flags and memorize this attribute has changed so we
        can regenerate it when outputting text.
        """
        super(EntryLine, self).remove_flag(flag)
        self._changed_attrs.add('flags')

    @property
    def flags(self):
        """
        Return a copy of the flags. The reason why we return a copy and not the
        original flags is that we don't want it to be altered because we need
        to keep the synchronisation with the text lines. To change a flag, use
        :meth:`add_flag` or :meth:`remove_flag` or use shortcut properties such
        as :attr:`ignored` or :attr:`pushed`.
        """
        return copy.copy(self._flags)

    @property
    def pushed(self):
        """
        Return True if the object has the :attr:`FLAG_PUSHED` flag set.
        """
        return self.has_flag(self.FLAG_PUSHED)

    @pushed.setter
    def pushed(self, value):
        """
        Set the ignored flag if the `value` it is set to evaluates to True,
        remove it otherwise.
        """
        self._add_or_remove_flag(self.FLAG_PUSHED, value)

    @property
    def ignored(self):
        """
        Return True if this entry is supposed to be ignored, False otherwise. A
        line can be ignored for several reasons:

            * It has the ignored flag set
            * Its duration is zero
            * Its description is `?`
            * Its alias ends with a `?`
        """
        return (
            self.has_flag(self.FLAG_IGNORED) or self.hours == 0 or
            self.description == '?' or self.alias[-1] == '?'
        )

    @ignored.setter
    def ignored(self, value):
        """
        Set the ignored flag if the `value` it is set to evaluates to True,
        remove it otherwise.
        """
        self._add_or_remove_flag(self.FLAG_IGNORED, value)


class DateLine(TextLine):
    """
    Represents a date in a timesheet.
    """
    def __init__(self, date, text=None):
        super(DateLine, self).__init__(text=text)

        self.date = date

        if text is not None:
            self.text = text

    def __repr__(self):
        return '<DateLine: "%s">' % (self.text if self.text else self.date)
