from django import template
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import strip_spaces_between_tags
from django.contrib.contenttypes.models import ContentType
from datetime import datetime


register = template.Library()


@register.simple_tag(takes_context=True)
def paginate(context, objects, num=10):
    request = context.get('request')

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    paginator = Paginator(objects, num)

    try:
        objects = paginator.page(page)
    except EmptyPage:
        # If the page is out of range (e.g., 9999), deliver the last page of results
        objects = paginator.page(paginator.num_pages)
    return objects


@register.filter()
def fromtimestamp(timestamp):
    # Convert timestamp to datetime
    return datetime.utcfromtimestamp(timestamp)


class SmartSpacelessNode(template.Node):

    """ Удалить пробелы из шаблона если отключен режим отладки """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context)
        return strip_spaces_between_tags(content.strip())


@register.tag
def smart_spaceless(parser, token):

    nodelist = parser.parse(('end_smart_spaceless',))
    parser.delete_first_token()
    return SmartSpacelessNode(nodelist)


@register.simple_tag
def get_items_by_model_name(model_name, ordering=None, num=None, **kwargs):
    """
    return queryset of every items by model name with filtering
    example:
        {% get_items_by_model_name 'door' ordering='-id' num=20 show=True price__gt=6000 as doors %}
    """
    items = ContentType.objects.filter(model=model_name).first().get_all_objects_for_this_type().filter(**kwargs)
    if ordering:
        items = items.order_by(ordering)
    if num:
        items = items[:num]
    return items