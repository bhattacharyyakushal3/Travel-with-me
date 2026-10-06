# ============================================================
# INDIA TOURIST PLANNER - BACKEND
# FAST SERVER SEARCH + PERSISTENT LOCAL CACHE
# ============================================================
#
# Put this file in the SAME folder as app.py
#
# Project structure:
#
#   YourProject/
#       app.py
#       backend.py
#
# The program will automatically create:
#
#       YourProject/
#           tourist_cache/
#               destinations.json
#
# You DO NOT need to create the cache folder manually.
#
# ============================================================

import json
import math
import re
import time
from pathlib import Path

import requests


# ============================================================
# 1. SERVER SETTINGS
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {
    "User-Agent": (
        "IndiaTouristPlanner/2.0 "
        "(Tourist Planning Application)"
    )
}


# ============================================================
# 2. HTTP SESSION
# ============================================================
#
# A Session reuses the internet connection and is faster than
# creating a new connection for every request.
#

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# 3. LOCAL CACHE SETTINGS
# ============================================================

CACHE_FOLDER = (
    Path(__file__).resolve().parent
    / "tourist_cache"
)

CACHE_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

CACHE_FILE = (
    CACHE_FOLDER
    / "destinations.json"
)

# Cached information remains valid for 30 days.
CACHE_DAYS = 30

CACHE_SECONDS = (
    CACHE_DAYS
    * 24
    * 60
    * 60
)

# In-memory cache.
# This makes repeated searches during the same program run
# extremely fast.
CACHE = {}


# ============================================================
# 4. LOAD CACHE WHEN BACKEND STARTS
# ============================================================

def load_cache():

    global CACHE

    if not CACHE_FILE.exists():
        CACHE = {}
        return

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            CACHE = data
        else:
            CACHE = {}

    except Exception as error:

        print(
            "Cache loading error:",
            error
        )

        CACHE = {}


# Load saved destinations immediately.
load_cache()


# ============================================================
# 5. SAVE CACHE
# ============================================================

def save_cache():

    temporary_file = (
        CACHE_FOLDER
        / "destinations.tmp"
    )

    try:

        with open(
            temporary_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                CACHE,
                file,
                indent=2,
                ensure_ascii=False
            )

        # Replace old cache safely.
        temporary_file.replace(
            CACHE_FILE
        )

    except Exception as error:

        print(
            "Cache saving error:",
            error
        )


# ============================================================
# 6. NORMALIZE DESTINATION NAME
# ============================================================

def normalize_destination(
    destination
):

    destination = str(
        destination or ""
    ).strip().lower()

    destination = re.sub(
        r"\s+",
        " ",
        destination
    )

    return destination


# ============================================================
# 7. CHECK WHETHER CACHE IS STILL VALID
# ============================================================

def cache_is_valid(
    cache_item
):

    if not cache_item:
        return False

    try:

        saved_time = float(
            cache_item.get(
                "saved_time",
                0
            )
        )

        age = (
            time.time()
            - saved_time
        )

        return age <= CACHE_SECONDS

    except Exception:

        return False


# ============================================================
# 8. HAVERSINE DISTANCE
# ============================================================
#
# Calculates distance between two latitude/longitude points.
#

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    earth_radius = 6371.0

    lat1 = math.radians(
        float(lat1)
    )

    lon1 = math.radians(
        float(lon1)
    )

    lat2 = math.radians(
        float(lat2)
    )

    lon2 = math.radians(
        float(lon2)
    )

    difference_latitude = (
        lat2 - lat1
    )

    difference_longitude = (
        lon2 - lon1
    )

    value = (
        math.sin(
            difference_latitude / 2
        ) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(
            difference_longitude / 2
        ) ** 2
    )

    distance = (
        2
        * earth_radius
        * math.asin(
            math.sqrt(value)
        )
    )

    return distance


# ============================================================
# 9. FIND DESTINATION COORDINATES
# ============================================================

def get_coordinates(
    destination
):

    destination = str(
        destination or ""
    ).strip()

    if not destination:
        return None

    key = normalize_destination(
        destination
    )

    # --------------------------------------------------------
    # FIRST: CHECK LOCAL CACHE
    # --------------------------------------------------------

    cached = CACHE.get(key)

    if (
        cached
        and cached.get("coordinates")
        and cache_is_valid(cached)
    ):

        print(
            "Coordinates loaded from cache:",
            destination
        )

        return cached["coordinates"]

    # --------------------------------------------------------
    # ONLINE SEARCH
    # --------------------------------------------------------

    search_queries = [
        f"{destination}, India",
        destination
    ]

    for query_text in search_queries:

        parameters = {
            "q": query_text,
            "format": "json",
            "limit": 5,
            "addressdetails": 1,
            "countrycodes": "in"
        }

        try:

            response = SESSION.get(
                NOMINATIM_URL,
                params=parameters,
                timeout=8
            )

            response.raise_for_status()

            results = response.json()

            if not results:
                continue

            # ------------------------------------------------
            # Find the most relevant result.
            # ------------------------------------------------

            requested_words = set(
                re.findall(
                    r"[a-z0-9]+",
                    destination.lower()
                )
            )

            best_result = None
            best_score = -1

            for result in results:

                display_name = str(
                    result.get(
                        "display_name",
                        ""
                    )
                ).lower()

                result_name = str(
                    result.get(
                        "name",
                        ""
                    )
                ).lower()

                combined_text = (
                    display_name
                    + " "
                    + result_name
                )

                score = 0

                for word in requested_words:

                    if word in combined_text:
                        score += 1

                # Prefer named locations.
                if result.get("name"):
                    score += 0.5

                if score > best_score:

                    best_score = score
                    best_result = result

            if best_result is None:
                continue

            # ------------------------------------------------
            # Convert coordinates.
            # ------------------------------------------------

            latitude = float(
                best_result["lat"]
            )

            longitude = float(
                best_result["lon"]
            )

            address = best_result.get(
                "address",
                {}
            )

            state = (
                address.get("state")
                or address.get(
                    "state_district"
                )
                or address.get(
                    "region"
                )
                or "India"
            )

            coordinates = {

                "latitude": latitude,

                "longitude": longitude,

                "state": state,

                "display_name": best_result.get(
                    "display_name",
                    destination
                )
            }

            # ------------------------------------------------
            # Save coordinates locally.
            # ------------------------------------------------

            old_data = CACHE.get(
                key,
                {}
            )

            CACHE[key] = {

                "saved_time": time.time(),

                "coordinates": coordinates,

                "places": old_data.get(
                    "places",
                    []
                )
            }

            save_cache()

            return coordinates

        except requests.exceptions.Timeout:

            print(
                "Geocoding timeout:",
                query_text
            )

        except requests.exceptions.RequestException as error:

            print(
                "Geocoding server error:",
                error
            )

        except Exception as error:

            print(
                "Geocoding processing error:",
                error
            )

    return None


# ============================================================
# 10. SEND QUERY TO OVERPASS
# ============================================================

def get_overpass_data(
    query
):

    # --------------------------------------------------------
    # Try each server.
    #
    # Connection timeout = 4 seconds
    # Read timeout       = 15 seconds
    #
    # This prevents the old 60-second waiting problem.
    # --------------------------------------------------------

    for server in OVERPASS_SERVERS:

        print(
            "Trying:",
            server
        )

        try:

            response = SESSION.post(

                server,

                data=query,

                timeout=(
                    4,
                    15
                )
            )

            if response.status_code == 200:

                return response.json()

            print(
                "Server status:",
                response.status_code
            )

        except requests.exceptions.Timeout:

            print(
                "Server timeout:",
                server
            )

        except requests.exceptions.RequestException as error:

            print(
                "Server connection error:",
                error
            )

        except Exception as error:

            print(
                "Unexpected server error:",
                error
            )

    return None


# ============================================================
# 11. GET TOURIST PLACES
# ============================================================

def get_tourist_places(
    destination,
    latitude,
    longitude
):

    key = normalize_destination(
        destination
    )

    # --------------------------------------------------------
    # FIRST: CHECK LOCAL CACHE
    # --------------------------------------------------------

    cached = CACHE.get(key)

    if (
        cached
        and cached.get("places")
        and cache_is_valid(cached)
    ):

        print(
            "Tourist places loaded from cache:",
            destination
        )

        return cached["places"]

    # --------------------------------------------------------
    # FIRST ONLINE SEARCH
    #
    # 8 km radius
    # --------------------------------------------------------

    radius = 8000

    query = f"""
[out:json][timeout:12];

(
  nwr["tourism"~"attraction|museum|gallery|viewpoint"]
    (around:{radius},{latitude},{longitude});

  nwr["historic"]
    (around:{radius},{latitude},{longitude});

  nwr["leisure"="park"]
    (around:{radius},{latitude},{longitude});

  nwr["natural"~"peak|water|beach|cave"]
    (around:{radius},{latitude},{longitude});
);

out center tags;
"""

    data = get_overpass_data(
        query
    )

    # --------------------------------------------------------
    # SECOND SEARCH ONLY IF REQUIRED
    #
    # Expand to 15 km.
    # --------------------------------------------------------

    if (
        data is None
        or not data.get("elements")
    ):

        print(
            "No nearby attractions found."
        )

        print(
            "Trying wider search..."
        )

        radius = 15000

        query = f"""
[out:json][timeout:12];

(
  nwr["tourism"~"attraction|museum|gallery|viewpoint"]
    (around:{radius},{latitude},{longitude});

  nwr["historic"]
    (around:{radius},{latitude},{longitude});

  nwr["leisure"="park"]
    (around:{radius},{latitude},{longitude});

  nwr["natural"~"peak|water|beach|cave"]
    (around:{radius},{latitude},{longitude});
);

out center tags;
"""

        data = get_overpass_data(
            query
        )

    if not data:

        print(
            "No Overpass data received."
        )

        return []

    elements = data.get(
        "elements",
        []
    )

    places = []

    used_names = set()

    # ========================================================
    # PROCESS EACH TOURIST PLACE
    # ========================================================

    for element in elements:

        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )

        if not name:
            continue

        name_key = normalize_destination(
            name
        )

        if name_key in used_names:
            continue

        used_names.add(
            name_key
        )

        # ----------------------------------------------------
        # Get attraction coordinates.
        # ----------------------------------------------------

        place_lat = element.get(
            "lat"
        )

        place_lon = element.get(
            "lon"
        )

        center = element.get(
            "center",
            {}
        )

        if place_lat is None:

            place_lat = center.get(
                "lat"
            )

        if place_lon is None:

            place_lon = center.get(
                "lon"
            )

        if (
            place_lat is None
            or place_lon is None
        ):
            continue

        try:

            place_lat = float(
                place_lat
            )

            place_lon = float(
                place_lon
            )

        except Exception:

            continue

        # ----------------------------------------------------
        # Distance from destination.
        # ----------------------------------------------------

        distance = calculate_distance_km(
            latitude,
            longitude,
            place_lat,
            place_lon
        )

        # ----------------------------------------------------
        # Determine category.
        # ----------------------------------------------------

        tourism_type = tags.get(
            "tourism",
            ""
        )

        historic_type = tags.get(
            "historic",
            ""
        )

        leisure_type = tags.get(
            "leisure",
            ""
        )

        natural_type = tags.get(
            "natural",
            ""
        )

        # ----------------------------------------------------
        # Activity.
        # ----------------------------------------------------

        if tourism_type == "museum":

            activity = (
                "Visit museum and explore "
                "local history and culture"
            )

        elif tourism_type == "gallery":

            activity = (
                "Explore art and cultural exhibitions"
            )

        elif tourism_type == "viewpoint":

            activity = (
                "Enjoy panoramic sightseeing "
                "and photography"
            )

        elif historic_type:

            activity = (
                "Explore historical and cultural heritage"
            )

        elif leisure_type == "park":

            activity = (
                "Nature walk, relaxation and sightseeing"
            )

        elif natural_type == "peak":

            activity = (
                "Mountain sightseeing and photography"
            )

        elif natural_type in (
            "water",
            "beach",
            "cave"
        ):

            activity = (
                "Nature sightseeing and photography"
            )

        else:

            activity = (
                "Sightseeing and photography"
            )

        # ----------------------------------------------------
        # Suggested duration.
        # ----------------------------------------------------

        if tourism_type == "museum":

            duration = "2–3 hours"

        elif tourism_type == "gallery":

            duration = "1–2 hours"

        elif leisure_type == "park":

            duration = "1–2 hours"

        elif natural_type:

            duration = "2–4 hours"

        else:

            duration = "1–3 hours"

        # ----------------------------------------------------
        # Entry fee.
        #
        # We do NOT invent ticket prices.
        # ----------------------------------------------------

        fee = str(
            tags.get(
                "fee",
                ""
            )
        ).lower()

        if fee in (
            "no",
            "false",
            "0"
        ):

            entry_cost = 0

        else:

            entry_cost = 0

        # ----------------------------------------------------
        # Save attraction.
        # ----------------------------------------------------

        places.append({

            "name": name,

            "activity": activity,

            "duration": duration,

            "entry_cost": entry_cost,

            "latitude": place_lat,

            "longitude": place_lon,

            "distance_km": round(
                distance,
                2
            )
        })

    # ========================================================
    # SORT BY DISTANCE
    # ========================================================

    places.sort(
        key=lambda item:
        item.get(
            "distance_km",
            999999
        )
    )

    # Maximum 20 attractions.
    places = places[:20]

    # ========================================================
    # SAVE TO LOCAL CACHE
    # ========================================================

    old_data = CACHE.get(
        key,
        {}
    )

    CACHE[key] = {

        "saved_time": time.time(),

        "coordinates": old_data.get(
            "coordinates"
        ),

        "places": places
    }

    save_cache()

    print(
        "Saved tourist places to cache:",
        destination
    )

    return places


# ============================================================
# ============================================================
# 12. GET NEARBY ACCOMMODATION WITH CONTACT DETAILS
# ============================================================

def _element_coordinates(element):
    """Return latitude/longitude from an Overpass node/way/relation."""
    lat = element.get("lat")
    lon = element.get("lon")
    center = element.get("center") or {}

    if lat is None:
        lat = center.get("lat")
    if lon is None:
        lon = center.get("lon")

    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def _contact_from_tags(tags):
    """Extract real contact information; never invent a phone number."""
    phone = (
        tags.get("phone")
        or tags.get("contact:phone")
        or tags.get("mobile")
        or tags.get("contact:mobile")
        or ""
    ).strip()

    website = (
        tags.get("website")
        or tags.get("contact:website")
        or tags.get("url")
        or ""
    ).strip()

    email = (
        tags.get("email")
        or tags.get("contact:email")
        or ""
    ).strip()

    if phone:
        primary = phone
        contact_type = "Phone"
    elif website:
        primary = website
        contact_type = "Website"
    elif email:
        primary = email
        contact_type = "Email"
    else:
        primary = ""
        contact_type = "No direct contact listed"

    return {
        "phone": phone,
        "website": website,
        "email": email,
        "contact": primary,
        "contact_type": contact_type,
        "contact_available": bool(phone or website or email),
    }


def get_accommodations(destination, latitude, longitude):
    """
    Find at least three nearby hotels/guest houses/home-stay type
    accommodations whenever OpenStreetMap contains them.

    Results are ranked so entries with a real phone/website/email come
    first, then by distance. Data are cached with the destination.
    """
    key = normalize_destination(destination)
    cached = CACHE.get(key, {})

    if (
        cached
        and cached.get("accommodations")
        and cache_is_valid(cached)
    ):
        print("Accommodation loaded from cache:", destination)
        return cached["accommodations"]

    # Search in two stages:
    # 1) accommodation with explicit contact data
    # 2) accommodation without contact data if fewer than 3 were found
    radii = [8000, 15000]
    accommodation_types = (
        "hotel|guest_house|hostel|motel|chalet|"
        "apartment|camp_site|alpine_hut"
    )

    contact_queries = [
        '["phone"]',
        '["contact:phone"]',
        '["website"]',
        '["contact:website"]',
        '["email"]',
        '["contact:email"]',
    ]

    elements = []
    seen_ids = set()

    def run_accommodation_query(radius, contact_filter=""):
        query = f"""
[out:json][timeout:12];
(
  nwr["tourism"~"{accommodation_types}"]{contact_filter}
    (around:{radius},{latitude},{longitude});
);
out center tags;
"""
        return get_overpass_data(query)

    # Prefer accommodation records having real contact information.
    for radius in radii:
        for contact_filter in contact_queries:
            data = run_accommodation_query(radius, contact_filter)
            for element in (data or {}).get("elements", []):
                element_id = (
                    element.get("type", ""),
                    element.get("id", "")
                )
                if element_id not in seen_ids:
                    seen_ids.add(element_id)
                    elements.append(element)

            if len(elements) >= 8:
                break

        if len(elements) >= 8:
            break

    # If OSM has fewer than 3 contact-bearing entries, supplement with
    # ordinary accommodation records. We never manufacture contact data.
    if len(elements) < 3:
        for radius in radii:
            data = run_accommodation_query(radius)
            for element in (data or {}).get("elements", []):
                element_id = (
                    element.get("type", ""),
                    element.get("id", "")
                )
                if element_id not in seen_ids:
                    seen_ids.add(element_id)
                    elements.append(element)
            if len(elements) >= 12:
                break

    accommodations = []
    used_names = set()

    for element in elements:
        tags = element.get("tags") or {}
        name = (tags.get("name") or "").strip()

        if not name:
            continue

        name_key = normalize_destination(name)
        if name_key in used_names:
            continue
        used_names.add(name_key)

        lat, lon = _element_coordinates(element)
        if lat is None or lon is None:
            continue

        distance = calculate_distance_km(
            latitude, longitude, lat, lon
        )

        tourism_type = tags.get("tourism", "").strip().lower()

        if tourism_type == "guest_house":
            property_type = "Guest House"
        elif tourism_type == "hotel":
            property_type = "Hotel"
        elif tourism_type == "hostel":
            property_type = "Hostel"
        elif tourism_type == "motel":
            property_type = "Motel"
        elif tourism_type == "chalet":
            property_type = "Chalet / Home Stay"
        elif tourism_type == "apartment":
            property_type = "Apartment / Home Stay"
        elif tourism_type == "camp_site":
            property_type = "Camp Site"
        elif tourism_type == "alpine_hut":
            property_type = "Mountain Hut"
        else:
            property_type = "Accommodation"

        contact = _contact_from_tags(tags)

        address_parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
            tags.get("addr:suburb", ""),
            tags.get("addr:city", ""),
            tags.get("addr:postcode", ""),
        ]
        address = ", ".join(
            part.strip()
            for part in address_parts
            if str(part).strip()
        )

        accommodations.append({
            "name": name,
            "type": property_type,
            "phone": contact["phone"],
            "website": contact["website"],
            "email": contact["email"],
            "contact": contact["contact"],
            "contact_type": contact["contact_type"],
            "contact_available": contact["contact_available"],
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "distance_km": round(distance, 2),
        })

    # Contact-bearing entries first, then nearest.
    accommodations.sort(
        key=lambda item: (
            not item["contact_available"],
            item.get("distance_km", 999999),
        )
    )

    # Keep a useful shortlist. The first three should be the best
    # contact-bearing choices whenever OSM provides at least three.
    accommodations = accommodations[:10]

    old_data = CACHE.get(key, {})
    CACHE[key] = {
        "saved_time": time.time(),
        "coordinates": old_data.get("coordinates"),
        "places": old_data.get("places", []),
        "accommodations": accommodations,
    }
    save_cache()

    print(
        "Saved accommodations:",
        destination,
        "|",
        len(accommodations)
    )

    return accommodations


# ============================================================
# 13. DESTINATION DESCRIPTION
# ============================================================

def generate_description(destination, state):
    return (
        f"{destination} is a tourist destination in {state}, India. "
        "Tourist attractions and nearby accommodation information "
        "are obtained from online geographic data and cached locally "
        "for faster future searches."
    )


# ============================================================
# 14. GET COMPLETE DESTINATION
# ============================================================

def get_destination(destination):
    destination = str(destination or "").strip()

    if not destination:
        return None

    key = normalize_destination(destination)
    cached = CACHE.get(key)

    if (
        cached
        and cached.get("coordinates")
        and cached.get("places")
        and cached.get("accommodations")
        and cache_is_valid(cached)
    ):
        print("CACHE HIT:", destination)
        return build_destination_data(
            destination,
            cached["coordinates"],
            cached["places"],
            cached["accommodations"],
        )

    print("CACHE MISS:", destination)

    coordinates = get_coordinates(destination)

    if coordinates is None:
        print("Destination could not be located.")
        return None

    places = get_tourist_places(
        destination,
        coordinates["latitude"],
        coordinates["longitude"]
    )

    accommodations = get_accommodations(
        destination,
        coordinates["latitude"],
        coordinates["longitude"]
    )

    destination_data = build_destination_data(
        destination,
        coordinates,
        places,
        accommodations,
    )

    CACHE[key] = {
        "saved_time": time.time(),
        "coordinates": coordinates,
        "places": places,
        "accommodations": accommodations,
    }
    save_cache()

    return destination_data


# ============================================================
# 15. BUILD DESTINATION DATA
# ============================================================

def build_destination_data(
    destination,
    coordinates,
    places,
    accommodations=None,
):
    accommodations = accommodations or []

    number_of_places = len(places)

    if number_of_places <= 3:
        recommended_days = 1
    elif number_of_places <= 6:
        recommended_days = 2
    elif number_of_places <= 10:
        recommended_days = 3
    else:
        recommended_days = 4

    return {
        "name": destination,
        "state": coordinates["state"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "description": generate_description(
            destination,
            coordinates["state"]
        ),
        "recommended_days": recommended_days,
        "places": places,
        "accommodations": accommodations,
        "tips": [
            "Check local weather conditions before travelling.",
            "Confirm attraction opening hours before visiting.",
            "Carry a valid identity document.",
            "Confirm ticket prices with the attraction before visiting.",
            "Travel time may vary because of traffic and local conditions.",
            "Confirm hotel/guest-house availability and contact details before booking.",
            "Contact details are shown only when available in the online geographic data.",
        ],
    }


# ============================================================
# 16. COMPATIBILITY FUNCTION
# ============================================================

def get_destinations():
    return {}


# ============================================================
# 17. CREATE ITINERARY
# ============================================================

def create_itinerary(
    destination,
    days,
    adults,
    children
):
    destination_data = get_destination(destination)

    if destination_data is None:
        return []

    places = destination_data.get("places", [])
    accommodations = destination_data.get("accommodations", [])

    if not places:
        return []

    try:
        days = max(1, int(days))
    except Exception:
        days = 1

    # Arrange attractions geographically rather than simply repeating
    # the same three nearest places every day.
    remaining = sorted(
        places,
        key=lambda p: p.get("distance_km", 999999)
    )

    day_buckets = [[] for _ in range(days)]

    # Greedy geographic grouping: distribute attractions round-robin
    # after sorting by distance. This keeps nearby attractions together
    # much better than the previous cyclic repetition.
    for index, place in enumerate(remaining):
        day_buckets[index % days].append(place)

    # Remove empty days when there are fewer attractions than days,
    # while still returning one entry per requested day.
    themes = [
        "Main Sightseeing",
        "Culture and Heritage",
        "Nature and Exploration",
        "Local Exploration",
        "Leisure and Photography",
        "Final Sightseeing",
    ]

    itinerary = []

    for day_number in range(1, days + 1):
        day_places = day_buckets[day_number - 1]

        if day_places:
            # Find a hotel/guest house near the day's attraction group.
            avg_lat = sum(
                float(p["latitude"]) for p in day_places
                if p.get("latitude") is not None
            ) / max(
                1,
                len([
                    p for p in day_places
                    if p.get("latitude") is not None
                ])
            )
            avg_lon = sum(
                float(p["longitude"]) for p in day_places
                if p.get("longitude") is not None
            ) / max(
                1,
                len([
                    p for p in day_places
                    if p.get("longitude") is not None
                ])
            )
        else:
            avg_lat = destination_data["latitude"]
            avg_lon = destination_data["longitude"]

        nearest_accommodation = None

        if accommodations:
            ranked_accommodations = sorted(
                accommodations,
                key=lambda hotel: calculate_distance_km(
                    avg_lat,
                    avg_lon,
                    hotel["latitude"],
                    hotel["longitude"],
                )
            )
            nearest_accommodation = ranked_accommodations[0]

        itinerary.append({
            "day": day_number,
            "theme": themes[(day_number - 1) % len(themes)],
            "places": day_places,
            "accommodation": nearest_accommodation,
            "stay_area": (
                nearest_accommodation["name"]
                if nearest_accommodation
                else "No accommodation found in online data"
            ),
        })

    return itinerary

# 17. ESTIMATED COST
# ============================================================

def calculate_estimated_cost(
    destination,
    days,
    adults,
    children,
    budget
):

    daily_cost = {

        "Budget": 1200,

        "Standard": 2500,

        "Premium": 5000
    }

    base_cost = daily_cost.get(

        budget,

        2500
    )

    try:

        days = int(
            days
        )

    except Exception:

        days = 1

    try:

        adults = int(
            adults
        )

    except Exception:

        adults = 1

    try:

        children = int(
            children
        )

    except Exception:

        children = 0

    adult_cost = (

        adults
        * base_cost
        * days
    )

    child_cost = (

        children
        * base_cost
        * 0.60
        * days
    )

    total_cost = (

        adult_cost
        + child_cost
    )

    return int(
        total_cost
    )


# ============================================================
# 18. CLEAR ONE DESTINATION CACHE
# ============================================================
#
# IMPORTANT:
# You normally DO NOT need to call this.
#
# It is useful when you want to force the application to fetch
# fresh information for ONE destination.
#
# Example:
#
# clear_destination_cache("Darjeeling")
#
# ============================================================

def clear_destination_cache(
    destination
):

    key = normalize_destination(
        destination
    )

    if key in CACHE:

        del CACHE[key]

        save_cache()

        print(
            "Cache cleared for:",
            destination
        )

        return True

    print(
        "Destination was not in cache:",
        destination
    )

    return False


# ============================================================
# 19. CLEAR ALL CACHE
# ============================================================
#
# IMPORTANT:
# You normally DO NOT need to call this.
#
# This is only for maintenance/testing.
#
# Example:
#
# clear_cache()
#
# ============================================================

def clear_cache():

    global CACHE

    CACHE = {}

    try:

        if CACHE_FILE.exists():

            CACHE_FILE.unlink()

        print(
            "All tourist cache cleared."
        )

        return True

    except Exception as error:

        print(
            "Unable to clear cache:",
            error
        )

        return False


# ============================================================
# 20. CACHE INFORMATION
# ============================================================

def get_cache_information():

    return {

        "cache_file":
            str(CACHE_FILE),

        "cached_destinations":
            len(CACHE),

        "cache_validity_days":
            CACHE_DAYS
    }


# ============================================================
# 21. BACKEND TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "================================================"
    )

    print(
        " INDIA TOURIST PLANNER"
    )

    print(
        " FAST BACKEND + LOCAL CACHE"
    )

    print(
        "================================================"
    )

    print()

    print(
        "Cache file:"
    )

    print(
        CACHE_FILE
    )

    print()

    print(
        "Cached destinations:",
        len(CACHE)
    )

    print()

    destination = input(
        "Enter an Indian tourist destination: "
    ).strip()

    if not destination:

        print(
            "No destination entered."
        )

    else:

        start_time = time.time()

        data = get_destination(
            destination
        )

        elapsed = (
            time.time()
            - start_time
        )

        print()

        if data is None:

            print(
                "Destination could not be found."
            )

        else:

            print(
                "Destination:",
                data["name"]
            )

            print(
                "State:",
                data["state"]
            )

            print(
                "Latitude:",
                data["latitude"]
            )

            print(
                "Longitude:",
                data["longitude"]
            )

            print()

            print(
                "Tourist places:"
            )

            for place in data[
                "places"
            ]:

                print(
                    "-",
                    place["name"],
                    "|",
                    place.get(
                        "distance_km",
                        "?"
                    ),
                    "km"
                )

            print()

            print(
                "Search time:",
                round(
                    elapsed,
                    2
                ),
                "seconds"
            )

            print()

            print(
                "If this destination is searched"
            )

            print(
                "again within the cache period,"
            )

            print(
                "the saved local data will be used."
            )
