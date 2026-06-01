#!/usr/bin/env python3
"""
Smallburg Workspace Page Generator
===================================
Generates smallburg.ca/w/[slug]/index.html workspace pages from municipality data.

Usage:
    python generate_workspace.py                    # generates all municipalities
    python generate_workspace.py --slug minden-hills  # generates one page
    python generate_workspace.py --dry-run           # prints first page to stdout

Output:
    smallburg-web/w/[slug]/index.html
"""

import os
import sys
import json
import argparse
from pathlib import Path
from textwrap import dedent

# ---------------------------------------------------------------------------
# Municipality data
# ---------------------------------------------------------------------------

# Workspace IDs: Bancroft=ws_0003, Hastings Highlands=ws_0015, Highlands East=ws_0022
# Remaining assigned sequentially in population order, skipping taken IDs.
# Population order: generate ws_0001 upward, reserve 0003/0015/0022.

def _assign_ids(municipalities):
    """Assign workspace IDs sequentially, skipping already-assigned ones."""
    taken = {"ws_0003", "ws_0015", "ws_0022"}
    counter = 1
    for m in municipalities:
        if m.get("workspace_id"):
            continue
        while True:
            candidate = f"ws_{counter:04d}"
            counter += 1
            if candidate not in taken:
                m["workspace_id"] = candidate
                break
    return municipalities


MUNICIPALITIES = _assign_ids([
    {
        "name": "Town of Kapuskasing",
        "slug": "kapuskasing",
        "type": "Town",
        "county": "Cochrane",
        "postal": "P5N 1A1",
        "postal_prefix": "P5N",
        "population": 8700,
        "email_domain": "@kapuskasing.ca",
        "website": "kapuskasing.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "49.4167° N · 82.4333° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Spruce Falls pulp mill heritage, planned community grid layout, Franco-Ontarian hub",
        "notes": "Far north Cochrane district. French-speaking majority.",
    },
    {
        "name": "Township of Muskoka Lakes",
        "slug": "muskoka-lakes",
        "type": "Township",
        "county": "Muskoka",
        "postal": "P0B 1M0",
        "postal_prefix": "P0B",
        "population": 6600,
        "email_domain": "@muskokalakes.ca",
        "website": "muskokalakes.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "45.1167° N · 79.6000° W",
        "priority": "P2",
        "rurality": "COTTAGE",
        "known_for": "Lake Rosseau, Lake Joseph, Windermere, cottage country, seasonal population spike",
        "notes": "Muskoka Lakes seasonal population 5x permanent. High-value real estate.",
    },
    {
        "name": "Municipality of Dysart et al",
        "slug": "dysart-et-al",
        "type": "Municipality",
        "county": "Haliburton",
        "postal": "K0M 1S0",
        "postal_prefix": "K0M",
        "population": 6000,
        "email_domain": "@dysartetal.ca",
        "website": "dysartetal.ca",
        "mayor_name": "Walt McKechnie (Acting Deputy Mayor)",
        "mayor_email": None,
        "cao_name": None,
        "cao_email": "info@dysartetal.ca",
        "coordinates": "45.0500° N · 78.5000° W",
        "priority": "P1",
        "rurality": "RURAL",
        "known_for": "County seat of Haliburton County, Haliburton Village, Haliburton Highlands",
        "notes": "HOLD until July 2026 — Mayor Murray Fearrey passed away May 29, 2026.",
        "hold": True,
    },
    {
        "name": "Municipality of Minden Hills",
        "slug": "minden-hills",
        "type": "Municipality",
        "county": "Haliburton",
        "postal": "K0M 2K0",
        "postal_prefix": "K0M",
        "population": 5700,
        "email_domain": "@mindenhills.ca",
        "website": "mindenhills.ca",
        "mayor_name": "Bob Carter",
        "mayor_email": "bcarter@mindenhills.ca",
        "cao_name": None,
        "cao_email": "admin@mindenhills.ca",
        "coordinates": "44.9333° N · 78.7333° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "County seat of Haliburton, Agnes Jamieson Gallery, Minden Hills Museum, Black River",
        "notes": "Strong Mayor powers May 2025. Active CivicWeb portal.",
    },
    {
        "name": "Town of Cochrane",
        "slug": "cochrane",
        "type": "Town",
        "county": "Cochrane",
        "postal": "P0L 1C0",
        "postal_prefix": "P0L",
        "population": 5500,
        "email_domain": "@cochraneontario.com",
        "website": "cochraneontario.com",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "49.0667° N · 81.0167° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Polar Bear Express railway terminus, Tim Hortons birthplace, Northern Ontario gateway",
        "notes": "Far north. Polar Bear Provincial Park nearby.",
    },
    {
        "name": "Municipality of Sioux Lookout",
        "slug": "sioux-lookout",
        "type": "Municipality",
        "county": "Kenora",
        "postal": "P8T 1A1",
        "postal_prefix": "P8T",
        "population": 5400,
        "email_domain": "@siouxlookout.ca",
        "website": "siouxlookout.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "50.0833° N · 91.9167° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Hub of the North, remote First Nations air transport hub, Lac Seul reservoir",
        "notes": "Northwestern Ontario. Gateway to 30+ remote First Nations communities.",
    },
    {
        "name": "Municipality of Central Frontenac",
        "slug": "central-frontenac",
        "type": "Municipality",
        "county": "Frontenac",
        "postal": "K0H 2B0",
        "postal_prefix": "K0H",
        "population": 5200,
        "email_domain": "@centralfrontenac.com",
        "website": "centralfrontenac.com",
        "mayor_name": "Frances Smith",
        "mayor_email": None,
        "cao_name": None,
        "cao_email": "info@centralfrontenac.com",
        "coordinates": "44.7333° N · 76.9167° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Canadian Shield cottage lakes, Sharbot Lake, Perth Road Village, mining heritage",
        "notes": "County of Frontenac. Strong cottage/seasonal economy.",
    },
    {
        "name": "Town of Espanola",
        "slug": "espanola",
        "type": "Town",
        "county": "Sudbury",
        "postal": "P5E 1S6",
        "postal_prefix": "P5E",
        "population": 5200,
        "email_domain": "@espanola.ca",
        "website": "espanola.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "46.2500° N · 81.7667° W",
        "priority": "P4",
        "rurality": "RURAL",
        "known_for": "Domtar pulp mill town, Spanish River, Manitoulin Island gateway",
        "notes": "Resource industry transition community. Bilingual.",
    },
    {
        "name": "Municipality of East Ferris",
        "slug": "east-ferris",
        "type": "Municipality",
        "county": "Nipissing",
        "postal": "P0H 1V0",
        "postal_prefix": "P0H",
        "population": 5000,
        "email_domain": "@eastferris.ca",
        "website": "eastferris.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "46.2833° N · 79.4000° W",
        "priority": "P3",
        "rurality": "RURAL",
        "known_for": "Nipissing district rural township, bedroom community to North Bay",
        "notes": "Adjacent to North Bay. Growing residential.",
    },
    {
        "name": "Town of Hearst",
        "slug": "hearst",
        "type": "Town",
        "county": "Cochrane",
        "postal": "P0L 1N0",
        "postal_prefix": "P0L",
        "population": 5000,
        "email_domain": "@hearst.ca",
        "website": "hearst.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "49.6833° N · 83.6667° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Moose capital of Canada, Franco-Ontarian culture, forestry industry",
        "notes": "Far north. French-speaking majority. Isolated.",
    },
    {
        "name": "City of Iroquois Falls",
        "slug": "iroquois-falls",
        "type": "City",
        "county": "Cochrane",
        "postal": "P0K 1G0",
        "postal_prefix": "P0K",
        "population": 4700,
        "email_domain": "@iroquoisfalls.ca",
        "website": "iroquoisfalls.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "48.7667° N · 80.6833° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Abitibi Canyon hydro dam, paper mill heritage, Iroquois Falls Museum",
        "notes": "Post-industrial. Significant population decline since mill closure.",
    },
    {
        "name": "Municipality of Greenstone",
        "slug": "greenstone",
        "type": "Municipality",
        "county": "Thunder Bay",
        "postal": "P0T 1V0",
        "postal_prefix": "P0T",
        "population": 4700,
        "email_domain": "@greenstone.ca",
        "website": "greenstone.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "49.7167° N · 87.3667° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Geraldton gold mining history, Trans-Canada Highway, Northwestern Ontario",
        "notes": "Thunder Bay district. Gold mining heritage. Very remote.",
    },
    {
        "name": "Township of Madawaska Valley",
        "slug": "madawaska-valley",
        "type": "Township",
        "county": "Renfrew",
        "postal": "K0J 1B0",
        "postal_prefix": "K0J",
        "population": 4500,
        "email_domain": "@madawaskavalley.ca",
        "website": "madawaskavalley.ca",
        "mayor_name": "Mark Willmer",
        "mayor_email": None,
        "cao_name": "Suzanne Klatt",
        "cao_email": "sklatt@madawaskavalley.ca",
        "coordinates": "45.5000° N · 77.6667° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Barry's Bay, Algonquin Park eastern gateway, Polish-Ukrainian heritage, Madawaska River",
        "notes": "Renfrew County. Strong Eastern European heritage community. Near Algonquin.",
    },
    {
        "name": "Municipality of Red Lake",
        "slug": "red-lake",
        "type": "Municipality",
        "county": "Kenora",
        "postal": "P0V 2M0",
        "postal_prefix": "P0V",
        "population": 4500,
        "email_domain": "@redlake.ca",
        "website": "redlake.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "51.0167° N · 93.8333° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Active gold mining operations, Red Lake Gold Rush 1926, First Nations territory",
        "notes": "Northwestern Ontario. Active gold mine. Fly-in community proximity.",
    },
    {
        "name": "Municipality of Hastings Highlands",
        "slug": "hastings-highlands",
        "type": "Municipality",
        "county": "Hastings",
        "postal": "K0L 1C0",
        "postal_prefix": "K0L",
        "population": 4400,
        "email_domain": "@hastingshighlands.ca",
        "website": "hastingshighlands.ca",
        "mayor_name": "Tony Fitzgerald",
        "mayor_email": None,
        "cao_name": "David Stewart",
        "cao_email": "david.stewart@hastingshighlands.ca",
        "coordinates": "45.2167° N · 77.9333° W",
        "priority": "P1",
        "rurality": "RURAL",
        "known_for": "Algonquin Park western corridor, Hastings Heritage Trail, granite Canadian Shield",
        "notes": "PAGE LIVE at smallburg.ca/w/hastings-highlands",
        "workspace_id": "ws_0015",
        "page_live": True,
    },
    {
        "name": "Municipality of North Hastings",
        "slug": "north-hastings",
        "type": "Municipality",
        "county": "Hastings",
        "postal": "K0L 1C0",
        "postal_prefix": "K0L",
        "population": 4200,
        "email_domain": "@northhastings.ca",
        "website": "northhastings.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "45.3000° N · 77.7000° W",
        "priority": "P1",
        "rurality": "RURAL",
        "known_for": "Bancroft area, uranium mining heritage, mineral collecting capital of Canada",
        "notes": "VERIFY — may not be a standalone municipality. Domain unresolved.",
        "verify": True,
    },
    {
        "name": "Municipality of Nipissing",
        "slug": "nipissing",
        "type": "Municipality",
        "county": "Nipissing",
        "postal": "P0H 1W0",
        "postal_prefix": "P0H",
        "population": 4200,
        "email_domain": "@municipalityofnipissing.ca",
        "website": "municipalityofnipissing.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "46.0167° N · 79.7333° W",
        "priority": "P3",
        "rurality": "RURAL",
        "known_for": "Lake Nipissing shoreline, French River corridor, Georgian Bay watershed",
        "notes": "Nipissing District. Cottage and recreation economy.",
    },
    {
        "name": "Town of Blind River",
        "slug": "blind-river",
        "type": "Town",
        "county": "Algoma",
        "postal": "P0R 1B0",
        "postal_prefix": "P0R",
        "population": 3800,
        "email_domain": "@blindriver.ca",
        "website": "blindriver.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "46.1833° N · 82.9667° W",
        "priority": "P4",
        "rurality": "REMOTE",
        "known_for": "Historic logging town, uranium refining (Cameco Blind River Refinery), Lake Huron North Shore",
        "notes": "Algoma District. Active uranium refinery. Highway 17 corridor.",
    },
    {
        "name": "Township of Lake of Bays",
        "slug": "lake-of-bays",
        "type": "Township",
        "county": "Muskoka",
        "postal": "P0A 1H0",
        "postal_prefix": "P0A",
        "population": 3700,
        "email_domain": "@lakeofbays.on.ca",
        "website": "lakeofbays.on.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "45.2833° N · 79.0500° W",
        "priority": "P3",
        "rurality": "COTTAGE",
        "known_for": "Dorset, Baysville, Lake of Bays, premium Muskoka cottage country, Dorset Lookout Tower",
        "notes": "Muskoka. Seasonal population overwhelms permanent. High property values.",
    },
    {
        "name": "Township of Bonnechere Valley",
        "slug": "bonnechere-valley",
        "type": "Township",
        "county": "Renfrew",
        "postal": "K0J 1T0",
        "postal_prefix": "K0J",
        "population": 3500,
        "email_domain": "@eganville.com",
        "website": "bonnecherevalleytwp.com",
        "mayor_name": "Jennifer Murphy",
        "mayor_email": None,
        "cao_name": "Annette Gilchrist",
        "cao_email": "annetteg@eganville.com",
        "coordinates": "45.5333° N · 77.1000° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Bonnechere River, Bonnechere Caves, Eganville village, Renfrew County limestone karst",
        "notes": "Mayor Murphy is vocal critic of Strong Mayor powers — approach thoughtfully.",
    },
    {
        "name": "Municipality of Powassan",
        "slug": "powassan",
        "type": "Municipality",
        "county": "Parry Sound",
        "postal": "P0H 1Z0",
        "postal_prefix": "P0H",
        "population": 3400,
        "email_domain": "@powassan.ca",
        "website": "powassan.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "46.0833° N · 79.3667° W",
        "priority": "P3",
        "rurality": "RURAL",
        "known_for": "Parry Sound District, South River watershed, Canadian Shield transition zone",
        "notes": "Parry Sound district. Small but growing.",
    },
    {
        "name": "Municipality of Highlands East",
        "slug": "highlands-east",
        "type": "Municipality",
        "county": "Haliburton",
        "postal": "K0L 2Y0",
        "postal_prefix": "K0L",
        "population": 2900,
        "email_domain": "@highlandseast.ca",
        "website": "highlandseast.ca",
        "mayor_name": "Dave Burton",
        "mayor_email": None,
        "cao_name": "Brittany McCaw",
        "cao_email": "bmccaw@highlandseast.ca",
        "coordinates": "45.0000° N · 78.1667° W",
        "priority": "P1",
        "rurality": "RURAL",
        "known_for": "Haliburton Highlands, Irondale, Wilberforce, mineral-rich Canadian Shield",
        "notes": "PAGE LIVE at smallburg.ca/w/highlands-east",
        "workspace_id": "ws_0022",
        "page_live": True,
    },
    {
        "name": "Municipality of Killaloe, Hagarty and Richards",
        "slug": "killaloe-hagarty-richards",
        "type": "Municipality",
        "county": "Renfrew",
        "postal": "K0J 2A0",
        "postal_prefix": "K0J",
        "population": 2700,
        "email_domain": "@khrtownship.ca",
        "website": "killaloe-hagarty-richards.ca",
        "mayor_name": "David Mayville",
        "mayor_email": None,
        "cao_name": None,
        "cao_email": "info@khrtownship.ca",
        "coordinates": "45.5500° N · 77.4167° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Killaloe village, Round Lake, Renfrew County rural heartland, Ottawa Valley",
        "notes": "Renfrew County. Small but well-organized.",
    },
    {
        "name": "Township of Algonquin Highlands",
        "slug": "algonquin-highlands",
        "type": "Township",
        "county": "Haliburton",
        "postal": "K0M 1J1",
        "postal_prefix": "K0M",
        "population": 2500,
        "email_domain": "@algonquinhighlands.ca",
        "website": "algonquinhighlands.ca",
        "mayor_name": "Liz Danielsen",
        "mayor_email": None,
        "cao_name": "Angie Bird",
        "cao_email": "abird@algonquinhighlands.ca",
        "coordinates": "45.2167° N · 78.6667° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Algonquin Park boundary, Dorset village, Lakes Kawagama and Halls Lake, Haliburton Highlands",
        "notes": "Haliburton County. Adjacent to Algonquin Park. Cottage and recreation economy.",
    },
    {
        "name": "Municipality of Addington Highlands",
        "slug": "addington-highlands",
        "type": "Municipality",
        "county": "Lennox and Addington",
        "postal": "K0H 1K0",
        "postal_prefix": "K0H",
        "population": 2500,
        "email_domain": "@addingtonhighlands.ca",
        "website": "addingtonhighlands.ca",
        "mayor_name": "Henry Hogg",
        "mayor_email": None,
        "cao_name": None,
        "cao_email": "info@addingtonhighlands.ca",
        "coordinates": "44.9667° N · 77.2167° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Kaladar, Northbrook, Mazinaw Lake, Bon Echo Provincial Park, Canadian Shield",
        "notes": "Uses 'Reeve' not 'Mayor' — Henry Hogg is Reeve. Lennox and Addington County.",
    },
    {
        "name": "Township of Georgian Bay",
        "slug": "georgian-bay",
        "type": "Township",
        "county": "Muskoka",
        "postal": "P0C 1H0",
        "postal_prefix": "P0C",
        "population": 2500,
        "email_domain": "@georgianbay.ca",
        "website": "georgianbay.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "44.8833° N · 79.7833° W",
        "priority": "P3",
        "rurality": "COTTAGE",
        "known_for": "Port Severn, Go Home Bay, Honey Harbour, Georgian Bay Islands National Park",
        "notes": "Muskoka. Highly seasonal. Cottage archipelago. Boating community.",
    },
    {
        "name": "Municipality of North Frontenac",
        "slug": "north-frontenac",
        "type": "Municipality",
        "county": "Frontenac",
        "postal": "K0H 2K0",
        "postal_prefix": "K0H",
        "population": 1900,
        "email_domain": "@northfrontenac.ca",
        "website": "northfrontenac.ca",
        "mayor_name": "Gerry Lichty",
        "mayor_email": None,
        "cao_name": None,
        "cao_email": "cao@northfrontenac.ca",
        "coordinates": "45.0333° N · 76.9667° W",
        "priority": "P2",
        "rurality": "RURAL",
        "known_for": "Plevna, Ompah, Canadian Shield lakes, County of Frontenac, Frontenac Arch Biosphere",
        "notes": "Mayor Gerry Lichty uses Gmail. cao@northfrontenac.ca is the working contact. Frontenac Arch UNESCO Biosphere Reserve.",
    },
])

# Also include the three live pages for completeness
MUNICIPALITIES_LIVE = [
    {
        "name": "Town of Bancroft",
        "slug": "bancroft",
        "type": "Town",
        "county": "Hastings",
        "postal": "K0L 1C0",
        "postal_prefix": "K0L",
        "population": 3900,
        "email_domain": "@town.bancroft.on.ca",
        "website": "town.bancroft.on.ca",
        "mayor_name": None,
        "mayor_email": None,
        "cao_name": None,
        "cao_email": None,
        "coordinates": "45.0547° N · 77.8573° W",
        "priority": "P1",
        "rurality": "RURAL",
        "known_for": "Mineral collecting capital of Canada, Bancroft Gem and Mineral Show, uranium mining heritage",
        "notes": "PAGE LIVE. Soft launch target: August 1, 2026 Gem and Mineral Show.",
        "workspace_id": "ws_0003",
        "page_live": True,
    },
]


# ---------------------------------------------------------------------------
# Gap generation logic
# ---------------------------------------------------------------------------

UNIVERSAL_GAPS = [
    {
        "title": "No verified building compliance record",
        "body": "Fire safety equipment, fall protection, and structural assets across {name} have never been systematically documented in a tamper-evident digital record. When an incident occurs, there is no pre-loss baseline.",
        "tag": "TapLog",
    },
    {
        "title": "No local career pathway in regulated trades",
        "body": "Young people in {county} who want to enter inspection, safety compliance, or regulated trades have no structured pathway into those roles that connects local employment with credentialled work.",
        "tag": "Commons · Muster",
    },
    {
        "title": "Institutional knowledge at retirement risk",
        "body": "The people who know where the records are, which buildings have outstanding issues, and how the informal compliance network works are within a decade of retirement. When they leave, that knowledge leaves too.",
        "tag": "Commons · Parcel",
    },
]


def get_specific_gaps(m):
    """Return 1–2 municipality-specific gap dicts based on county/rurality/known_for."""
    county = m.get("county", "")
    rurality = m.get("rurality", "")
    known_for = m.get("known_for", "").lower()
    name = m.get("name", "")
    gaps = []

    if county in ("Haliburton",):
        gaps.append({
            "title": "Haliburton County zoning data is fragmented across four municipalities",
            "body": f"Land use decisions in {name} depend on zoning records held separately by each of the four Haliburton County municipalities in inconsistent formats. No consolidated view exists.",
            "tag": "Parcel",
        })
    if "uranium" in known_for or "mining" in known_for:
        gaps.append({
            "title": "Historic extraction site records are incomplete",
            "body": f"Legacy mining operations in the {name} area produced infrastructure and environmental obligations that are inadequately documented in current municipal records.",
            "tag": "TapLog · Parcel",
        })
    if county in ("Renfrew",):
        gaps.append({
            "title": "Ottawa Valley corridor compliance data doesn't cross municipal lines",
            "body": f"Contractors operating across Renfrew County townships — including {name} — have no unified record of which sites they've inspected, leaving gaps at every municipal boundary.",
            "tag": "TapLog",
        })
    if county in ("Frontenac",):
        gaps.append({
            "title": "County of Frontenac asset records are siloed by lower-tier municipality",
            "body": f"The Canadian Shield cottage economy in {name} generates significant seasonal infrastructure demand with no unified compliance baseline across the Frontenac municipalities.",
            "tag": "TapLog · Parcel",
        })
    if county in ("Cochrane", "Kenora", "Thunder Bay"):
        gaps.append({
            "title": "Remote access and low inspector density create compliance blind spots",
            "body": f"{name}'s geographic isolation means inspection cycles are long and irregular. Assets go years between documented compliance checks with no digital record of the gap.",
            "tag": "TapLog",
        })
    if rurality == "COTTAGE":
        gaps.append({
            "title": "Seasonal population surge overwhelms year-round compliance infrastructure",
            "body": f"{name}'s permanent population of under 5,000 swells dramatically each summer. Fire safety and structural assets serving peak-season capacity have never been benchmarked against that load.",
            "tag": "TapLog",
        })
    if county in ("Nipissing", "Parry Sound", "Algoma"):
        gaps.append({
            "title": "Northern Ontario resource transition leaves compliance records orphaned",
            "body": f"As industrial employers in {county} have downsized or closed, the buildings and assets they maintained have passed to new operators — often without transferring the compliance history.",
            "tag": "TapLog · Farpost",
        })

    return gaps[:2]  # cap at 2 specific gaps


def get_commons_tasks(m):
    """Return 3–4 commons task dicts for this municipality."""
    tasks = [
        {
            "number": "01",
            "title": "Register your first asset",
            "body": "Attach an NFC tag to any inspectable asset — fire extinguisher, fall arrest anchor, exit sign. Scan it with TapLog to create the first entry in {name}'s compliance record.",
            "role": "DIG-FS",
        },
        {
            "number": "02",
            "title": "Map your building inventory",
            "body": "Upload a list of buildings under municipal jurisdiction. TapLog will generate a workspace asset map — the first complete picture of what exists and what doesn't have a compliance record yet.",
            "role": "DIG-GEN",
        },
        {
            "number": "03",
            "title": "Invite your first inspector",
            "body": "Add a certified inspector to your workspace. Every tap they complete in {name} becomes a verified, timestamped record tied to this address.",
            "role": "DIG-GEN",
        },
    ]

    county = m.get("county", "")
    known_for = m.get("known_for", "").lower()

    if "mining" in known_for or "uranium" in known_for:
        tasks.append({
            "number": "04",
            "title": "Flag legacy extraction sites",
            "body": "Mark historic mine sites, headframes, and industrial properties on the workspace map. Flag them for priority first inspection to establish a pre-development compliance baseline.",
            "role": "DIG-LU",
        })
    elif county in ("Haliburton", "Frontenac", "Lennox and Addington"):
        tasks.append({
            "number": "04",
            "title": "Connect to the county workspace network",
            "body": f"Link your {county} workspace to adjacent municipalities. When a contractor inspects a building in your township, that record becomes visible to the next municipality they work in.",
            "role": "DIG-GEN",
        })
    elif county in ("Renfrew",):
        tasks.append({
            "number": "04",
            "title": "Activate the Algonquin corridor compliance link",
            "body": "Connect your workspace to the Ottawa Valley corridor network. Contractors and inspectors working between Renfrew County townships will have a single record that follows them.",
            "role": "DIG-GEN",
        })

    return [dict(t, body=t["body"].replace("{name}", m["name"])) for t in tasks]


# ---------------------------------------------------------------------------
# Community profile cards
# ---------------------------------------------------------------------------

# Tag colours cycle through the Bancroft palette
TAG_COLORS = ["amber", "teal", "purple", "coral", "green", "teal"]

def get_profile_cards(m):
    """Return 6 community profile card dicts with tag/title/body matching Bancroft style."""
    pop = m["population"]
    county = m["county"]
    rurality = m["rurality"]
    known_for = m.get("known_for", "")
    name = m.get("name", "")
    notes = m.get("notes", "")

    rurality_desc = {
        "RURAL": "Rural municipality with a permanent year-round population. Service centre for surrounding townships.",
        "REMOTE": "Remote northern community. Geographic isolation shapes every aspect of service delivery and workforce.",
        "COTTAGE": "Seasonal cottage economy. Permanent population expands dramatically each summer with significant infrastructure implications.",
    }.get(rurality, "Rural Ontario community.")

    cards = [
        {
            "tag": "Economy",
            "color": "amber",
            "title": f"{county} County service community",
            "body": f"Population {pop:,} with a service catchment that extends well beyond municipal boundaries. {county} County context shapes the local economic base — trades, services, and seasonal activity.",
        },
        {
            "tag": "Known for",
            "color": "teal",
            "title": known_for.split(",")[0].strip(),
            "body": f"{known_for}.",
        },
        {
            "tag": "Community type",
            "color": "purple",
            "title": rurality.title().replace("_", " ") + " community",
            "body": rurality_desc,
        },
        {
            "tag": "Compliance",
            "color": "coral",
            "title": "No verified asset record on file",
            "body": f"Zero TapLog records exist for {name}. Fire safety assets, fall protection equipment, and regulated infrastructure have never been systematically documented in a tamper-evident digital system.",
        },
        {
            "tag": "Workforce",
            "color": "green",
            "title": "Inspector network not yet established",
            "body": f"No certified inspectors are connected to the {name} workspace. The compliance baseline cannot be built until the first inspector is onboarded and begins tagging assets.",
        },
        {
            "tag": "Region",
            "color": "teal",
            "title": f"Part of {county} County",
            "body": f"{name} operates within {county} County's administrative and service framework. Neighbouring municipalities share contractors, inspectors, and compliance obligations across municipal lines.",
        },
    ]
    return cards


# ---------------------------------------------------------------------------
# HTML render helpers
# ---------------------------------------------------------------------------

def render_profile_card(card):
    return f"""
      <div class="profile-card">
        <div class="profile-card-tag tag-{card['color']}">{card['tag']}</div>
        <h3>{card['title']}</h3>
        <p>{card['body']}</p>
      </div>"""


def render_gap(gap, name):
    body = gap["body"].replace("{name}", name)
    tag = gap.get("tag", "TapLog")
    return f"""
      <div class="gap-item">
        <div>
          <h4>{gap["title"]}</h4>
          <p>{body}</p>
        </div>
        <div class="gap-tag">{tag}</div>
      </div>"""


def render_task(task):
    role = task.get("role", "DIG-GEN")
    return f"""
      <div class="task">
        <div class="task-num">{task["number"]}</div>
        <div>
          <h4>{task["title"]}</h4>
          <p>{task["body"]}</p>
        </div>
        <div class="task-role">{role}</div>
      </div>"""


# ---------------------------------------------------------------------------
# HTML template — matches Bancroft design exactly
# ---------------------------------------------------------------------------

def generate_page(m):
    name = m["name"]
    slug = m["slug"]
    workspace_id = m.get("workspace_id", "ws_XXXX")
    county = m["county"]
    postal = m.get("postal", "")
    postal_prefix = m.get("postal_prefix", "")
    coordinates = m.get("coordinates", "")
    population = m.get("population", 0)
    email_domain = m.get("email_domain", "")
    website = m.get("website", "")
    mayor_title = "Reeve" if "reeve" in (m.get("notes") or "").lower() else "Mayor"
    mayor_name = m.get("mayor_name") or "not yet researched"
    cao_name = m.get("cao_name") or "not yet researched"
    cao_email = m.get("cao_email") or ""
    priority = m.get("priority", "P2")
    known_for = m.get("known_for", "")
    hold = m.get("hold", False)
    verify = m.get("verify", False)


    # Generate content
    all_gaps = UNIVERSAL_GAPS + get_specific_gaps(m)
    gaps_html = "".join(render_gap(g, name) for g in all_gaps)
    tasks_html = "".join(render_task(t) for t in get_commons_tasks(m))
    cards_html = "".join(render_profile_card(c) for c in get_profile_cards(m))

    # Nav status
    if m.get("page_live"):
        nav_status = f"workspace {workspace_id} · active"
    elif hold:
        nav_status = f"workspace {workspace_id} · hold"
    elif verify:
        nav_status = f"workspace {workspace_id} · verify"
    else:
        nav_status = f"workspace {workspace_id} · dormant · awaiting activation"

    # Hero desc — build from known_for and county
    name_short = name.replace("Municipality of ", "").replace("Township of ", "").replace("Town of ", "").replace("City of ", "")
    hero_desc = f"{known_for.split(',')[0].strip()}. {county} County. Population {population:,} — this workspace was built for you before you arrived. It knows your community. It's waiting to be activated."

    # Claim block postal note
    postal_note = f"Residents and community workers can join with a personal email and postal code <strong>{postal}</strong>."

    # CTA email
    cta_email = cao_email if cao_email else "hello@smallburg.ca"
    cta_subject = f"{name_short} workspace — early access request"

    # Gap section heading — vary by county
    if county in ("Cochrane", "Kenora", "Thunder Bay"):
        gap_heading = f"What {name_short} needs<br><em>right now.</em>"
    elif county in ("Haliburton", "Frontenac", "Lennox and Addington"):
        gap_heading = f"The gaps this platform<br><em>was built to close.</em>"
    else:
        gap_heading = f"What {name_short} is missing<br><em>and why it matters.</em>"

    # Module color classes matching Bancroft
    module_colors = ["teal", "amber", "purple", "coral", "coral", "gray"]
    module_statuses = [
        ("Ready to connect", "status-ready"),
        ("Dormant", "status-dormant"),
        ("Dormant", "status-dormant"),
        ("Coming soon", "status-dormant"),
        ("Coming soon", "status-dormant"),
        ("Coming soon", "status-dormant"),
    ]

    # Name split for h1: "Town of\nBancroft" style
    name_parts = name.split(" ", 2)
    if len(name_parts) >= 3:
        h1_top = " ".join(name_parts[:2])
        h1_em = name_parts[2]
    else:
        h1_top = ""
        h1_em = name

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — Smallburg Workspace</title>
<meta name="description" content="Smallburg community workspace for {name}, Ontario. Pre-built infrastructure for local compliance, workforce, and community services.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">
<style>
  :root {{
    --ground: #0f0e0b;
    --ground-2: #181610;
    --ground-3: #221f18;
    --line: #2e2b22;
    --line-2: #3d3928;
    --warm: #c8a96e;
    --warm-dim: #7a6540;
    --warm-bright: #e8c887;
    --text: #e8e4d8;
    --text-dim: #8a8474;
    --text-muted: #4a4640;
    --teal: #4a9e82;
    --teal-dim: #2a5e4e;
    --purple: #7a6eb8;
    --purple-dim: #3d3770;
    --coral: #c06848;
    --coral-dim: #6b3520;
    --amber: #c89040;
    --amber-dim: #7a5518;
    --green: #5a9e48;
    --green-dim: #2d5422;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}

  body {{
    background: var(--ground);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
    line-height: 1.7;
    overflow-x: hidden;
  }}

  body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--line) 1px, transparent 1px),
      linear-gradient(90deg, var(--line) 1px, transparent 1px);
    background-size: 48px 48px;
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
  }}

  body::after {{
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--line-2) 1px, transparent 1px),
      linear-gradient(90deg, var(--line-2) 1px, transparent 1px);
    background-size: 240px 240px;
    opacity: 0.45;
    pointer-events: none;
    z-index: 0;
  }}

  .wrap {{
    position: relative;
    z-index: 1;
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 2rem;
  }}

  nav {{
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 100;
    border-bottom: 1px solid var(--line-2);
    background: rgba(15,14,11,0.94);
    backdrop-filter: blur(8px);
  }}
  nav .wrap {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 52px;
  }}
  .nav-left {{ display: flex; align-items: center; gap: 1rem; }}
  .wordmark {{
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.08em;
    color: var(--warm);
    text-decoration: none;
  }}
  .wordmark span {{ color: var(--text-muted); font-weight: 300; }}
  .nav-sep {{ color: var(--text-muted); font-size: 12px; }}
  .nav-workspace {{
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.06em;
  }}
  .nav-right {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 0.08em;
  }}

  .hero {{
    padding: 100px 0 60px;
    border-bottom: 1px solid var(--line-2);
  }}
  .hero-inner {{
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 4rem;
    align-items: start;
  }}
  @media (max-width: 760px) {{ .hero-inner {{ grid-template-columns: 1fr; }} }}

  .hero-label {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--warm-dim);
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }}
  .hero-label::before {{
    content: '';
    display: block;
    width: 24px;
    height: 1px;
    background: var(--warm-dim);
  }}

  h1 {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 400;
    line-height: 1.1;
    color: var(--text);
    margin-bottom: 1rem;
  }}
  h1 em {{ font-style: italic; color: var(--warm); }}

  .hero-desc {{
    font-size: 1rem;
    color: var(--text-dim);
    max-width: 520px;
    line-height: 1.8;
    margin-bottom: 2rem;
  }}

  .claim-block {{
    background: var(--ground-2);
    border: 1px solid var(--warm-dim);
    padding: 1.75rem;
  }}
  .claim-block-label {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--warm-dim);
    margin-bottom: 1rem;
  }}
  .claim-block p {{
    font-size: 0.9rem;
    color: var(--text-dim);
    line-height: 1.7;
    margin-bottom: 1.25rem;
  }}
  .claim-block p strong {{ color: var(--text); font-weight: 400; }}
  .claim-input {{
    width: 100%;
    background: var(--ground);
    border: 1px solid var(--line-2);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    padding: 0.6rem 0.75rem;
    margin-bottom: 0.75rem;
    outline: none;
    transition: border-color 0.2s;
  }}
  .claim-input::placeholder {{ color: var(--text-muted); }}
  .claim-input:focus {{ border-color: var(--warm-dim); }}
  .claim-btn {{
    width: 100%;
    background: var(--warm);
    color: var(--ground);
    border: none;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.75rem;
    cursor: pointer;
    transition: background 0.2s;
  }}
  .claim-btn:hover {{ background: var(--warm-bright); }}
  .claim-note {{
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.75rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.04em;
  }}

  .stats-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    border: 1px solid var(--line-2);
    margin: 2.5rem 0 0;
  }}
  @media (max-width: 600px) {{ .stats-row {{ grid-template-columns: 1fr 1fr; }} }}
  .stat {{
    background: var(--ground-2);
    padding: 1.25rem 1rem;
    border-right: 1px solid var(--line-2);
  }}
  .stat-value {{
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: var(--warm);
    line-height: 1;
    margin-bottom: 0.3rem;
  }}
  .stat-label {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
  }}

  section {{ padding: 56px 0; border-bottom: 1px solid var(--line-2); }}
  .section-label {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }}
  .section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--line-2);
    max-width: 80px;
  }}
  h2 {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.5rem, 3vw, 2.2rem);
    font-weight: 400;
    line-height: 1.2;
    color: var(--text);
    margin-bottom: 1rem;
  }}
  h2 em {{ font-style: italic; color: var(--warm); }}

  .profile-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px;
    margin-top: 2rem;
  }}
  @media (max-width: 600px) {{ .profile-grid {{ grid-template-columns: 1fr; }} }}
  .profile-card {{
    background: var(--ground-2);
    border: 1px solid var(--line-2);
    padding: 1.5rem;
  }}
  .profile-card-tag {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }}
  .profile-card h3 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 400;
    color: var(--text);
    margin-bottom: 0.75rem;
  }}
  .profile-card p {{
    font-size: 0.875rem;
    color: var(--text-dim);
    line-height: 1.7;
  }}
  .tag-teal {{ color: var(--teal); }}
  .tag-coral {{ color: var(--coral); }}
  .tag-amber {{ color: var(--amber); }}
  .tag-purple {{ color: var(--purple); }}
  .tag-green {{ color: var(--green); }}

  .module-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2px;
    margin-top: 2rem;
  }}
  @media (max-width: 760px) {{ .module-grid {{ grid-template-columns: 1fr; }} }}
  .module {{
    background: var(--ground-2);
    border: 1px solid var(--line-2);
    padding: 1.75rem 1.5rem;
    position: relative;
    transition: background 0.2s;
  }}
  .module:hover {{ background: var(--ground-3); }}
  .module-status {{
    position: absolute;
    top: 1rem; right: 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.2rem 0.5rem;
    border: 1px solid;
  }}
  .status-dormant {{ color: var(--text-muted); border-color: var(--text-muted); opacity: 0.5; }}
  .status-ready {{ color: var(--teal); border-color: var(--teal-dim); }}
  .module-icon {{
    font-size: 1.4rem;
    margin-bottom: 0.75rem;
    font-family: 'DM Mono', monospace;
    color: var(--text-muted);
  }}
  .module h3 {{
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 400;
    color: var(--text);
    margin-bottom: 0.4rem;
  }}
  .module-sub {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
  }}
  .module p {{ font-size: 0.85rem; color: var(--text-dim); line-height: 1.65; }}
  .module-action {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 1rem;
    cursor: pointer;
    border: none;
    background: none;
    padding: 0;
  }}
  .module-teal {{ border-top: 2px solid var(--teal-dim); }}
  .module-teal .module-sub, .module-teal .module-action {{ color: var(--teal); }}
  .module-amber {{ border-top: 2px solid var(--amber-dim); }}
  .module-amber .module-sub, .module-amber .module-action {{ color: var(--amber); }}
  .module-purple {{ border-top: 2px solid var(--purple-dim); }}
  .module-purple .module-sub, .module-purple .module-action {{ color: var(--purple); }}
  .module-coral {{ border-top: 2px solid var(--coral-dim); }}
  .module-coral .module-sub, .module-coral .module-action {{ color: var(--coral); }}
  .module-gray {{ border-top: 2px solid var(--line-2); }}
  .module-gray .module-sub, .module-gray .module-action {{ color: var(--text-muted); }}
  .module.dormant {{ opacity: 0.6; }}
  .module.dormant:hover {{ opacity: 0.8; }}

  .gap-list {{
    margin-top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .gap-item {{
    background: var(--ground-2);
    border: 1px solid var(--line-2);
    border-left: 3px solid var(--coral-dim);
    padding: 1rem 1.25rem;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 1rem;
    align-items: center;
  }}
  .gap-item h4 {{
    font-size: 0.9rem;
    font-weight: 400;
    color: var(--text);
    margin-bottom: 0.2rem;
  }}
  .gap-item p {{ font-size: 0.8rem; color: var(--text-dim); }}
  .gap-tag {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--teal);
    border: 1px solid var(--teal-dim);
    padding: 0.2rem 0.5rem;
    white-space: nowrap;
  }}

  .task-list {{
    margin-top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .task {{
    background: var(--ground-2);
    border: 1px solid var(--line-2);
    padding: 1rem 1.25rem;
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 1rem;
    align-items: center;
  }}
  .task-num {{
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--warm-dim);
    min-width: 24px;
  }}
  .task h4 {{
    font-size: 0.875rem;
    font-weight: 400;
    color: var(--text);
    margin-bottom: 0.15rem;
  }}
  .task p {{ font-size: 0.78rem; color: var(--text-dim); }}
  .task-role {{
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    white-space: nowrap;
  }}

  footer {{ border-top: 1px solid var(--line-2); padding: 2.5rem 0; }}
  .footer-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }}
  .footer-left {{
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.8;
  }}
  .footer-left a {{ color: var(--warm-dim); text-decoration: none; }}
  .footer-left a:hover {{ color: var(--warm); }}
  .footer-right {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: var(--text-muted);
    text-align: right;
  }}

  @media (prefers-reduced-motion: no-preference) {{
    .fade-up {{
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.6s ease, transform 0.6s ease;
    }}
    .fade-up.visible {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
</head>
<body>

<nav>
  <div class="wrap">
    <div class="nav-left">
      <a class="wordmark" href="https://smallburg.ca">smallburg<span>.ca</span></a>
      <span class="nav-sep">/</span>
      <span class="nav-workspace">{slug} · {postal.lower()}</span>
    </div>
    <div class="nav-right">{nav_status}</div>
  </div>
</nav>

<div class="wrap">

  <!-- Hero -->
  <section class="hero" style="border-bottom:none; padding-bottom:40px">
    <div class="hero-inner">
      <div>
        <div class="hero-label fade-up">Smallburg community workspace</div>
        <h1 class="fade-up">{h1_top}<br><em>{h1_em}</em></h1>
        <p class="hero-desc fade-up">{hero_desc}</p>

        <div class="stats-row fade-up">
          <div class="stat">
            <div class="stat-value">{population:,}</div>
            <div class="stat-label">Population</div>
          </div>
          <div class="stat">
            <div class="stat-value">0</div>
            <div class="stat-label">Asset records</div>
          </div>
          <div class="stat">
            <div class="stat-value">0</div>
            <div class="stat-label">Inspectors</div>
          </div>
          <div class="stat">
            <div class="stat-value">{workspace_id}</div>
            <div class="stat-label">Workspace ID</div>
          </div>
        </div>
      </div>

      <div class="fade-up">
        <div class="claim-block">
          <div class="claim-block-label">Activate this workspace</div>
          <p>This workspace is reserved for <strong>{name}</strong> staff and community members. Sign in with your <strong>{email_domain}</strong> email address to activate it.</p>
          <p>{postal_note}</p>
          <input class="claim-input" type="email" placeholder="your@{website} or personal email">
          <input class="claim-input" type="text" placeholder="Postal code (residents only)">
          <button class="claim-btn" onclick="this.textContent='Request sent — we\\'ll be in touch'; this.style.background='var(--teal)'">Request early access →</button>
          <div class="claim-note">hello@smallburg.ca · smallburg.ca · Maynooth, ON K0L 2S0</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Community profile -->
  <section>
    <div class="section-label">Community profile</div>
    <h2>What we already know<br><em>about {name_short}.</em></h2>
    <p style="color:var(--text-dim); font-size:0.95rem; max-width:580px; margin-bottom:0">This profile was built from public data before anyone from {name_short} signed up. It updates as your community data grows.</p>

    <div class="profile-grid fade-up">
{cards_html}
    </div>
  </section>

  <!-- Platform modules -->
  <section>
    <div class="section-label">Platform modules</div>
    <h2>Six things this workspace<br><em>is ready to do.</em></h2>
    <p style="color:var(--text-dim); font-size:0.95rem; max-width:580px; margin-bottom:0">Each module activates independently. Start with one. The rest are waiting.</p>

    <div class="module-grid fade-up">

      <div class="module module-teal">
        <div class="module-status status-ready">Ready to connect</div>
        <div class="module-icon">01</div>
        <h3>TapLog</h3>
        <div class="module-sub">Built environment</div>
        <p>Fire safety, fall protection, and regulated trades inspection for every asset in {name}. NFC-tagged, inspection-logged, compliance-tracked. Pre-loss records surface automatically in insurance claims.</p>
        <button class="module-action">Connect TapLog →</button>
      </div>

      <div class="module module-amber">
        <div class="module-status status-dormant">Dormant</div>
        <div class="module-icon">02</div>
        <h3>The Commons</h3>
        <div class="module-sub">Knowledge work marketplace</div>
        <p>Post local knowledge capture work. {name_short} residents get paid to digitize variance records, verify municipal data, and maintain community datasets. The money stays local. The knowledge stays too.</p>
        <button class="module-action">Activate Commons →</button>
      </div>

      <div class="module module-purple">
        <div class="module-status status-dormant">Dormant</div>
        <div class="module-icon">03</div>
        <h3>Muster</h3>
        <div class="module-sub">Local workforce registry</div>
        <p>Retired planners. Local tradespeople. People who know {name_short} and have had no economic vehicle for that knowledge — until now. Muster is their registry.</p>
        <button class="module-action">Build your Muster →</button>
      </div>

      <div class="module module-coral dormant">
        <div class="module-status status-dormant">Coming soon</div>
        <div class="module-icon">04</div>
        <h3>Farpost</h3>
        <div class="module-sub">Insurance claims dispatch</div>
        <p>When a claim is filed for a {name_short} property, the adjuster sees the pre-loss TapLog inspection history automatically. Every compliant asset on record. Every open deficiency flagged.</p>
        <button class="module-action" style="opacity:0.4; cursor:default">Coming soon</button>
      </div>

      <div class="module module-coral dormant">
        <div class="module-status status-dormant">Coming soon</div>
        <div class="module-icon">05</div>
        <h3>Parcel</h3>
        <div class="module-sub">Land record dataset</div>
        <p>Zoning history. Variances. Easements. Environmental constraints. The land record knowledge that lives in {county} County filing cabinets — digitized, structured, and queryable by civic address.</p>
        <button class="module-action" style="opacity:0.4; cursor:default">Coming soon</button>
      </div>

      <div class="module module-gray dormant">
        <div class="module-status status-dormant">Coming soon</div>
        <div class="module-icon">06</div>
        <h3>Ledger</h3>
        <div class="module-sub">Property compliance history</div>
        <p>When a property changes hands in {name_short}, the full TapLog and Parcel record transfers with it. The buyer knows what they're getting. The history doesn't disappear.</p>
        <button class="module-action" style="opacity:0.4; cursor:default">Coming soon</button>
      </div>

    </div>
  </section>

  <!-- Gaps -->
  <section>
    <div class="section-label">What {name_short} is starving for</div>
    <h2>{gap_heading}</h2>

    <div class="gap-list fade-up">
{gaps_html}
    </div>
  </section>

  <!-- First tasks -->
  <section>
    <div class="section-label">First Commons tasks</div>
    <h2>Work that exists<br><em>right now.</em></h2>
    <p style="color:var(--text-dim); font-size:0.95rem; max-width:580px; margin-bottom:0">These tasks are waiting in the {name_short} Commons queue. They pay. They build something real. They stay local.</p>

    <div class="task-list fade-up">
{tasks_html}
    </div>
  </section>

  <!-- Footer CTA -->
  <section style="border-bottom:none">
    <div class="section-label">Activate this workspace</div>
    <h2>{name_short} has been<br><em>waiting for this.</em></h2>
    <p style="color:var(--text-dim); font-size:0.95rem; max-width:560px; margin-bottom:2rem">This workspace was built before you arrived. The community profile is pre-populated. The Commons queue has work waiting. The modules are ready to activate. All it takes is someone with a {email_domain} email address — or a {postal_prefix} postal code — to claim it.</p>
    <a href="mailto:{cta_email}?subject={cta_subject}" style="display:inline-flex; align-items:center; gap:0.5rem; font-family:'DM Mono',monospace; font-size:11px; letter-spacing:0.12em; text-transform:uppercase; color:var(--warm); border:1px solid var(--warm-dim); padding:0.75rem 1.5rem; text-decoration:none; transition:all 0.2s">{cta_email} →</a>
  </section>

</div>

<footer>
  <div class="wrap">
    <div class="footer-inner">
      <div class="footer-left">
        <a href="https://smallburg.ca">smallburg.ca</a> · {workspace_id} · {name} · {postal}<br>
        Built in Maynooth, Ontario · <a href="mailto:hello@smallburg.ca">hello@smallburg.ca</a>
      </div>
      <div class="footer-right">
        Small town. Big infrastructure.<br>
        {coordinates}
      </div>
    </div>
  </div>
</footer>

<script>
  const obs = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
  }}, {{ threshold: 0.08 }});
  document.querySelectorAll('.fade-up').forEach(el => obs.observe(el));
</script>

</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_page(m, output_root="smallburg-web"):
    slug = m["slug"]
    out_dir = Path(output_root) / "w" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(generate_page(m), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate Smallburg workspace pages")
    parser.add_argument("--slug", help="Generate only this slug")
    parser.add_argument("--dry-run", action="store_true", help="Print first page to stdout, no files written")
    parser.add_argument("--output-dir", default="smallburg-web", help="Root output directory (default: smallburg-web)")
    parser.add_argument("--include-live", action="store_true", help="Also regenerate already-live pages")
    args = parser.parse_args()

    all_munis = MUNICIPALITIES
    if args.include_live:
        all_munis = MUNICIPALITIES_LIVE + MUNICIPALITIES

    if args.dry_run:
        print(generate_page(all_munis[0]))
        return

    if args.slug:
        targets = [m for m in all_munis if m["slug"] == args.slug]
        if not targets:
            print(f"ERROR: slug '{args.slug}' not found.")
            sys.exit(1)
    else:
        targets = [m for m in all_munis if not m.get("page_live")]

    print(f"Generating {len(targets)} workspace page(s) -> {args.output_dir}/w/[slug]/index.html\n")

    for m in targets:
        flag = ""
        if m.get("hold"):
            flag = "  ⚠ HOLD (see notes)"
        if m.get("verify"):
            flag = "  ⚠ VERIFY (municipality status unclear)"
        path = write_page(m, output_root=args.output_dir)
        print(f"  ok  {m['workspace_id']}  {m['name']:<45} -> {path}{flag}")

    print(f"\nDone. Upload {args.output_dir}/ folder to Cloudflare Pages.")
    print("Pages already live (skipped): bancroft, hastings-highlands, highlands-east")
    print("Use --include-live to regenerate those too.")
    print("\nNotes:")
    print("  * Dysart et al: HOLD until July (Mayor deceased May 29)")
    print("  * North Hastings: VERIFY -- may not be a standalone municipality")


if __name__ == "__main__":
    main()
