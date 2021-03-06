
from django import template

register = template.Library()

@register.filter(name='private')
def private(obj, attribute):
    return getattr(obj, attribute)

@register.filter
def get_range( value ):
    return range(1, value+1)

@register.filter
def split(string, sep):
    """Return the last string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)[1]


@register.filter
def joinby(value, arg):
    return arg.join(value)


@register.filter
def get_type(value):
    return value.__class__.__name__


@register.filter
def intiger(value):
    return int(value)


'''@register.filter
def float(value):
    return int(float)'''


@register.filter
def get_key(obj, key):
    return obj[key][0]

@register.filter(name='get')
def get(d, k):
    return d.get(k, None)

'''date=output['meta']['date'].split('T')[0]
output['meta']['date'] = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%y')'''


@register.filter
def replaceid(string):
    """Return the last string split by sep.

    Example usage: {{ value|replace }}
    """
    new = string.replace(" ", "_")
    return new.replace (".", "-")

@register.filter
def replace(string):
    """Return the last string split by sep.

    Example usage: {{ value|replace }}
    """
    return string.replace(" ", "_")


@register.filter
def sub(string):
    """Return the last string split by sep.

    Example usage: {{ value|sub }}
    """
    return string-1

@register.filter
def id(obj):
    """Return id.

    Example usage: {{ value|id }}
    """
    return obj['_id']

'''@register.filter(name='times')
def times(number):
    max=0
    for attribute, value in number.iteritems():
        print attribute, value # example usage
        length= len(value)
        if length>max:
            max=length
    return range(0,max)'''

@register.filter(name='times')
def times(number):
    return range(0,5)

'''@register.filter
def add(string):
    return string+1'''

@register.filter
def getlevel(d,k):
    return d[k]

@register.filter
def getvalue(d,k):
    n=0
    for value in d:
        if int(k) == n:
            return value
        n=n+1

@register.filter
def splitname(d):
    # print d
    # if "_" in d:
    #     print "for split:" + d
        return d.split('_')[1]
    # return d.split('_')[1]
