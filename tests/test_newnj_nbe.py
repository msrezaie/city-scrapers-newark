from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.newnj_nbe import NewnjNbeSpider

test_response = file_response(
    join(dirname(__file__), "files", "newnj_nbe.html"),
    url="https://www.nps.k12.nj.us/board-of-education/meetings/",
)

test_detail_response = file_response(
    join(dirname(__file__), "files", "newnj_nbe_detail.html"),
    url="https://www.nps.k12.nj.us/events/nboe-retreat-05-20-2023/",
)

spider = NewnjNbeSpider()

freezer = freeze_time("2024-03-27")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
test_detail_response.meta["location_cell"] = "Virtual"
parsed_item = next(spider._parse_detail(test_detail_response), None)

freezer.stop()

"""
Arbitrary number of items. 24 is the total
number of meetings extracted from the organization's website.
"""


def test_count():
    assert len(parsed_items) == 24


def test_title():
    assert parsed_item["title"] == "NBOE Retreat"


def test_description():
    assert parsed_item["description"] == ""


def test_start():
    assert parsed_item["start"] == datetime(2023, 5, 20, 9, 0)


def test_end():
    assert parsed_item["end"] == datetime(2023, 5, 20, 12, 0)


def test_time_notes():
    assert parsed_item["time_notes"] == ""


def test_id():
    assert parsed_item["id"] == "newnj_nbe/202305200900/x/nboe_retreat"


def test_status():
    assert parsed_item["status"] == PASSED


def test_location():
    assert parsed_item["location"] == {"address": "Virtual", "name": "Virtual"}


def test_source():
    assert (
        parsed_item["source"]
        == "https://www.nps.k12.nj.us/events/nboe-retreat-05-20-2023/"
    )


def test_links():
    assert parsed_item["links"] == [
        {
            "title": "Join via Webex",
            "href": "https://nboe.webex.com/nboe/j.php?MTID=m1a907c8d4af9175efba61f7f2ec99702",  # noqa
        },
        {"title": "Watch on Facebook Live", "href": "https://fb.me/e/11wRxFREk"},
        {"title": "Watch on Vimeo", "href": "https://vimeo.com/event/3417032"},
    ]


def test_classification():
    assert parsed_item["classification"] == BOARD


def test_all_day():
    assert parsed_item["all_day"] is False
