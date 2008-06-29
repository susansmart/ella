from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from ella.core.cache import CachedForeignKey
from ella.core.models import Category
from ella.core.cache import get_cached_list, get_cached_object, cache_this
from ella.menu.managers import MenuItemManager
from ella.db.models import Publishable


class Menu(models.Model):
    slug = models.SlugField(_('Slug'), max_length=255)
    site = models.ForeignKey(Site)
    category = models.ForeignKey(Category, null=True, blank=True)

    def __unicode__(self):
        return unicode('%s for category %s on %s' % (self.slug, self.category, self.site))

class MenuItem(models.Model):
    parent = CachedForeignKey('self', blank=True, null=True, verbose_name=_('parent'))
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_ct = models.ForeignKey(ContentType, null=True, blank=True)
    target = generic.GenericForeignKey(ct_field="target_ct", fk_field="target_id")
    url = models.URLField(blank=True)
    label = models.CharField(max_length=100, blank=True)
    menu = models.ForeignKey(Menu)
    order = models.IntegerField(default=1)

    objects = MenuItemManager()

    def __unicode__(self):
        if self.label:
            return self.label
        return unicode(self.target)

    @property
    def subitems(self):
        #return get_cached_list(MenuItem, parent=self.pk)
        return MenuItem.objects.filter(parent=self.pk).order_by('order')

    @property
    def get_url(self):
        if self.url:
            return self.url
        elif isinstance(self.target, Publishable):
            return self.target.get_absolute_url()

    class Meta:
        verbose_name = _('Menu item')
        verbose_name_plural = _('Menu items')


# initialization
from ella.menu import register
del register