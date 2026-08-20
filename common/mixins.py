from django.http import Http404, HttpResponse


class TenantQuerysetMixin:
    def get_school(self):
        school = self.request.user.school
        if school is None:
            raise Http404
        return school

    def get_queryset(self):
        return super().get_queryset().for_school(self.get_school())


class TenantFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['school'] = self.get_school()
        return kwargs


class TenantCreateMixin(TenantQuerysetMixin):
    def form_valid(self, form):
        form.instance.school = self.get_school()
        return super().form_valid(form)


class HtmxTemplateMixin:
    htmx_template_name = None

    def get_template_names(self):
        if getattr(self.request, 'htmx', False) and self.htmx_template_name:
            return [self.htmx_template_name]
        return super().get_template_names()


class HtmxModalFormMixin:
    trigger_event = 'refresh-list'

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self.request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': self.trigger_event})
        return response


class HtmxDeleteMixin:
    trigger_event = 'refresh-list'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if getattr(self.request, 'htmx', False):
            return HttpResponse(status=204, headers={'HX-Trigger': self.trigger_event})
        return HttpResponse(status=204)
