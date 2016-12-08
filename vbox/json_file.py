"""An interface for reading, writing, and modifying a JSON file"""

import contextlib
import errno
import json
import os

import vbox.error


class Error(vbox.error.Error):

    """Base class for errors in json_file module"""


class JsonFile(object):

    """Reads from and writes to a JSON file using Python data structures"""

    def __init__(self, path, validate=lambda data: None, indent=None):
        """
        *path* is the path to the JSON file

        *validate* is a function that takes the Python representation of the data (a dictionary or
        list) and raises InvalidDataError if that data is invalid

        *indent* is an optional integer indicating the number of spaces to use for indents when
        writing the JSON data to file
        """
        self.path = path
        self._validate = validate
        self._indent = indent

    def read(self, validate=True):
        """
        Reads the JSON data from the file

        Returns a dictionary

        Raises JsonFileNotFoundError if the data file doesn't exist

        If *validate* is True, raises InvalidDataError if the data is invalid
        """
        try:
            with self._open_file() as data_file:
                data = json.load(data_file)
        except IOError:
            raise JsonFileNotFoundError(self.path)
        except ValueError as err:
            raise InvalidDataError(str(err))
        else:
            if validate:
                self._validate(data)
            return data

    @contextlib.contextmanager
    def _open_file(self, *args, **kwargs):
        with open(self.path, *args, **kwargs) as data_file:
            yield data_file

    def write(self, data, validate=True):
        """
        Writes the given *data* dictionary to file as JSON

        If *validate* is True, raises InvalidDataError if the data is invalid
        """
        if validate:
            self._validate(data)

        self._ensure_directory_exists()

        with self._open_file(mode='w') as data_file:
            json.dump(data, data_file, indent=self._indent)

    def _ensure_directory_exists(self):
        directory = os.path.dirname(self.path)
        _mkdirs(directory)

    @contextlib.contextmanager
    def modify(self, validate=True):
        """
        Yields the JSON as a modifiable dictionary and writes the modified dictionary to file after
        the context

        Raises JsonFileNotFoundError if the data file doesn't exist

        If *validate* is True, raises InvalidDataError if the data is invalid
        """
        data = self.read(validate=validate)
        yield data
        self.write(data, validate=validate)


class JsonFileNotFoundError(Error):

    """Data file does not exist"""

    def __init__(self, path):
        super(JsonFileNotFoundError, self).__init__('File {} does not exist'.format(path))


class InvalidDataError(Error):

    """Data format is invalid"""

    def __init__(self, reason):
        super(InvalidDataError, self).__init__('Data is invalid: {}'.format(reason))


def _mkdirs(newdir, *args, **kwargs):
    try:
        os.makedirs(newdir, *args, **kwargs)
    except OSError as err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise
