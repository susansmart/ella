# -*- coding: utf-8 -*-
from djangosanetesting import UnitTestCase, DatabaseTestCase

from ella.core.templatetags.related import parse_related_tag, RelatedNode
from ella.core.models import Related, Publishable

from unit_project.test_core import create_basic_categories, create_and_place_a_publishable, \
        create_and_place_more_publishables, list_all_placements_in_category_by_hour

class TestGetRelated(DatabaseTestCase):
    def setUp(self):
        super(TestGetRelated, self).setUp()
        create_basic_categories(self)
        create_and_place_a_publishable(self)
        create_and_place_more_publishables(self)

        Publishable.objects.all().update(category=self.publishable.category)

        list_all_placements_in_category_by_hour(self, category=self.publishable.category)


    def test_returns_publishables_listed_in_same_cat_if_no_related(self):
        expected = map(lambda x: x.pk, reversed(self.publishables))
        self.assert_equals(
                expected,
                [p.pk for p in Related.objects.get_related_for_object(self.publishable, len(expected))]
            )

    def test_returns_at_most_count_objects(self):
        self.assert_equals(
                [self.publishables[-1].pk],
                [p.pk for p in Related.objects.get_related_for_object(self.publishable, 1)]
            )

    def test_returns_manual_objects_first(self):
        r = Related(publishable=self.publishables[0])
        r.related = self.publishable
        r.save()

        self.assert_equals(
                [self.publishables[0].pk, self.publishables[-1].pk],
                [p.pk for p in Related.objects.get_related_for_object(self.publishable, 2)]
            )

    def test_returns_unique_objects(self):
        r = Related(publishable=self.publishables[-2])
        r.related = self.publishable
        r.save()

        self.assert_equals(
                [self.publishables[-2].pk, self.publishables[-1].pk, self.publishables[-3].pk],
                [p.pk for p in Related.objects.get_related_for_object(self.publishable, 3)]
            )

class TestRelatedTagParser(UnitTestCase):
    '''
    {% related N [app_label.Model, ...] for object as var_name %}
    '''
    def setUp(self):
        super(TestRelatedTagParser, self).setUp()
        self.minimal_args = ['related', '10', 'for', 'obj_var', 'as', 'some_var']

    def test_minimal_args(self):
        obj_var, count, var_name, mods = parse_related_tag(self.minimal_args)
        self.assert_equals('obj_var', obj_var)
        self.assert_equals(10, count)
        self.assert_equals('some_var', var_name)
        self.assert_equals([], mods)

    def test_limit_bu_model(self):
        from ella.articles.models import Article, ArticleContents
        self.minimal_args.insert(2, 'articles.article')
        obj_var, count, var_name, mods = parse_related_tag(self.minimal_args)
        self.assert_equals('obj_var', obj_var)
        self.assert_equals(10, count)
        self.assert_equals('some_var', var_name)
        self.assert_equals([Article], mods)

    def test_limit_bu_more_models(self):
        from ella.articles.models import Article, ArticleContents
        self.minimal_args.insert(2, 'articles.article,articles.articlecontents')
        obj_var, count, var_name, mods = parse_related_tag(self.minimal_args)
        self.assert_equals('obj_var', obj_var)
        self.assert_equals(10, count)
        self.assert_equals('some_var', var_name)
        self.assert_equals([Article, ArticleContents], mods)

    def test_limit_bu_more_models_with_space(self):
        from ella.articles.models import Article, ArticleContents
        self.minimal_args.insert(2, 'articles.article,')
        self.minimal_args.insert(3, 'articles.articlecontents')
        obj_var, count, var_name, mods = parse_related_tag(self.minimal_args)
        self.assert_equals('obj_var', obj_var)
        self.assert_equals(10, count)
        self.assert_equals('some_var', var_name)
        self.assert_equals([Article, ArticleContents], mods)

    def test_limit_bu_more_models_with_spaces_around_comma(self):
        from ella.articles.models import Article, ArticleContents
        self.minimal_args.insert(2, 'articles.article')
        self.minimal_args.insert(3, ',')
        self.minimal_args.insert(4, 'articles.articlecontents')
        obj_var, count, var_name, mods = parse_related_tag(self.minimal_args)
        self.assert_equals('obj_var', obj_var)
        self.assert_equals(10, count)
        self.assert_equals('some_var', var_name)
        self.assert_equals([Article, ArticleContents], mods)
