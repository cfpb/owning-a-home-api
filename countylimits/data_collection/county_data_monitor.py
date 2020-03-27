import os
from difflib import ndiff

from django.core.mail import send_mail

import requests
from bs4 import BeautifulSoup as bs


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CENSUS_CHANGELOG = "https://www.census.gov/geo/reference/county-changes.html"
LAST_CHANGELOG = "{}/last_changelog.txt".format(BASE_DIR)
CHANGELOG_ID = "tab_2010"


def get_current_log():
    changelog_response = requests.get(CENSUS_CHANGELOG)
    changelog_response.raise_for_status()
    soup = bs(changelog_response.text, "html.parser")
    return soup.find("div", {"id": CHANGELOG_ID}).text


def get_base_log(from_filename=None):
    filename = from_filename or LAST_CHANGELOG
    with open(filename, "r") as f:
        base_log = f.read()
        return base_log


def store_change_log(newlog, to_filename=None):
    filename = to_filename or LAST_CHANGELOG
    with open(filename, "w") as f:
        f.write(newlog)


def get_lines(changelog):
    return [line.strip() for line in changelog.split("\n") if line]


def check_for_county_changes(email=None):
    """
    Check the census county changelog against a local copy of the last log
    to see whether updates have been added. If changes are detected,
    note the change and update our local 'last_changelog.txt' file.
    """
    current_changelog = get_current_log()
    current_lines = get_lines(current_changelog)
    base_lines = get_lines(get_base_log())
    if base_lines == current_lines:
        msg = "No county changes found, no emails sent."
        return msg
    else:
        msg = (
            "County changes need to be checked at {}\n"
            "These changes were detected:".format(CENSUS_CHANGELOG)
        )
        diffsets = []
        diffset = ndiff(base_lines, current_lines)
        diffsets.append(
            d for d in diffset if d.startswith("- ") or d.startswith("+ ")
        )
        for diffsett in diffsets:
            for diff in diffsett:
                msg += "\n{}".format(diff)
        store_change_log(current_changelog)
        msg += "\n\nOur 'last_changelog.txt' file has been updated."
        if email:
            send_mail(
                "Owning a Home alert: Change detected in census county data",
                msg,
                "tech@cfpb.gov",
                email,
                fail_silently=False,
            )

            return (
                "Emails were sent to {} with the following message: \n\n"
                "{}".format(", ".join(email), msg)
            )
        else:
            return msg
