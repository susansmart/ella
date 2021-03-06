from datetime import datetime

from django.db import models, connection
from django.db.models import F, Q
from django.conf import settings

from ella.core.models import Listing, Publishable, Category

def cmp_listing_or_meta(x, y):
    from ella.exports.models import ExportPosition
    def return_from_datetime(obj):
        if type(obj) == Listing:
            return obj.publish_from
        elif type(obj) == ExportPosition:
            return obj.visible_from

    classes = (Listing, ExportPosition,)
    if type(x) not in classes or type(y) not in classes:
        raise NotImplementedError

    date_x = return_from_datetime(x)
    date_y = return_from_datetime(y)
    if date_x > date_y:
        return 1
    elif date_x < date_y:
        return -1
    return 0

class ExportManager(models.Manager):
    error_messages = {
        'cannot': 'This Publishable object cannot be exported'
    }

    def get_items_for_slug(self, slug):
        from ella.exports.models import Export
        exports = Export.objects.filter(slug=slug)
        if not exports:
            return list()
        return self.get_items_for_category(use_export=exports[0])
    
    def get_items_for_category(self, category=None, export=None):
        """
        generates export items for certain category or specific Export.

        @param   category   category asociated with Export
        @param   export     use Export object rather than category.

        Functionality:
        1. URL format is /category/path/to/any/depth/[content_type/]
        2. Sort export items by its main placement and listings.
        3. Override item's title, photo, description if ExportMeta for item and Export is present.
        4. Override item's position and visibility timerange if defined.
        """
        from ella.exports.models import Export, ExportPosition, ExportMeta,\
        POSITION_IS_NOT_OVERLOADED
        use_export = None
        use_category = category
        if not use_export:
            exports = Export.objects.filter(category=use_category)
        else:
            exports = (export,)
            use_category = use_export.category
        if exports:
            use_export = exports[0]
            # Find fitting ExportPositions
            positions = ExportPosition.objects.filter(
                Q(visible_to__gte=datetime.now()) | Q(visible_to__isnull=True),
                export=use_export, 
                position__exact=POSITION_IS_NOT_OVERLOADED,
                visible_from__lte=datetime.now(),
            )
            fix_positions = ExportPosition.objects.filter(
                Q(visible_to__gte=datetime.now()) | Q(visible_to__isnull=True),
                export=use_export, 
                position__gt=POSITION_IS_NOT_OVERLOADED,
                visible_from__lte=datetime.now(),
            )
            objects = list(Listing.objects.get_listing(
                use_category, 
                count=use_export.max_visible_items * 2
            ))
            map(lambda i: objects.append(i), positions)
            objects.sort(cmp=cmp_listing_or_meta)
            if fix_positions:
                # Assign positions of items (if position is overloaded via ExportPosition)
                self.__insert_to_position(fix_positions, objects)

            pre_out = objects[:use_export.max_visible_items]
        else:
            # Get listed objects for category
            objects = list(Listing.objects.get_listing(use_category))
            objects.sort(cmp=cmp_listing_or_meta)
            pre_out = objects
        # extract Publishable objects from Listing/ExportPosition objects
        out = list()
        for i in pre_out:
            pub = self.__get_overloaded_publishable(i, export=use_export)
            out.append(pub)
        # override title, photo, etc. via get_export_data?
        for o in out:
            yield o

    def __insert_to_position(self, fix_positions, out):
        """ 
        Insert elements in fix_positions queryset to specified position
        in list specified by parameter out.

        Fixed-positioned items have higher priority than existing items in list 
        given in parameter out.

        This method changes "out" parameter.
        """
        tmp = list()
        positions = fix_positions.order_by('position')
        last_position = positions[0].position
        for i in range(len(positions)):
            item = positions[i]
            diff = item.position - last_position
            if diff > 1:
                # gap found
                # append items from out up to diff, then append item
                for x in range(diff - 1):
                    tmp.append(out.pop(0))
            tmp.append(item)
            last_position = item.position

        for remaining in range(len(out)):
            tmp.append(out.pop(0))

        for t in tmp:
            out.append(t)

    def __get_publishable(self, obj):
        from ella.exports.models import ExportPosition
        if type(obj) == Listing:
            return obj.placement.publishable
        elif type(obj) == ExportPosition:
            return obj.object.publishable
        else:
            raise NotImplementedError

    def __get_overloaded_publishable(self, obj, export):
        """ 
        @return publishable object with overloaded attributes 
        title, photo, description. 
        """
        pub = self.__get_publishable(obj)
        field_dict = self.get_export_data(pub, export=export)
        pub.title = field_dict['title']
        pub.photo = field_dict['photo']
        pub.description = field_dict['description']
        if pub.photo:
            formated = pub.photo.get_formated_photo(export.photo_format.name)
            #pub.export_thumbnail_url = u'%s%s' % (settings.MEDIA_URL, formated.url)
            pub.export_thumbnail_url = formated.url
        else:
            pub.export_thumbnail_url = None
        return pub

    def get_export_data(self, publishable, export=None, export_category=None):
        """ 
        @return dict containing keys: title, photo, description. 
        If export parameter is None, first export fitting publishable's category
        is used.
        """
        from ella.exports.models import Export, ExportPosition, ExportMeta
        from ella.exports.models import UnexportableException
        if export:
            pub_export = export
        else:
            category = publishable.category
            if export_category:
                category = export_category
            pub_export = Export.objects.filter(category=category)
            if not pub_export:
                raise UnexportableException(self.error_messages['cannot'])
            pub_export = pub_export[0]
        
        # Try to find ExportMeta and ExportPosition for given publishable
        metas = ExportMeta.objects.filter(publishable=publishable)
        pos = None
        out = dict()
        # FIXME simplify follwing code (cycle tries to find appropriate ExportMeta for selected Export)
        for meta in metas:
            positions = ExportPosition.objects.filter(object=meta, export=pub_export)
            if not positions:
                return {
                    'title': meta.get_title(),
                    'photo': meta.get_photo(),
                    'description': meta.get_description()
                }

            pos = positions[0]
            return {
                'title': pos.object.get_title(),
                'photo': pos.object.get_photo(),
                'description': pos.object.get_description()
            }

        if not pos:
            return {
                'title': publishable.get_title(),
                'photo': publishable.get_photo(),
                'description': publishable.get_description()
            }

# EOF
