import codecs

class BasicIo(object):
    def read(self):
        raise NotImplementedError()

    def write(self, lines):
        raise NotImplementedError()

class PlainFileIo(BasicIo):
    def __init__(self, path):
        self.file_path = path

    def read(self):
        with codecs.open(self.file_path, 'r', 'utf-8') as f:
            lines = f.readlines()

        return lines

    def write(self, lines):
        with codecs.open(self.file_path, 'w', 'utf-8') as f:
            for line in lines:
                f.write('%s\n' % line)

class StreamIo(BasicIo):
    def __init__(self, text):
        self.lines = text.split('\n')

    def read(self):
        return self.lines

    def write(self, path):
        return self.lines
