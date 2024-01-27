"""Utilities for downloading presidential speeches from Wikipedia (as of Jan 20,
2024).
"""
import json
import requests
from pathlib import Path

from bs4 import BeautifulSoup


URL_BASE = "https://en.wikisource.org"


def _scrape_list_of_speeches(url_extension: str) -> list[str]:
    """
    Find urls of all speeches given the relative extension path.

    @param url_extension: Relative path to base where full list of speeches is
        available.
    @returns list of url links to speeches.
    """
    page = requests.get(f"{URL_BASE}{url_extension}")
    soup = BeautifulSoup(page.content, features="html.parser")

    # Speech pages include a div with all the speeches listed (as a nested list
    # of alphabetically listed presidents).
    div_list = soup.find("div", {"class": "mw-category mw-category-columns"})

    def _read_li(li):
        a = li.find("a")
        return f'{URL_BASE}{a.get("href")}'

    return [_read_li(li) for li in div_list.find_all("li")]


def _scrape_speech(url: str) -> dict:
    """
    Read speech and meta data given the absolute url path.

    @param url: Absolute path to speech.
    @returns dict object including speech meta and text.
    """
    page = requests.get(url)
    soup = BeautifulSoup(page.content, features="html.parser")

    def _read_p(p):
        text = p.getText().strip()
        if "public domain" in text.lower():
            return ""
        return text

    text = "\n".join(
        [
            _read_p(p)
            for p in soup.find_all(
                lambda t: t.name == "p"
                and len(t.find_all_previous("div", {"class": "ws-noexport"})) > 1
            )
        ]
    )

    def _get_author():
        return soup.find("span", {"id": "header_author_text"}).getText().strip("by ")

    def _get_year():
        span = soup.find("span", {"id": "header_year_text"})
        if span is None:
            return 0
        return int(span.getText().strip().replace("(", "").replace(")", ""))

    def _get_title():
        return soup.find("span", {"id": "header_title_text"}).getText().strip()

    return {
        "author": _get_author(),
        "year": _get_year(),
        "title": _get_title(),
        "text": text.strip(),
    }


def _make_json_name(d: dict) -> str:
    return (
        f"{d['year']:04d}.{d['author'].lower().replace('.', '').replace(' ', '_')}.json"
    )


def inaugural(output_path: Path) -> None:
    """
    Scrape inaugural addresses.

    @param output_path: path in which to write speech JSONs.
    """
    speech_list = _scrape_list_of_speeches(
        "/wiki/Category:U.S._Presidential_Inaugural_Addresses"
    )
    print(f"found {len(speech_list)} total speeches")

    for speech in speech_list:
        data = _scrape_speech(speech)
        with open(output_path / _make_json_name(data), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def sotu(output_path: Path) -> None:
    """
    Scrape inaugural addresses.

    @param output_path: path in which to write speech JSONs.
    """
    # There's almost certainly a better way to do this with the php query, but
    # we'll just hard code the two pages here.
    speech_list = _scrape_list_of_speeches(
        "/wiki/Category:State_of_the_Union_addresses"
    ) + _scrape_list_of_speeches(
        "/wiki/Category:State_of_the_Union_addresses?pagefrom=Taft4%0AWilliam+Howard+Taft%27s+Fourth+State+of+the+Union+Address"
    )
    print(f"found {len(speech_list)} total speeches")

    for speech in speech_list:
        data = _scrape_speech(speech)
        with open(output_path / _make_json_name(data), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
