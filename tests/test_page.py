import dateutil
import pytest
from haralyzer import HarPage, HarParser
import re

PAGE_ID = 'page_3'


def test_init(har_data):
    """
    Test the object loading
    """
    with pytest.raises(ValueError):
        page = HarPage(PAGE_ID)

    # Make sure it can load with either har_data or a parser
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    assert isinstance(page, HarPage)
    parser = HarParser(init_data)
    page = HarPage(PAGE_ID, har_parser=parser)
    assert isinstance(page, HarPage)

    assert len(page.entries) == 4
    # Make sure that the entries are actually in order. Going a little bit
    # old school here.
    for index in range(0, len(page.entries)):
        if index != len(page.entries) - 1:
            current_date = dateutil.parser.parse(
                page.entries[index]['startedDateTime'])
            next_date = dateutil.parser.parse(
                page.entries[index + 1]['startedDateTime'])
            assert current_date <= next_date


def test_filter_entries(har_data):
    """
    Tests ability to filter entries, with or without regex
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    # Filter by request type only
    entries = page.filter_entries(request_type='.*ET')
    assert len(entries) == 4
    for entry in entries:
        assert entry['request']['method'] == 'GET'

    # Filter by request type and content_type
    entries = page.filter_entries(request_type='.*ET', content_type='image.*')
    assert len(entries) == 1
    for entry in entries:
        assert entry['request']['method'] == 'GET'
        for header in entry['response']['headers']:
            if header['name'] == 'Content-Type':
                assert re.search('image.*', header['value'])

    # Filter by request type, content type, and status code
    entries = page.filter_entries(request_type='.*ET', content_type='image.*',
                                  status_code='2.*')
    assert len(entries) == 1
    for entry in entries:
        assert entry['request']['method'] == 'GET'
        assert re.search('2.*', str(entry['response']['status']))
        for header in entry['response']['headers']:
            if header['name'] == 'Content-Type':
                assert re.search('image.*', header['value'])

    entries = page.filter_entries(request_type='.*ST')
    assert len(entries) == 0
    entries = page.filter_entries(request_type='.*ET', content_type='video.*')
    assert len(entries) == 0
    entries = page.filter_entries(request_type='.*ET', content_type='image.*',
                                  status_code='3.*')


def test_get_load_time(har_data):
    """
    Tests HarPage.get_load_time()
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    assert page.get_load_time(request_type='GET') == 463
    assert page.get_load_time(request_type='GET', async=False) == 843
    assert page.get_load_time(content_type='image.*') == 304
    assert page.get_load_time(status_code='2.*') == 463


def test_entries(har_data):
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    for entry in page.entries:
        assert entry['pageref'] == page.page_id


def test_file_types(har_data):
    """
    Test file type properties
    """
    init_data = har_data('cnn.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    file_types = {'image_files': ['image'], 'css_files': ['css'],
                  'js_files': ['javascript'], 'audio_files': ['audio'],
                  'video_files': ['video', 'flash'], 'text_files': ['text']}

    # TODO - Add a test for page.misc_files

    for k, v in file_types.iteritems():
        for asset in getattr(page, k, None):
            if not _correct_file_type(asset, v):
                print asset
            assert _correct_file_type(asset, v)


def test_request_types(har_data):
    """
    Test request type filters
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    # Check request type lists
    for req in page.get_requests:
        assert req['request']['method'] == 'GET'

    for req in page.post_requests:
        assert req['request']['method'] == 'POST'


def test_sizes(har_data):
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    assert page.page_size == 238
    assert page.total_page_size == 62204
    assert page.total_text_size == 246
    assert page.total_css_size == 8
    assert page.total_js_size == 38367
    assert page.total_image_size == 23591


def test_load_times(har_data):
    """
    This whole test really needs better sample data. I need to make a
    web page with like 2-3 of each asset type to really test the load times.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    # Check initial page load
    assert page.actual_page['request']['url'] == 'http://humanssuck.net/'

    # Check initial page load times
    assert page.initial_load_time == 153
    assert page.content_load_time == 543
    # Check content type browser (async) load times
    assert page.image_load_time == 304
    assert page.css_load_time == 76
    assert page.js_load_time == 310
    assert page.html_load_time == 153
    # TODO - Need to get sample data for these types
    assert page.audio_load_time == 0
    assert page.video_load_time == 0

    # Total load times
    assert page.total_load_time == 567
    assert page.total_image_load_time == 304
    assert page.total_css_load_time == 76
    assert page.total_js_load_time == 310
    assert page.total_html_load_time == 153
    # TODO - Need to get sample data for these types
    assert page.total_audio_load_time == 0
    assert page.total_video_load_time == 0


def test_time_to_first_byte(har_data):
    """
    Tests that TTFB is correctly reported as a property of the page.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    assert page.time_to_first_byte == 153


def _correct_file_type(entry, file_types):
    for header in entry['response']['headers']:
        if header['name'] == 'Content-Type':
            return any(ft in header['value'] for ft in file_types)
