__author__ = 'dirk'

def format_date(pattern, time_value):
    import time
    if type(time_value).__name__ == 'float':
        time_value = time.localtime(time_value)
    elif type(time_value).__name__ == 'struct_time':
        pass
    else:
        raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
    return time.strftime(pattern, time_value)


def parse_duration(duration_string):
    import re
#   pattern = r"^((?P<h>\d+h)(?iP<m>\d+m)?(?iP<s>\d+s)?|?P<ps>\d+)$"
    pattern = r"((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s?)?"
    matches = re.match(pattern, duration_string)
    (h, m, s) = (matches.group('h'), matches.group('m'), matches.group('s'))
    duration = (int(h) * 3600 if h is not None else 0) +\
               (int(m) * 60 if m is not None else 0) +\
               (int(s) if s is not None else 0)
    return duration


# Taken from http://stackoverflow.com/questions/120951/how-can-i-normalize-a-url-in-python
def url_fix(s, charset='utf-8'):
    """Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.  This
    function can fix some of the problems in a similar way browsers
    handle data entered by the user:

    :param charset: The target charset for the URL if the url was
                    given as unicode string.
    """
    import urlparse, urllib

    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')

    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))