from __future__ import unicode_literals

from taxi.alias import AliasDatabase, Mapping


def test_alias_in():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    assert 'foo' in db


def test_alias_in_local_alias():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    db.local_aliases.add('local_alias')

    assert 'foo' in db
    assert 'local_alias' in db


def test_alias_not_in():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    assert 'bar' not in db


def test_alias_not_in_local_alias():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    db.local_aliases.add('local_alias')

    assert 'bar' not in db


def test_alias_iter():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    })
    db.local_aliases.add('local_alias')
    alias_set = set(db)

    assert alias_set == set(['foo', 'bar', 'local_alias'])


def test_alias_update_item():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    db['foo'] = Mapping(mapping=(2, 2), backend='dummy')

    assert db['foo'].mapping == (2, 2)


def test_alias_add_item():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    db['bar'] = Mapping(mapping=(2, 2), backend='dummy')

    assert db['foo'].mapping == (1, 2)
    assert db['bar'].mapping == (2, 2)


def test_alias_iteritems():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    })
    db.local_aliases.add('local_alias')
    alias_set = set(db.iteritems())

    assert alias_set == set([
        ('foo', Mapping(mapping=(1, 2), backend='dummy')),
        ('bar', Mapping(mapping=(1, 3), backend='dummy')),
        ('local_alias', None)
    ])


def test_keys():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    })
    db.local_aliases.add('local_alias')
    assert set(db.keys()) == set(['foo', 'bar', 'local_alias'])


def test_update():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    })
    db.update({
        'foo': Mapping(mapping=(2, 2), backend='dummy'),
        'baz': Mapping(mapping=(9, 9), backend='dummy'),
    })

    assert set(db.iteritems()) == set([
        ('foo', Mapping(mapping=(2, 2), backend='dummy')),
        ('bar', Mapping(mapping=(1, 3), backend='dummy')),
        ('baz', Mapping(mapping=(9, 9), backend='dummy')),
    ])


def test_reset():
    db = AliasDatabase({'foo': Mapping(mapping=(1, 2), backend='dummy')})
    db.reset()

    assert 'foo' not in db


def test_is_local():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
    })
    db.local_aliases.add('local_alias')

    assert not db.is_local('foo')
    assert db.is_local('local_alias')


def test_get_reversed_aliases():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    })
    db.local_aliases.add('local_alias')
    reversed_aliases = db.get_reversed_aliases().items()

    assert set(reversed_aliases) == set([
        (Mapping(mapping=(1, 2), backend='dummy'), 'foo'),
        (Mapping(mapping=(1, 3), backend='dummy'), 'bar'),
    ])


def test_filter_from_mapping_partial():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
        'baz': Mapping(mapping=(2, 3), backend='dummy'),
    })
    assert db.filter_from_mapping((1, None)) == {
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
    }


def test_filter_from_mapping():
    db = AliasDatabase({
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
        'baz': Mapping(mapping=(2, 3), backend='dummy'),
    })
    assert db.filter_from_mapping((1, 3)) == {
        'bar': Mapping(mapping=(1, 3), backend='dummy')
    }


def test_filter_from_mapping_empty_search():
    aliases = {
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'bar': Mapping(mapping=(1, 3), backend='dummy'),
        'baz': Mapping(mapping=(2, 3), backend='dummy'),
    }
    db = AliasDatabase(aliases)

    assert db.filter_from_mapping('') == aliases


def test_filter_from_alias():
    aliases = {
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'foobar': Mapping(mapping=(1, 3), backend='dummy'),
        'baz': Mapping(mapping=(2, 3), backend='dummy'),
    }
    db = AliasDatabase(aliases)

    assert db.filter_from_alias('foo') == {
        'foo': Mapping(mapping=(1, 2), backend='dummy'),
        'foobar': Mapping(mapping=(1, 3), backend='dummy'),
    }
