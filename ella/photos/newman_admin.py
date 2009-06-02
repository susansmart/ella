from django.utils.translation import ugettext_lazy as _

from ella import newman

from ella.photos.models import FormatedPhoto, Format, Photo
from django.conf.urls.defaults import patterns, url
from ella.newman.utils import JsonResponse, JsonResponseError
from ella.newman.config import STATUS_OBJECT_NOT_FOUND

class FormatAdmin(newman.NewmanModelAdmin):
    list_display = ('name', 'max_width', 'max_height', 'stretch', 'resample_quality',)
    list_filter = ('sites', 'stretch', 'nocrop', 'flexible_height',)
    search_fields = ('name',)

class FormatedPhotoInlineAdmin(newman.NewmanTabularInline):
    model = FormatedPhoto

class PhotoAdmin(newman.NewmanModelAdmin):
    inlines = []
    list_display = ('title', 'size', 'thumb', 'pk',)
    list_filter = ('created',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'image', 'description', 'id',)
    suggest_fields = {'authors': ('name', 'slug',), 'source': ('name', 'url',)}

    def size(self, obj):
        return "%dx%d px" % (obj.width, obj.height)
    size.short_description = _('Size')

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(.+)/thumb/$',
                self.json_photo_info,
                name='photo-json-info'),
        )
        urlpatterns += super(PhotoAdmin, self).get_urls()
        return urlpatterns

    def json_photo_info(self, request, object_id, extra_context=None):
        obj = self.get_change_view_object(object_id)

        if obj is None:
            return JsonResponseError(_('Photo id %s does not exists.') % object_id, status=STATUS_OBJECT_NOT_FOUND)

        out = {
            'title': obj.title,
            'thumb_url': obj.thumb_url()
        }

        return JsonResponse('', out)


class FormatedPhotoAdmin(newman.NewmanModelAdmin):
    list_display = ('image', 'format', 'width', 'height')
    list_filter = ('format',)
    search_fields = ('image',)
    raw_id_fields = ('photo',)


newman.site.register(Format, FormatAdmin)
newman.site.register(Photo, PhotoAdmin)
newman.site.register(FormatedPhoto, FormatedPhotoAdmin)

