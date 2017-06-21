import datetime

from . import create_timesheet


def test_entry_with_question_mark_description_is_ignored():
    t = create_timesheet('10.10.2012\nfoo 2 ?')
    assert list(t.entries.values())[0][0].ignored


def test_entry_with_question_mark_in_alias_is_ignored():
    t = create_timesheet('10.10.2012\nfoo? 2 Foo')
    assert list(t.entries.values())[0][0].ignored


def test_entry_without_question_mark_in_alias_is_not_ignored():
    t = create_timesheet('10.10.2012\nfoo 2 Foo')
    assert not list(t.entries.values())[0][0].ignored


def test_add_ignored_flag_to_alias_makes_entry_ignored():
    t = create_timesheet('10.10.2012\nfoo 2 Foo')
    t.entries[datetime.date(2012, 10, 10)][0].ignored = True
    assert list(t.entries.values())[0][0].ignored


def test_entry_without_start_time_following_duration_is_ignored():
    contents = """10.10.2012
foo 0900-1000 baz
bar 2 bar
foo     -1200 bar"""
    t = create_timesheet(contents)
    assert list(t.entries.values())[0][2].ignored


def test_entry_without_start_time_without_previous_entry_is_ignored():
    contents = """10.10.2012
foo -1000 baz"""
    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].ignored


def test_entry_without_start_time_after_previous_entry_without_end_time_is_ignored():
    contents = """10.10.2012
foo 0900-1000 baz
bar 1000-? bar
foo     -1200 bar"""
    t = create_timesheet(contents)
    assert list(t.entries.values())[0][2].ignored


def test_entry_without_end_time_is_ignored():
    contents = "10.10.2012\nfoo 1400-? Foo"
    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].ignored


def test_add_ignored_flag_to_alias_makes_to_lines_output_question_mark():
    t = create_timesheet('10.10.2012\nfoo 2 Foo')
    t.entries[datetime.date(2012, 10, 10)][0].alias = 'foo?'
    assert t.entries.to_lines()[-1] == 'foo? 2 Foo'


def test_entry_with_zero_duration_is_ignored():
    contents = "10.10.2012\nfoo 0 Foo"
    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].ignored
