from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from xml.etree import ElementTree

import httpx

from app.config import (
    APPLE_CALDAV_BASE_URL,
    APPLE_CALDAV_CALENDAR_NAME,
    APPLE_CALDAV_PASSWORD,
    APPLE_CALDAV_USERNAME,
)
from app.services.calendar_import import parse_ics_events


DAV = "DAV:"
CALDAV = "urn:ietf:params:xml:ns:caldav"
NS = {"d": DAV, "c": CALDAV}


class AppleCalDAVConfigError(RuntimeError):
    pass


async def fetch_apple_calendar_events(calendar_url: str | None = None) -> list[dict]:
    if not APPLE_CALDAV_USERNAME or not APPLE_CALDAV_PASSWORD:
        raise AppleCalDAVConfigError(
            "Missing APPLE_CALDAV_USERNAME or APPLE_CALDAV_PASSWORD in backend/.env"
        )

    auth = (APPLE_CALDAV_USERNAME, APPLE_CALDAV_PASSWORD)
    async with httpx.AsyncClient(timeout=30, auth=auth, follow_redirects=True) as client:
        target_calendar_url = calendar_url or await _discover_calendar_url(client)
        raw_calendars = await _calendar_query(client, target_calendar_url)

    events: list[dict] = []
    for raw_ics in raw_calendars:
        events.extend(parse_ics_events(raw_ics))
    for event in events:
        event["source"] = "apple_caldav"
    return events


async def discover_apple_calendars() -> list[dict]:
    if not APPLE_CALDAV_USERNAME or not APPLE_CALDAV_PASSWORD:
        raise AppleCalDAVConfigError(
            "Missing APPLE_CALDAV_USERNAME or APPLE_CALDAV_PASSWORD in backend/.env"
        )

    auth = (APPLE_CALDAV_USERNAME, APPLE_CALDAV_PASSWORD)
    async with httpx.AsyncClient(timeout=30, auth=auth, follow_redirects=True) as client:
        principal_url = await _current_user_principal(client)
        home_url = await _calendar_home_set(client, principal_url)
        return await _list_calendars(client, home_url)


async def _discover_calendar_url(client: httpx.AsyncClient) -> str:
    principal_url = await _current_user_principal(client)
    home_url = await _calendar_home_set(client, principal_url)
    calendars = await _list_calendars(client, home_url)
    if not calendars:
        raise AppleCalDAVConfigError("No Apple calendars were discovered through CalDAV.")

    if APPLE_CALDAV_CALENDAR_NAME:
        wanted = APPLE_CALDAV_CALENDAR_NAME.lower()
        for calendar in calendars:
            if calendar["name"].lower() == wanted:
                return calendar["url"]
        raise AppleCalDAVConfigError(
            f"Calendar named '{APPLE_CALDAV_CALENDAR_NAME}' was not found."
        )

    return calendars[0]["url"]


async def _current_user_principal(client: httpx.AsyncClient) -> str:
    body = """
    <d:propfind xmlns:d="DAV:">
      <d:prop><d:current-user-principal /></d:prop>
    </d:propfind>
    """
    root = await _propfind(client, APPLE_CALDAV_BASE_URL, body, "0")
    href = root.find(".//d:current-user-principal/d:href", NS)
    if href is None or not href.text:
        raise AppleCalDAVConfigError("Could not discover Apple CalDAV principal URL.")
    return _absolute_url(href.text)


async def _calendar_home_set(client: httpx.AsyncClient, principal_url: str) -> str:
    body = """
    <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop><c:calendar-home-set /></d:prop>
    </d:propfind>
    """
    root = await _propfind(client, principal_url, body, "0")
    href = root.find(".//c:calendar-home-set/d:href", NS)
    if href is None or not href.text:
        raise AppleCalDAVConfigError("Could not discover Apple calendar home set.")
    return _absolute_url(href.text)


async def _list_calendars(client: httpx.AsyncClient, home_url: str) -> list[dict]:
    body = """
    <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop>
        <d:displayname />
        <d:resourcetype />
      </d:prop>
    </d:propfind>
    """
    root = await _propfind(client, home_url, body, "1")
    calendars: list[dict] = []
    for response in root.findall("d:response", NS):
        resource_type = response.find(".//d:resourcetype", NS)
        if resource_type is None or resource_type.find("c:calendar", NS) is None:
            continue
        href = response.find("d:href", NS)
        display_name = response.find(".//d:displayname", NS)
        if href is None or not href.text:
            continue
        calendars.append(
            {
                "name": display_name.text if display_name is not None and display_name.text else "Calendar",
                "url": _absolute_url(href.text),
            }
        )
    return calendars


async def _calendar_query(client: httpx.AsyncClient, calendar_url: str) -> list[str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).strftime("%Y%m%dT%H%M%SZ")
    end = (now + timedelta(days=180)).strftime("%Y%m%dT%H%M%SZ")
    body = f"""
    <c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop>
        <d:getetag />
        <c:calendar-data />
      </d:prop>
      <c:filter>
        <c:comp-filter name="VCALENDAR">
          <c:comp-filter name="VEVENT">
            <c:time-range start="{start}" end="{end}" />
          </c:comp-filter>
        </c:comp-filter>
      </c:filter>
    </c:calendar-query>
    """
    response = await client.request(
        "REPORT",
        calendar_url,
        headers={"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
        content=body.strip(),
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)
    return [
        node.text
        for node in root.findall(".//c:calendar-data", NS)
        if node.text
    ]


async def _propfind(
    client: httpx.AsyncClient,
    url: str,
    body: str,
    depth: str,
) -> ElementTree.Element:
    response = await client.request(
        "PROPFIND",
        url,
        headers={"Depth": depth, "Content-Type": "application/xml; charset=utf-8"},
        content=body.strip(),
    )
    response.raise_for_status()
    return ElementTree.fromstring(response.text)


def _absolute_url(value: str) -> str:
    if value.startswith("http"):
        return value
    return urljoin(APPLE_CALDAV_BASE_URL, value)
