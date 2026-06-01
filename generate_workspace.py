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
        "icon": "⬡",
        "title": "No verified building compliance record",
        "body": "Fire safety equipment, fall protection, and structural assets across {name} have never been systematically documented in a tamper-evident digital record. When an incident occurs, there is no pre-loss baseline.",
    },
    {
        "icon": "◈",
        "title": "No local career pathway in regulated trades",
        "body": "Young people in {county} who want to enter inspection, safety compliance, or regulated trades have no structured pathway into those roles that connects local employment with credentialled work.",
    },
    {
        "icon": "△",
        "title": "Institutional knowledge at retirement risk",
        "body": "The people who know where the records are, which buildings have outstanding issues, and how the informal compliance network works are within a decade of retirement. When they leave, that knowledge leaves too.",
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
            "icon": "◇",
            "title": "Haliburton County zoning data is fragmented across four municipalities",
            "body": f"Land use decisions in {name} depend on zoning records held separately by each of the four Haliburton County municipalities in inconsistent formats. No consolidated view exists.",
        })
    if "uranium" in known_for or "mining" in known_for:
        gaps.append({
            "icon": "◈",
            "title": "Historic extraction site records are incomplete",
            "body": f"Legacy mining operations in the {name} area produced infrastructure and environmental obligations that are inadequately documented in current municipal records.",
        })
    if county in ("Renfrew",):
        gaps.append({
            "icon": "◇",
            "title": "Ottawa Valley corridor compliance data doesn't cross municipal lines",
            "body": f"Contractors operating across Renfrew County townships — including {name} — have no unified record of which sites they've inspected, leaving gaps at every municipal boundary.",
        })
    if county in ("Frontenac",):
        gaps.append({
            "icon": "◇",
            "title": "County of Frontenac asset records are siloed by lower-tier municipality",
            "body": f"The Canadian Shield cottage economy in {name} generates significant seasonal infrastructure demand with no unified compliance baseline across the Frontenac municipalities.",
        })
    if county in ("Cochrane", "Kenora", "Thunder Bay"):
        gaps.append({
            "icon": "◇",
            "title": "Remote access and low inspector density create compliance blind spots",
            "body": f"{name}'s geographic isolation means inspection cycles are long and irregular. Assets go years between documented compliance checks with no digital record of the gap.",
        })
    if rurality == "COTTAGE":
        gaps.append({
            "icon": "◇",
            "title": "Seasonal population surge overwhelms year-round compliance infrastructure",
            "body": f"{name}'s permanent population of under 5,000 swells dramatically each summer. Fire safety and structural assets serving peak-season capacity have never been benchmarked against that load.",
        })
    if county in ("Nipissing", "Parry Sound", "Algoma"):
        gaps.append({
            "icon": "◇",
            "title": "Northern Ontario resource transition leaves compliance records orphaned",
            "body": f"As industrial employers in {county} have downsized or closed, the buildings and assets they maintained have passed to new operators — often without transferring the compliance history.",
        })

    return gaps[:2]  # cap at 2 specific gaps


def get_commons_tasks(m):
    """Return 3–4 commons task dicts for this municipality."""
    tasks = [
        {
            "number": "01",
            "title": "Register your first asset",
            "body": "Attach an NFC tag to any inspectable asset — fire extinguisher, fall arrest anchor, exit sign. Scan it with TapLog to create the first entry in {name}'s compliance record.",
        },
        {
            "number": "02",
            "title": "Map your building inventory",
            "body": "Upload a list of buildings under municipal jurisdiction. TapLog will generate a workspace asset map — the first complete picture of what exists and what doesn't have a compliance record yet.",
        },
        {
            "number": "03",
            "title": "Invite your first inspector",
            "body": "Add a certified inspector to your workspace. Every tap they complete in {name} becomes a verified, timestamped record tied to this address.",
        },
    ]

    county = m.get("county", "")
    known_for = m.get("known_for", "").lower()

    if "mining" in known_for or "uranium" in known_for:
        tasks.append({
            "number": "04",
            "title": "Flag legacy extraction sites",
            "body": "Mark historic mine sites, headframes, and industrial properties on the workspace map. Flag them for priority first inspection to establish a pre-development compliance baseline.",
        })
    elif county in ("Haliburton", "Frontenac", "Lennox and Addington"):
        tasks.append({
            "number": "04",
            "title": "Connect to the county workspace network",
            "body": f"Link your {county} workspace to adjacent municipalities. When a contractor inspects a building in your township, that record becomes visible to the next municipality they work in.",
        })
    elif county in ("Renfrew",):
        tasks.append({
            "number": "04",
            "title": "Activate the Algonquin corridor compliance link",
            "body": "Connect your workspace to the Ottawa Valley corridor network. Contractors and inspectors working between Renfrew County townships will have a single record that follows them.",
        })

    return [dict(t, body=t["body"].replace("{name}", m["name"])) for t in tasks]


# ---------------------------------------------------------------------------
# Community profile cards
# ---------------------------------------------------------------------------

def get_profile_cards(m):
    """Return 6 community profile card dicts."""
    pop = m["population"]
    county = m["county"]
    rurality = m["rurality"]
    known_for = m.get("known_for", "")

    rurality_label = {
        "RURAL": "Rural township",
        "REMOTE": "Remote community",
        "COTTAGE": "Cottage country",
    }.get(rurality, "Rural community")

    cards = [
        {"label": "Population", "value": f"{pop:,}", "sub": f"{county} County"},
        {"label": "Community type", "value": rurality_label, "sub": "Ontario classification"},
        {"label": "Known for", "value": known_for.split(",")[0].strip().title(), "sub": "Primary identity"},
        {"label": "Platform status", "value": "Workspace reserved", "sub": "Awaiting activation"},
        {"label": "Asset records", "value": "0 on file", "sub": "No compliance baseline"},
        {"label": "Inspector network", "value": "Not yet established", "sub": "Workspace dormant"},
    ]
    return cards


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

def render_gap(gap, name):
    body = gap["body"].replace("{name}", name)
    return f"""
        <div class="gap-item">
          <span class="gap-icon">{gap["icon"]}</span>
          <div class="gap-content">
            <div class="gap-title">{gap["title"]}</div>
            <div class="gap-body">{body}</div>
          </div>
        </div>"""


def render_task(task):
    return f"""
        <div class="task-item">
          <div class="task-number">{task["number"]}</div>
          <div class="task-content">
            <div class="task-title">{task["title"]}</div>
            <div class="task-body">{task["body"]}</div>
          </div>
        </div>"""


def render_profile_card(card):
    return f"""
          <div class="profile-card">
            <div class="profile-label">{card["label"]}</div>
            <div class="profile-value">{card["value"]}</div>
            <div class="profile-sub">{card["sub"]}</div>
          </div>"""


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
    mayor_name = m.get("mayor_name") or "—"
    cao_name = m.get("cao_name") or "—"
    cao_email = m.get("cao_email") or ""
    priority = m.get("priority", "P2")
    known_for = m.get("known_for", "")
    hold = m.get("hold", False)
    verify = m.get("verify", False)

    # Generate gaps
    all_gaps = UNIVERSAL_GAPS + get_specific_gaps(m)
    gaps_html = "".join(render_gap(g, name) for g in all_gaps)

    # Generate tasks
    tasks_html = "".join(render_task(t) for t in get_commons_tasks(m))

    # Generate profile cards
    cards_html = "".join(render_profile_card(c) for c in get_profile_cards(m))

    # Status badge
    if m.get("page_live"):
        status_badge = '<span class="badge badge-live">● live</span>'
        status_text = "active"
    elif hold:
        status_badge = '<span class="badge badge-hold">◌ hold</span>'
        status_text = "hold"
    elif verify:
        status_badge = '<span class="badge badge-verify">⚠ verify</span>'
        status_text = "verify"
    else:
        status_badge = '<span class="badge badge-dormant">○ dormant</span>'
        status_text = "dormant · awaiting activation"

    # CAO contact line
    if cao_email:
        cao_contact = f'<a href="mailto:{cao_email}" class="contact-link">{cao_email}</a>'
    else:
        cao_contact = "<span>Contact not yet researched</span>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Smallburg Workspace</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --amber: #c8a96e;
      --amber-dim: rgba(200, 169, 110, 0.15);
      --amber-mid: rgba(200, 169, 110, 0.35);
      --bg: #0d0d0b;
      --bg-card: #131310;
      --bg-card2: #171714;
      --text: #e8e4dc;
      --text-dim: #8a857a;
      --text-mid: #b5b0a5;
      --border: rgba(200, 169, 110, 0.18);
      --border-faint: rgba(255,255,255,0.06);
      --mono: 'DM Mono', monospace;
      --sans: 'DM Sans', sans-serif;
      --serif: 'Playfair Display', serif;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
      position: relative;
      overflow-x: hidden;
    }}

    /* Topographic grid background */
    body::before {{
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(200,169,110,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(200,169,110,0.04) 1px, transparent 1px),
        linear-gradient(rgba(200,169,110,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(200,169,110,0.015) 1px, transparent 1px);
      background-size: 240px 240px, 240px 240px, 48px 48px, 48px 48px;
      pointer-events: none;
      z-index: 0;
    }}

    body > * {{ position: relative; z-index: 1; }}

    /* ── NAV ── */
    nav {{
      border-bottom: 1px solid var(--border-faint);
      padding: 0 2rem;
      height: 52px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.02em;
      backdrop-filter: blur(8px);
      background: rgba(13,13,11,0.7);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .nav-left {{ display: flex; align-items: center; gap: 0.5rem; }}
    .nav-logo {{ color: var(--amber); font-weight: 500; }}
    .nav-sep {{ color: var(--text-dim); }}
    .nav-muni {{ color: var(--text); }}
    .nav-postal {{ color: var(--text-dim); }}
    .nav-right {{ display: flex; align-items: center; gap: 0.75rem; color: var(--text-dim); }}
    .nav-wsid {{ color: var(--amber); }}

    /* ── BADGES ── */
    .badge {{
      font-family: var(--mono);
      font-size: 0.65rem;
      padding: 2px 8px;
      border-radius: 2px;
      letter-spacing: 0.04em;
    }}
    .badge-dormant {{ background: rgba(138,133,122,0.15); color: var(--text-dim); border: 1px solid rgba(138,133,122,0.25); }}
    .badge-live {{ background: rgba(100,180,100,0.12); color: #7ec97e; border: 1px solid rgba(100,180,100,0.25); }}
    .badge-hold {{ background: rgba(200,169,110,0.1); color: var(--amber); border: 1px solid var(--border); }}
    .badge-verify {{ background: rgba(200,150,60,0.12); color: #d4924a; border: 1px solid rgba(200,150,60,0.25); }}

    /* ── HERO ── */
    .hero {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 4rem 2rem 2rem;
    }}
    .hero-eyebrow {{
      font-family: var(--mono);
      font-size: 0.7rem;
      color: var(--amber);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }}
    .hero-title {{
      font-family: var(--serif);
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 700;
      line-height: 1.1;
      margin-bottom: 0.5rem;
      color: var(--text);
    }}
    .hero-subtitle {{
      font-family: var(--mono);
      font-size: 0.78rem;
      color: var(--text-dim);
      margin-bottom: 2.5rem;
    }}
    .hero-subtitle span {{ color: var(--text-mid); }}

    /* ── STATS ROW ── */
    .stats-row {{
      display: flex;
      gap: 0;
      border: 1px solid var(--border);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 3rem;
    }}
    .stat {{
      flex: 1;
      padding: 1.25rem 1.5rem;
      border-right: 1px solid var(--border);
      background: var(--bg-card);
    }}
    .stat:last-child {{ border-right: none; }}
    .stat-label {{
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--text-dim);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.4rem;
    }}
    .stat-value {{
      font-family: var(--serif);
      font-size: 1.5rem;
      color: var(--amber);
      line-height: 1;
      margin-bottom: 0.25rem;
    }}
    .stat-sub {{
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--text-dim);
    }}

    /* ── CLAIM BLOCK ── */
    .claim-block {{
      border: 1px solid var(--border);
      background: var(--bg-card);
      border-radius: 4px;
      padding: 2rem;
      margin-bottom: 4rem;
    }}
    .claim-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 1rem;
      gap: 2rem;
    }}
    .claim-title {{
      font-family: var(--serif);
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 0.4rem;
    }}
    .claim-body {{
      font-size: 0.875rem;
      color: var(--text-dim);
      line-height: 1.6;
      max-width: 520px;
    }}
    .claim-form {{
      display: flex;
      gap: 0.75rem;
      margin-top: 1.5rem;
      flex-wrap: wrap;
    }}
    .claim-input {{
      background: rgba(0,0,0,0.4);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--mono);
      font-size: 0.8rem;
      padding: 0.6rem 1rem;
      border-radius: 3px;
      flex: 1;
      min-width: 220px;
      outline: none;
    }}
    .claim-input:focus {{ border-color: var(--amber); }}
    .claim-input::placeholder {{ color: var(--text-dim); }}
    .claim-btn {{
      background: var(--amber);
      color: #0d0d0b;
      border: none;
      font-family: var(--mono);
      font-size: 0.75rem;
      font-weight: 500;
      letter-spacing: 0.06em;
      padding: 0.6rem 1.5rem;
      border-radius: 3px;
      cursor: pointer;
      white-space: nowrap;
    }}
    .claim-btn:hover {{ background: #daba7e; }}
    .claim-gate-note {{
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--text-dim);
      margin-top: 0.75rem;
      letter-spacing: 0.03em;
    }}
    .claim-gate-note code {{
      color: var(--amber);
      background: var(--amber-dim);
      padding: 1px 5px;
      border-radius: 2px;
    }}

    /* ── SECTION HEADERS ── */
    .section {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 2rem;
      margin-bottom: 4rem;
    }}
    .section-header {{
      display: flex;
      align-items: baseline;
      gap: 1rem;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid var(--border-faint);
      padding-bottom: 0.75rem;
    }}
    .section-title {{
      font-family: var(--mono);
      font-size: 0.7rem;
      color: var(--amber);
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .section-rule {{
      flex: 1;
      height: 1px;
      background: var(--border-faint);
    }}
    .section-count {{
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--text-dim);
    }}

    /* ── PROFILE GRID ── */
    .profile-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1px;
      background: var(--border-faint);
      border: 1px solid var(--border-faint);
      border-radius: 4px;
      overflow: hidden;
    }}
    .profile-card {{
      background: var(--bg-card);
      padding: 1.25rem 1.5rem;
    }}
    .profile-label {{
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--text-dim);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.4rem;
    }}
    .profile-value {{
      font-size: 1rem;
      font-weight: 500;
      color: var(--text);
      margin-bottom: 0.25rem;
      line-height: 1.3;
    }}
    .profile-sub {{
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--text-dim);
    }}

    /* ── MODULE GRID ── */
    .module-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }}
    .module-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-faint);
      border-radius: 4px;
      padding: 1.5rem;
      position: relative;
      overflow: hidden;
    }}
    .module-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg, var(--amber) 0%, transparent 100%);
      opacity: 0.4;
    }}
    .module-icon {{
      font-size: 1.25rem;
      margin-bottom: 0.75rem;
      display: block;
    }}
    .module-name {{
      font-family: var(--mono);
      font-size: 0.72rem;
      color: var(--amber);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }}
    .module-desc {{
      font-size: 0.82rem;
      color: var(--text-dim);
      line-height: 1.55;
    }}
    .module-status {{
      display: inline-block;
      margin-top: 1rem;
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--text-dim);
      letter-spacing: 0.06em;
    }}

    /* ── GAPS ── */
    .gaps-list {{
      display: flex;
      flex-direction: column;
      gap: 0;
      border: 1px solid var(--border-faint);
      border-radius: 4px;
      overflow: hidden;
    }}
    .gap-item {{
      display: flex;
      gap: 1.5rem;
      padding: 1.5rem;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border-faint);
    }}
    .gap-item:last-child {{ border-bottom: none; }}
    .gap-icon {{
      font-size: 1rem;
      color: var(--amber);
      opacity: 0.7;
      flex-shrink: 0;
      margin-top: 2px;
      width: 1rem;
      text-align: center;
    }}
    .gap-title {{
      font-weight: 500;
      font-size: 0.9rem;
      color: var(--text);
      margin-bottom: 0.4rem;
    }}
    .gap-body {{
      font-size: 0.82rem;
      color: var(--text-dim);
      line-height: 1.6;
    }}

    /* ── COMMONS TASKS ── */
    .tasks-list {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}
    .task-item {{
      display: flex;
      gap: 1.5rem;
      padding: 1.5rem;
      background: var(--bg-card);
      border: 1px solid var(--border-faint);
      border-radius: 4px;
    }}
    .task-number {{
      font-family: var(--mono);
      font-size: 1.2rem;
      color: var(--amber);
      opacity: 0.5;
      flex-shrink: 0;
      width: 2rem;
      text-align: right;
      line-height: 1.3;
    }}
    .task-title {{
      font-weight: 500;
      font-size: 0.9rem;
      color: var(--text);
      margin-bottom: 0.4rem;
    }}
    .task-body {{
      font-size: 0.82rem;
      color: var(--text-dim);
      line-height: 1.6;
    }}

    /* ── CONTACT SECTION ── */
    .contact-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1px;
      background: var(--border-faint);
      border: 1px solid var(--border-faint);
      border-radius: 4px;
      overflow: hidden;
    }}
    .contact-card {{
      background: var(--bg-card);
      padding: 1.5rem;
    }}
    .contact-role {{
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--text-dim);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.4rem;
    }}
    .contact-name {{
      font-size: 1rem;
      font-weight: 500;
      color: var(--text);
      margin-bottom: 0.35rem;
    }}
    .contact-link {{
      font-family: var(--mono);
      font-size: 0.72rem;
      color: var(--amber);
      text-decoration: none;
    }}
    .contact-link:hover {{ text-decoration: underline; }}

    /* ── CTA FOOTER ── */
    .cta-section {{
      max-width: 1100px;
      margin: 0 auto 3rem;
      padding: 0 2rem;
    }}
    .cta-block {{
      background: var(--bg-card2);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 3rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 2rem;
    }}
    .cta-text {{ max-width: 520px; }}
    .cta-eyebrow {{
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--amber);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }}
    .cta-title {{
      font-family: var(--serif);
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 0.75rem;
    }}
    .cta-body {{
      font-size: 0.875rem;
      color: var(--text-dim);
      line-height: 1.6;
    }}
    .cta-actions {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      flex-shrink: 0;
    }}
    .cta-btn-primary {{
      background: var(--amber);
      color: #0d0d0b;
      border: none;
      font-family: var(--mono);
      font-size: 0.75rem;
      font-weight: 500;
      letter-spacing: 0.06em;
      padding: 0.75rem 2rem;
      border-radius: 3px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      text-align: center;
    }}
    .cta-btn-secondary {{
      background: transparent;
      color: var(--amber);
      border: 1px solid var(--border);
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.06em;
      padding: 0.65rem 2rem;
      border-radius: 3px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      text-align: center;
    }}
    .cta-btn-secondary:hover {{ background: var(--amber-dim); }}

    /* ── SITE FOOTER ── */
    footer {{
      border-top: 1px solid var(--border-faint);
      padding: 2rem;
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }}
    .footer-left {{
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--text-dim);
    }}
    .footer-left strong {{ color: var(--amber); }}
    .footer-right {{
      font-family: var(--mono);
      font-size: 0.65rem;
      color: var(--text-dim);
      text-align: right;
    }}

    /* ── RESPONSIVE ── */
    @media (max-width: 768px) {{
      .stats-row {{ flex-wrap: wrap; }}
      .stat {{ flex: 1 1 40%; }}
      .profile-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .module-grid {{ grid-template-columns: 1fr 1fr; }}
      .contact-grid {{ grid-template-columns: 1fr; }}
      .cta-block {{ flex-direction: column; }}
      .claim-header {{ flex-direction: column; }}
    }}
    @media (max-width: 500px) {{
      .module-grid {{ grid-template-columns: 1fr; }}
      .profile-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

  <!-- NAV -->
  <nav>
    <div class="nav-left">
      <a href="https://smallburg.ca" style="text-decoration:none;">
        <span class="nav-logo">smallburg.ca</span>
      </a>
      <span class="nav-sep">/</span>
      <span class="nav-muni">{name.lower()}</span>
      <span class="nav-sep">·</span>
      <span class="nav-postal">{postal}</span>
    </div>
    <div class="nav-right">
      <span class="nav-wsid">{workspace_id}</span>
      <span>·</span>
      <span>{status_text}</span>
      {status_badge}
    </div>
  </nav>

  <!-- HERO -->
  <div class="hero">
    <div class="hero-eyebrow">Smallburg workspace · {county} County · {priority}</div>
    <h1 class="hero-title">{name}</h1>
    <div class="hero-subtitle">
      <span>{coordinates}</span>
      &nbsp;·&nbsp;
      <span>pop. {population:,}</span>
      &nbsp;·&nbsp;
      <span>{website}</span>
    </div>

    <!-- STATS ROW -->
    <div class="stats-row">
      <div class="stat">
        <div class="stat-label">workspace id</div>
        <div class="stat-value">{workspace_id}</div>
        <div class="stat-sub">assigned · {county} County</div>
      </div>
      <div class="stat">
        <div class="stat-label">population</div>
        <div class="stat-value">{population:,}</div>
        <div class="stat-sub">permanent residents</div>
      </div>
      <div class="stat">
        <div class="stat-label">asset records</div>
        <div class="stat-value">0</div>
        <div class="stat-sub">no compliance baseline on file</div>
      </div>
      <div class="stat">
        <div class="stat-label">inspectors</div>
        <div class="stat-value">0</div>
        <div class="stat-sub">network not yet established</div>
      </div>
    </div>

    <!-- CLAIM BLOCK -->
    <div class="claim-block">
      <div class="claim-header">
        <div>
          <div class="claim-title">Claim this workspace</div>
          <div class="claim-body">
            This workspace is reserved for {name}. Municipal staff, CAO office, and authorized contractors
            can claim access using an official email address or postal code verification.
            Once claimed, the workspace becomes the compliance record of {name}.
          </div>
        </div>
        {status_badge}
      </div>
      <div class="claim-form">
        <input class="claim-input" type="email" placeholder="your.name{email_domain}">
        <button class="claim-btn" onclick="return false;">REQUEST ACCESS →</button>
      </div>
      <div class="claim-gate-note">
        Access gated on <code>{email_domain}</code> email domain · or verify with postal code
        <code>{postal_prefix}</code>
      </div>
    </div>
  </div>

  <!-- COMMUNITY PROFILE -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">Community profile</span>
      <div class="section-rule"></div>
      <span class="section-count">6 signals</span>
    </div>
    <div class="profile-grid">
{cards_html}
    </div>
  </div>

  <!-- MODULES -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">Platform modules</span>
      <div class="section-rule"></div>
      <span class="section-count">6 modules · dormant</span>
    </div>
    <div class="module-grid">
      <div class="module-card">
        <span class="module-icon">⬡</span>
        <div class="module-name">TapLog</div>
        <div class="module-desc">NFC-based asset inspection. Every fire extinguisher, fall anchor, and regulated asset gets a permanent tamper-evident compliance record.</div>
        <span class="module-status">● activate first</span>
      </div>
      <div class="module-card">
        <span class="module-icon">◈</span>
        <div class="module-name">Farpost</div>
        <div class="module-desc">Insurance claims dispatch. When a claim is filed at an address in {name}, the adjuster sees the full pre-loss asset record from TapLog.</div>
        <span class="module-status">○ requires TapLog data</span>
      </div>
      <div class="module-card">
        <span class="module-icon">△</span>
        <div class="module-name">Permit</div>
        <div class="module-desc">Construction lending verification. Before draw funds are released, the lender checks compliance status at the build address.</div>
        <span class="module-status">○ coming</span>
      </div>
      <div class="module-card">
        <span class="module-icon">◇</span>
        <div class="module-name">Roster</div>
        <div class="module-desc">Industrial workforce authorization. Workers check in via NFC. Safety managers see who's certified, on site, and authorized in real time.</div>
        <span class="module-status">○ coming</span>
      </div>
      <div class="module-card">
        <span class="module-icon">□</span>
        <div class="module-name">Ledger</div>
        <div class="module-desc">Property title and compliance history. When a property changes hands, the full asset record transfers with it as a permanent chain of custody.</div>
        <span class="module-status">○ coming</span>
      </div>
      <div class="module-card">
        <span class="module-icon">○</span>
        <div class="module-name">Signal</div>
        <div class="module-desc">Commercial insurance risk modelling. Underwriters see four years of asset-level compliance data when pricing policies in {county} County.</div>
        <span class="module-status">○ coming</span>
      </div>
    </div>
  </div>

  <!-- GAPS -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">Documented gaps</span>
      <div class="section-rule"></div>
      <span class="section-count">{len(all_gaps)} identified</span>
    </div>
    <div class="gaps-list">
{gaps_html}
    </div>
  </div>

  <!-- COMMONS TASKS -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">Commons tasks</span>
      <div class="section-rule"></div>
      <span class="section-count">first steps</span>
    </div>
    <div class="tasks-list">
{tasks_html}
    </div>
  </div>

  <!-- CONTACTS -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">Municipal contacts</span>
      <div class="section-rule"></div>
      <span class="section-count">on record</span>
    </div>
    <div class="contact-grid">
      <div class="contact-card">
        <div class="contact-role">{mayor_title}</div>
        <div class="contact-name">{mayor_name}</div>
        <div style="font-family: var(--mono); font-size: 0.72rem; color: var(--text-dim);">{name}</div>
      </div>
      <div class="contact-card">
        <div class="contact-role">Chief Administrative Officer</div>
        <div class="contact-name">{cao_name}</div>
        {cao_contact}
      </div>
    </div>
  </div>

  <!-- CTA -->
  <div class="cta-section">
    <div class="cta-block">
      <div class="cta-text">
        <div class="cta-eyebrow">Ready to activate</div>
        <div class="cta-title">Build {name}'s compliance record.</div>
        <div class="cta-body">
          Every tap an inspector makes in {name} becomes a permanent, tamper-evident record
          tied to this workspace. The first inspection is the hardest — after that, the data
          compounds. Four years from now, {name} has a complete asset history that no
          neighbouring municipality can match.
        </div>
      </div>
      <div class="cta-actions">
        <a href="mailto:{cao_email if cao_email else 'hello@smallburg.ca'}" class="cta-btn-primary">CONTACT CAO →</a>
        <a href="https://smallburg.ca" class="cta-btn-secondary">← all workspaces</a>
      </div>
    </div>
  </div>

  <!-- FOOTER -->
  <footer>
    <div class="footer-left">
      <strong>Smallburg</strong> · small town. big infrastructure. · smallburg.ca
    </div>
    <div class="footer-right">
      {workspace_id} · {name} · {county} County<br>
      <span style="opacity:0.5;">© 2026 Smallburg · Built near Bancroft, Ontario</span>
    </div>
  </footer>

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

    print(f"Generating {len(targets)} workspace page(s) → {args.output_dir}/w/[slug]/index.html\n")

    for m in targets:
        flag = ""
        if m.get("hold"):
            flag = "  ⚠ HOLD (see notes)"
        if m.get("verify"):
            flag = "  ⚠ VERIFY (municipality status unclear)"
        path = write_page(m, output_root=args.output_dir)
        print(f"  ✓  {m['workspace_id']}  {m['name']:<45} → {path}{flag}")

    print(f"\nDone. Upload {args.output_dir}/ folder to Cloudflare Pages.")
    print("Pages already live (skipped): bancroft, hastings-highlands, highlands-east")
    print("Use --include-live to regenerate those too.")
    print("\nNotes:")
    print("  • Dysart et al: HOLD until July (Mayor deceased May 29)")
    print("  • North Hastings: VERIFY — may not be a standalone municipality")


if __name__ == "__main__":
    main()
