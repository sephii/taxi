from __future__ import unicode_literals

from taxi.aliases import AliasesDatabase, Mapping


def test_alias_in():
    db = AliasesDatabase({'foo': Mapping(mapping=(1, 2), backend='test')})
    assert 'foo' in db


def test_alias_not_in():
    db = AliasesDatabase({'foo': Mapping(mapping=(1, 2), backend='test')})
    assert 'bar' not in db


def test_alias_iter():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    })
    alias_set = set(db)

    assert alias_set == set(['foo', 'bar'])


def test_alias_update_item():
    db = AliasesDatabase({'foo': Mapping(mapping=(1, 2), backend='test')})
    db['foo'] = Mapping(mapping=(2, 2), backend='test')

    assert db['foo'].mapping == (2, 2)


def test_alias_add_item():
    db = AliasesDatabase({'foo': Mapping(mapping=(1, 2), backend='test')})
    db['bar'] = Mapping(mapping=(2, 2), backend='test')

    assert db['foo'].mapping == (1, 2)
    assert db['bar'].mapping == (2, 2)


def test_alias_iteritems():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    })
    alias_set = set(db.iteritems())

    assert alias_set == set([
        ('foo', Mapping(mapping=(1, 2), backend='test')),
        ('bar', Mapping(mapping=(1, 3), backend='test')),
    ])


def test_keys():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    })
    assert set(db.keys()) == set(['foo', 'bar'])


def test_update():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    })
    db.update({
        'foo': Mapping(mapping=(2, 2), backend='test'),
        'baz': Mapping(mapping=(9, 9), backend='test'),
    })

    assert set(db.iteritems()) == set([
        ('foo', Mapping(mapping=(2, 2), backend='test')),
        ('bar', Mapping(mapping=(1, 3), backend='test')),
        ('baz', Mapping(mapping=(9, 9), backend='test')),
    ])


def test_reset():
    db = AliasesDatabase({'foo': Mapping(mapping=(1, 2), backend='test')})
    db.reset()

    assert 'foo' not in db


def test_get_reversed_aliases():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    })
    reversed_aliases = db.get_reversed_aliases().items()

    assert set(reversed_aliases) == set([
        (Mapping(mapping=(1, 2), backend='test'), 'foo'),
        (Mapping(mapping=(1, 3), backend='test'), 'bar'),
    ])


def test_filter_from_mapping_partial():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
        'baz': Mapping(mapping=(2, 3), backend='test'),
    })
    assert db.filter_from_mapping((1, None)) == {
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
    }


def test_filter_from_mapping():
    db = AliasesDatabase({
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
        'baz': Mapping(mapping=(2, 3), backend='test'),
    })
    assert db.filter_from_mapping((1, 3)) == {
        'bar': Mapping(mapping=(1, 3), backend='test')
    }


def test_filter_from_mapping_empty_search():
    aliases = {
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'bar': Mapping(mapping=(1, 3), backend='test'),
        'baz': Mapping(mapping=(2, 3), backend='test'),
    }
    db = AliasesDatabase(aliases)

    assert db.filter_from_mapping(None) == aliases


def test_filter_from_alias():
    aliases = {
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'foobar': Mapping(mapping=(1, 3), backend='test'),
        'baz': Mapping(mapping=(2, 3), backend='test'),
    }
    db = AliasesDatabase(aliases)

    assert db.filter_from_alias('foo') == {
        'foo': Mapping(mapping=(1, 2), backend='test'),
        'foobar': Mapping(mapping=(1, 3), backend='test'),
    }
