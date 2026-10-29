from django import template

from core.seo_ld import build_graph, json_ld_script

register = template.Library()


@register.simple_tag(takes_context=True)
def structured_data(context):
    return json_ld_script(build_graph(context))
