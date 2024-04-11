import re
from datetime import datetime, time

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class NewnjNbeSpider(CityScrapersSpider):
    name = "newnj_nbe"
    agency = "Newark Board of Education"
    timezone = "America/New_York"
    start_urls = ["https://www.nps.k12.nj.us/board-of-education/meetings/"]

    def parse(self, response):
        """
        Most of the meeting details are provided in a detail page.
        Though each meeting's location address varies, so they are taken
        from the main page and passed as a meta value to the followed
        callback method.
        """
        meetings_table = response.css(
            ".su-table.su-table-alternate table tbody tr:not(:first-child)"
        )
        for item in meetings_table:
            location_cell = item.css("td:nth-child(4)::text").getall()
            detail_link = item.css("td a::attr(href)").extract_first()

            yield response.follow(
                detail_link,
                callback=self._parse_detail,
                meta={"location_cell": location_cell},
            )

    def _parse_detail(self, response):
        location_cell = response.meta["location_cell"]

        date = self._parse_date(response)
        start_time, end_time = self._parse_start_end_time(response)

        meeting = Meeting(
            title=self._parse_title(response),
            description="",
            classification=BOARD,
            start=self._gen_datetime(date, start_time),
            end=self._gen_datetime(date, end_time),
            all_day=False,
            time_notes="",
            location=self._parse_location(response, location_cell),
            links=self._parse_links(response),
            source=response.url,
        )

        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)

        yield meeting

    def _parse_title(self, item):
        title = item.css("h1.entry-title::text").extract_first()
        return title

    def _gen_datetime(self, date, time_obj):
        if time_obj is None:
            time_obj = time(0, 0)  # Midnight

        return datetime.combine(date, time_obj)

    def _parse_start_end_time(self, item):
        time_str = item.css(".su-table table tr:nth-child(2) td:nth-child(2)::text")[
            0
        ].get()
        if time_str:
            time_str = time_str.strip()
            start_time_str, end_time_str = time_str.split(" - ")

            start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
            end_time = datetime.strptime(end_time_str, "%I:%M %p").time()

            return start_time, end_time
        return None, None

    def _parse_date(self, item):
        date_str = item.css(
            ".su-table.su-table-alternate table tr td:nth-child(2)::text"
        )[0].get()

        date_obj = datetime.strptime(date_str, "%m/%d/%Y")

        return date_obj

    def _parse_location(self, item, location_cell):
        if "Virtual" in location_cell:
            return {
                "address": "Virtual",
                "name": "Virtual",
            }

        location_name = item.css(
            ".su-table table tr:nth-child(3) td:nth-child(2) a::text"
        ).extract_first()
        return {
            "address": self._format_location(location_cell),
            "name": location_name.split(" - ")[0] if location_name else None,
        }

    def _parse_links(self, item):
        links = []
        watch_links = item.css(
            ".su-table.su-table-alternate table tbody tr:first-child td:nth-child(2)"
        )
        for watch_link in watch_links:
            a_tags = watch_link.css("a")
            for a_tag in a_tags:
                link = {
                    "title": a_tag.css("::text").get(),
                    "href": a_tag.css("::attr(href)").get(),
                }
                links.append(link)
        return links

    def _get_ordinal_suffix(self, number):
        """
        Returns the ordinal suffix for a number.
        """
        if 11 <= (number % 100) <= 13:
            return "th"
        else:
            return {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")

    def _format_location(self, lst):
        """
        This method is used for writing back an ordinal suffix to the
        location string which was taken out during the inital extraction.
        """
        lst = [i.strip() for i in lst if i.strip()]
        if re.search(r"\d+$", lst[0]):
            number = int(re.search(r"\d+$", lst[0]).group())
            suffix = self._get_ordinal_suffix(number)
            lst[0] = re.sub(r"\d+$", f"{number}{suffix}", lst[0])
        joined_string = " ".join(lst) + ", Newark, NJ"
        return joined_string
