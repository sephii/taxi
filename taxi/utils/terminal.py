import re


def select_number(max, description, min=0):
    while True:
        char = input('\n%s' % description)
        try:
            number = int(char)
            if min <= number <= max:
                return number
            else:
                print('Number out of range, try again')
        except ValueError:
            print('Please enter a number')


def select_string(description, format=None, regexp_flags=0, default=None):
    while True:
        char = input(description)
        if char == '' and default is not None:
            return default

        if format is not None:
            if re.match(format, char, regexp_flags):
                return char
            else:
                print('Invalid input, please try again')
        else:
            return char
