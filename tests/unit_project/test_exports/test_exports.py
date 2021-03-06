# -*- coding: utf-8 -*-
from time import time, gmtime, localtime, strftime
from datetime import datetime

from djangosanetesting import DatabaseTestCase
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify

from ella.core.models import Category, Listing, Placement, Author, Publishable
from ella.articles.models import Article
from ella.exports.models import Export, ExportMeta, ExportPosition
from ella.exports.models import UnexportableException

DATE_FORMAT = '%Y-%m-%d %H:%M'
HOUR = 3600
MINUTE = 60

def article_builder(**kwargs):
    title = kwargs.get('title', u'Third Article')
    a = Article.objects.create(
        title=title,
        slug=kwargs.get('slug', slugify(title)),
        description=kwargs.get('description', u'Some\nlonger\ntext'),
        category=kwargs.get('category')
    )
    return Publishable.objects.get(pk=a.pk)

def placement_for_publishable_builder(**kwargs):
    pub = kwargs.get('publishable')
    dat_from = datetime.strptime(kwargs.get('publish_from'), DATE_FORMAT)
    dat_to = datetime.strptime(kwargs.get('publish_to'), DATE_FORMAT)
    return Placement.objects.create(
        publishable=pub,
        category=pub.category,
        slug=pub.slug,
        publish_from=dat_from,
        publish_to=dat_to
    )

def listing_for_placement(**kwargs):
    plac = kwargs.get('placement')
    dat_from = datetime.strptime(kwargs.get('publish_from'), DATE_FORMAT)
    dat_to = datetime.strptime(kwargs.get('publish_to'), DATE_FORMAT)
    out = Listing.objects.create(
        placement=plac,
        category=kwargs.get('category'),
        publish_from=dat_from,
        publish_to=dat_to,
    )
    if 'priority_from' in kwargs and 'priority_to' in kwargs \
        and 'priority_value' in kwargs:
        prio_dat_from = datetime.strptime(kwargs.get('priority_from'), DATE_FORMAT)
        prio_dat_to = datetime.strptime(kwargs.get('priority_to'), DATE_FORMAT)
        out.priority_from = prio_dat_from
        out.priority_to = prio_dat_to
        out.priority_value = kwargs.get('priority_value')

class TestExport(DatabaseTestCase):
    " Export model and its manager test. "

    def setUp(self):
        super(TestExport, self).setUp()
        self.site = Site.objects.get(name='example.com')
        self.site_second = Site.objects.create(
            domain='test.net', 
            name='test.net'
        )
        self.author = Author.objects.create(name='igorko', slug='igorko')
        # Categories
        self.categoryA = Category.objects.create( 
            title='Category A',
             slug='category-a',
             tree_parent=None,
             description='auauau',
             site=self.site 
        )
        self.categoryB = Category.objects.create( 
            title='Category B',
             slug='category-b',
             tree_parent=self.categoryA,
             description='bububu',
             site=self.site 
        )
        self.categoryH = Category.objects.create( 
            title='Category H',
             slug='category-h',
             tree_parent=self.categoryA,
             description='Export category one.',
             site=self.site 
        )
        self.categoryI = Category.objects.create( 
            title='Category I',
             slug='category-i',
             tree_parent=self.categoryA,
             description='Eksport kategory zwo',
             site=self.site 
        )
        # Publishable objects (Articlez)
        self.publishableA = article_builder(
            title=u'First Article', 
            category=self.categoryA
        )
        self.publishableB = article_builder(
            title=u'Second Article', 
            category=self.categoryA
        )
        self.publishableC = article_builder(
            title=u'Third Article', 
            category=self.categoryA
        )
        self.publishableD = article_builder(
            title=u'Fourth Article', 
            category=self.categoryA
        )
        # Placements, listings & co.
        self.setup_placements_listings()

    def setup_placements_listings(self):
        now = time()
        self.str_now = strftime(DATE_FORMAT, localtime(now))
        self.str_future = strftime(DATE_FORMAT, localtime(now + HOUR))

        # publishable A
        self.placementA = placement_for_publishable_builder(
            publishable=self.publishableA,
            publish_from=self.str_now,
            publish_to=self.str_future
        )

        self.str_listingA_from = strftime(DATE_FORMAT, localtime(now))
        self.str_listingA_to = strftime(DATE_FORMAT, localtime(now + HOUR * 3))
        self.str_listingB_from = strftime(DATE_FORMAT, localtime(now - HOUR))
        self.str_listingB_to = strftime(DATE_FORMAT, localtime(now + HOUR))
        self.str_listingC_from = strftime(DATE_FORMAT, localtime(now - HOUR))
        self.str_listingC_to = strftime(DATE_FORMAT, localtime(now + HOUR * 2))
        self.listA = listing_for_placement(
            placement=self.placementA,
            publish_from=self.str_listingA_from,
            publish_to=self.str_listingA_to,
            category=self.categoryH
        )
        
        # publishable B
        self.placementB = placement_for_publishable_builder(
            publishable=self.publishableB,
            publish_from=self.str_now,
            publish_to=self.str_future
        )

        self.listB = listing_for_placement(
            placement=self.placementB,
            publish_from=self.str_listingB_from,
            publish_to=self.str_listingB_to,
            category=self.categoryH
        )

        # Exports
        self.exportA = Export.objects.create(
            category=self.categoryH,
            title='hotentot',
            slug='hotentot',
            max_visible_items=2,
            photo_format_id=0
        )
        self.export_position_overrides = Export.objects.create(
            category=self.categoryI,
            title='export for testing position overrides',
            slug='export-for-testing-position-overrides',
            max_visible_items=3,
            photo_format_id=0
        )
        self.export_metaA = ExportMeta.objects.create(
            publishable=self.publishableC,
            title=u'ahoy!',
            description=u'Enjoy polka!',
        )
        self.export_metaB = ExportMeta.objects.create(
            publishable=self.publishableD,
            title=u'',
            description=u'',
        )
        ExportPosition.objects.create(
            object=self.export_metaA,
            export=self.export_position_overrides,
            visible_from=datetime.strptime(self.str_listingA_from, DATE_FORMAT),
            visible_to=datetime.strptime(self.str_listingA_to, DATE_FORMAT),
            position=2
        )
        ExportPosition.objects.create(
            object=self.export_metaB,
            export=self.export_position_overrides,
            visible_from=datetime.strptime(self.str_listingB_from, DATE_FORMAT),
            visible_to=datetime.strptime(self.str_listingB_to, DATE_FORMAT),
            position=1
        )
#TODO create test data with only publish_from defined (usual way of creating Listings)

    def test_get_items_for_category(self):
        " basic test getting items for certain export category. "
        degen = Export.objects.get_items_for_category(self.categoryH)
        out = map(None, degen)
        self.assert_equals(len(out), 2)
        self.assert_true(self.publishableA in out)
        self.assert_true(self.publishableB in out)
        # ordering test
        self.assert_equals(
            out,
            [self.publishableB, self.publishableA]
        )

    def test_get_items_for_category__placed_by_position(self):
        " test get_items_for_category() method to overloaded item position "
        degen = Export.objects.get_items_for_category(self.categoryI)
        out = map(None, degen)
        self.assert_equals(len(out), 2)
        self.assert_true(self.publishableC in out)
        self.assert_true(self.publishableD in out)

    def test_get_items_for_category__placed_by_position_and_by_listings(self):
        """
        test whether position overloading works right if some of ExportPosition 
        objects have .position == 0. 
        """
        listing_for_placement(
            placement=self.placementB,
            publish_from=self.str_listingB_from,
            publish_to=self.str_listingB_to,
            category=self.categoryI
        )
        listing_for_placement(
            placement=self.placementA,
            publish_from=self.str_listingA_from,
            publish_to=self.str_listingA_to,
            category=self.categoryI
        )
        degen = Export.objects.get_items_for_category(self.categoryI)
        out = map(None, degen)
        self.assert_equals(len(out), 3)
        self.assert_true(self.publishableC in out)
        self.assert_true(self.publishableD in out)
        self.assert_true(self.publishableB in out)
        # ordering test
        self.assert_equals(
            out, 
            [self.publishableD, self.publishableC, self.publishableB]
        )

    def test_get_export_data(self):
        out = Export.objects.get_export_data(
            self.publishableA, 
            export_category=self.categoryH
        )
        right_out = {
            'title': u'First Article',
            'description': u'Some\nlonger\ntext',
            'photo': None
        }
        self.assert_equals(out, right_out)
        # test unexportable publishable (Export object for publishable's category is not present) as well.
        try:
            out = Export.objects.get_export_data(self.publishableD)
            self.assert_equals('Object should not be exportable!', '')
        except UnexportableException:
            pass #OK

    def test_get_export_data__overloading_fields(self):
        out = Export.objects.get_export_data(
            self.publishableC, 
            export_category=self.categoryI
        )
        right_out = {
            'title': u'ahoy!',
            'description': u'Enjoy polka!',
            'photo': None
        }
        self.assert_equals(out, right_out)

    def test_unique(self):
        "test uniqness of items returned from get_items_for_category() method."
        listing_for_placement(
            placement=self.placementA,
            publish_from=self.str_listingC_from,
            publish_to=self.str_listingC_to,
            category=self.categoryH
        )
        self.exportA.max_visible_items = 5
        self.exportA.save()
        degen = Export.objects.get_items_for_category(self.categoryH)
        out = map(None, degen)
        self.assert_equals(len(out), 2)

    def test_unique_positions(self):
        self.export_metaC = ExportMeta.objects.create(
            publishable=self.publishableA,
            title=u'',
            description=u'',
        )
        ExportPosition.objects.create(
            object=self.export_metaC,
            export=self.exportA,
            visible_from=datetime.strptime(self.str_listingB_from, DATE_FORMAT),
            visible_to=datetime.strptime(self.str_listingB_to, DATE_FORMAT),
            position=1
        )
        self.exportA.max_visible_items = 5
        self.exportA.save()
        degen = Export.objects.get_items_for_category(self.categoryH)
        out = map(None, degen)
        self.assert_equals(len(out), 3)

    def test_(self):
        " copy/paste template "
        pass

# EOF
