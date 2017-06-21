def line_in(line, content):
    def remove_spaces(text):
        chars_to_strip = [' ', '\t']

        for char in chars_to_strip:
            text = text.replace(char, '')

        return text

    return remove_spaces(line) in remove_spaces(content)
