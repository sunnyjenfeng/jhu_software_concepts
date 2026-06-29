"""Tests for the worker scraper."""

import os
import sys

import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
WORKER_DIR = os.path.join(PROJECT_DIR, "src", "worker")
sys.path.insert(0, WORKER_DIR)

import scrape  # pylint: disable=wrong-import-position


HTML = """
<table>
  <tr><th>School</th><th>Program</th><th>Added On</th><th>Decision</th><th>Sort</th></tr>
  <tr>
    <td><a href="/result/123">Test University</a></td>
    <td>Computer Science PhD</td>
    <td>May 1, 2026</td>
    <td>Accepted on May 1</td>
    <td>Total comments</td>
  </tr>
  <tr><td>Fall 2026 International GPA 3.90</td></tr>
  <tr><td>Helpful comment</td></tr>
</table>
"""


class FakeDriver:
    """Small Selenium driver test double."""

    page_source = HTML

    def __init__(self):
        """Initialize captured driver state."""
        self.urls = []
        self.closed = False
        self.quit_called = False

    def get(self, url):
        """Capture navigated URL."""
        self.urls.append(url)

    def close(self):
        """Mark the browser tab as closed."""
        self.closed = True

    def quit(self):
        """Mark the browser process as quit."""
        self.quit_called = True


class FakeWait:  # pylint: disable=too-few-public-methods
    """Small WebDriverWait test double."""

    def __init__(self, driver, timeout):
        """Store wait inputs."""
        self.driver = driver
        self.timeout = timeout

    def until(self, _condition):
        """Pretend the wait condition succeeded."""
        return True


@pytest.mark.worker
def test_scrape_data(monkeypatch):
    """Scrape a table page with fake Selenium objects."""
    fake_driver = FakeDriver()

    monkeypatch.setattr(scrape.webdriver, "Chrome", lambda service, options: fake_driver)
    monkeypatch.setattr(scrape, "WebDriverWait", FakeWait)
    monkeypatch.setattr(scrape.time, "sleep", lambda seconds: None)

    records = scrape.scrape_data(start_page=1, end_page=1)

    assert fake_driver.urls == ["https://www.thegradcafe.com/survey?page=1"]
    assert fake_driver.closed is True
    assert fake_driver.quit_called is True
    assert records == [
        {
            "page_number": 1,
            "School": "Test University",
            "Program": "Computer Science PhD",
            "Added On": "May 1, 2026",
            "Decision": "Accepted on May 1",
            "applicant_entry_url": "https://www.thegradcafe.com/result/123",
            "extra_info": "Fall 2026 International GPA 3.90",
            "comments": "Helpful comment",
            "raw_texts": [
                "Test University",
                "Computer Science PhD",
                "May 1, 2026",
                "Accepted on May 1",
                "Total comments",
            ],
        }
    ]


@pytest.mark.worker
def test_scrape_data_handles_driver_close_error(monkeypatch):
    """The scraper still returns records if browser cleanup raises."""

    class BadCloseDriver(FakeDriver):
        """Driver whose close method raises."""

        def close(self):
            """Raise a cleanup error."""
            raise RuntimeError("close failed")

    monkeypatch.setattr(scrape.webdriver, "Chrome", lambda service, options: BadCloseDriver())
    monkeypatch.setattr(scrape, "WebDriverWait", FakeWait)
    monkeypatch.setattr(scrape.time, "sleep", lambda seconds: None)

    assert scrape.scrape_data(start_page=1, end_page=1)
