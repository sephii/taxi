import re


def select_number(max, description, min=0):
    while True:
        char = raw_input('\n%s' % description)
        try:
            number = int(char)
            if min <= number <= max:
                return number
            else:
                print(u'Number out of range, try again')
        except ValueError:
            print(u'Please enter a number')


def select_string(description, format=None, regexp_flags=0, default=None):
    while True:
        char = raw_input(description)
        if char == '' and default is not None:
            return default

        if format is not None:
            if re.match(format, char, regexp_flags):
                return char
            else:
                print(u'Invalid input, please try again')
        else:
            return char
