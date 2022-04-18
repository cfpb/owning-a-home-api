from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from countylimits.models import CountyLimit


# A static allowlist of abbreviations and FIPS codes
SAFE_STATE_LIST = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "AS",
    "GU",
    "MP",
    "PR",
    "VI",
    "01",
    "02",
    "04",
    "05",
    "06",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "53",
    "54",
    "55",
    "56",
    "60",
    "66",
    "69",
    "72",
    "78",
]


@api_view(["GET"])
def county_limits(request):
    """Return all counties with their limits per state."""
    if request.method == "GET":
        package = {"request": {}, "data": []}
        if "state" in request.GET:
            state = request.GET["state"]
            if state in SAFE_STATE_LIST:
                data = CountyLimit.county_limits_by_state(state)
                package["request"]["state"] = state
                package["data"] = data
                return Response(package)
            else:
                return Response(
                    {"state": "Invalid state"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"detail": "Required parameter state is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
