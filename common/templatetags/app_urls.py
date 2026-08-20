from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active_nav(context, url_name):
    request = context.get('request')
    if request is None:
        return 'menu-item'
    try:
        target = reverse(url_name)
    except NoReverseMatch:
        return 'menu-item'
    if request.path.startswith(target):
        return 'menu-item active'
    return 'menu-item'
