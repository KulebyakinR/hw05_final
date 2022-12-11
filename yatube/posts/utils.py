from django.conf import settings
from django.core.paginator import Paginator


def get_page_context(object_list, request):
    return Paginator(object_list, settings.PAGE_COUNT).get_page(
        request.GET.get('page')
    )
