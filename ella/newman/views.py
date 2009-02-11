import logging

from django import template, forms
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Template
from django.contrib.admin.views.main import ChangeList, ERROR_FLAG
from ella.newman.changelist import NewmanChangeList, FilterChangeList
from django.contrib.admin.options import IncorrectLookupParameters
from django.shortcuts import render_to_response

from ella.newman.options import NewmanModelAdmin


log = logging.getLogger('ella.newman.views')


def filters_view(model_admin, request, extra_context=None):
    "stolen from: The 'change list' admin view for this model."
    opts = model_admin.model._meta
    app_label = opts.app_label
    try:
        cl = FilterChangeList(request, model_admin.model, model_admin.list_display, model_admin.list_display_links, model_admin.list_filter,
            model_admin.date_hierarchy, model_admin.search_fields, model_admin.list_select_related, model_admin.list_per_page, model_admin)
    except IncorrectLookupParameters:
        # Wacky lookup parameters were given, so redirect to the main
        # changelist page, without parameters, and pass an 'invalid=1'
        # parameter via the query string. If wacky parameters were given and
        # the 'invalid=1' parameter was already in the query string, something
        # is screwed up with the database, so display an error page.
        if ERROR_FLAG in request.GET.keys():
            return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
        return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

    context = {
        'title': cl.title,
        'is_popup': cl.is_popup,
        'cl': cl,
        'has_add_permission': model_admin.has_add_permission(request),
        'root_path': model_admin.admin_site.root_path,
        'app_label': app_label,
}
    context.update(extra_context or {})
    out= render_to_response(
        'admin/filters.html',
        context,
        context_instance=template.RequestContext(request)
)
    return HttpResponse(out, mimetype='text/plain;charset=utf-8')


def changelist_view(self, request, extra_context=None):
    opts = self.model._meta
    app_label = opts.app_label
    if not self.has_change_permission(request, None):
        raise PermissionDenied
    try:
        cl = NewmanChangeList(request, self.model, self.list_display, self.list_display_links, self.list_filter,
            self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page, self)
    except IncorrectLookupParameters:
        # Wacky lookup parameters were given, so redirect to the main
        # changelist page, without parameters, and pass an 'invalid=1'
        # parameter via the query string. If wacky parameters were given and
        # the 'invalid=1' parameter was already in the query string, something
        # is screwed up with the database, so display an error page.
        if ERROR_FLAG in request.GET.keys():
            return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
        return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

    context = {
        'title': cl.title,
        'is_popup': cl.is_popup,
        'cl': cl,
        'has_add_permission': self.has_add_permission(request),
        'root_path': self.admin_site.root_path,
        'app_label': app_label,
}
    context.update(extra_context or {})
    return render_to_response(self.change_list_template or [
        'admin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
        'admin/%s/change_list.html' % app_label,
        'admin/change_list.html'
    ], context, context_instance=template.RequestContext(request))

NewmanModelAdmin.register(lambda x: x is None, changelist_view)
NewmanModelAdmin.register(lambda x: x.endswith('filters'), filters_view)
