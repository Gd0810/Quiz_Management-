from django import template

register = template.Library()


@register.filter
def getattribute(obj, attr_name):
    value = getattr(obj, attr_name)
    if callable(value):
        return value()
    return value


@register.filter
def get_item(mapping, key):
    return mapping.get(key)
