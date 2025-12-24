#!/usr/bin/env python
"""
Generate talkmap from markdown files in _talks directory
"""

import glob
import json
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Manual geocoding for known locations (to avoid API timeouts)
LOCATION_COORDS = {
    "Honolulu, Hawaii": (21.3099, -157.8581),
    "Location TBD": None,
    "Atlanta, Georgia": (33.7490, -84.3880),
    "Bentonville, Arkansas": (36.3729, -94.2088),
    "Dallas, Texas": (32.7767, -96.7970),
    "Denver, Colorado": (39.7392, -104.9903),
    "Long Beach, California": (33.7701, -118.1937),
    "Washington, DC": (38.9072, -77.0369),
    "Phoenix, Arizona": (33.4484, -112.0740),
    "Tempe, Arizona": (33.4255, -111.9400),
    "Manhattan, Kansas": (39.1836, -96.5717),
    "Virtual": None,
    "Nashville, Tennessee": (36.1627, -86.7816),
    "Seattle, Washington": (47.6062, -122.3321),
    "Gainesville, Florida": (29.6516, -82.3248),
    "Riverside, California": (33.9806, -117.3755),
    "St. Louis, Missouri": (38.6270, -90.1994),
    "New York, New York": (40.7128, -74.0060),
    "Hanover, New Hampshire": (43.7022, -72.2896),
    "Houston, Texas": (29.7604, -95.3698),
    "Lawrence, Kansas": (38.9717, -95.2353),
    "Salt Lake City, Utah": (40.7608, -111.8910),
    "South Bend, Indiana": (41.6764, -86.2520),
    "University Park, Pennsylvania": (40.7982, -77.8599),
    "National Harbor, Maryland": (38.7829, -77.0174),
    "Rotterdam, Netherlands": (51.9225, 4.4792),
    "College Park, Maryland": (38.9807, -76.9370),
    "Orlando, Florida": (28.5383, -81.3792),
    "Singapore": (1.3521, 103.8198),
    "Glasgow, Scotland": (55.8642, -4.2518),
    "Boston, Massachusetts": (42.3601, -71.0589),
    "Chicago, Illinois": (41.8781, -87.6298),
    "Coral Gables, Florida": (25.7617, -80.1918),
    "Boulder, Colorado": (40.0150, -105.2705),
    "San Diego, California": (32.7157, -117.1611),
    "Miami, Florida": (25.7617, -80.1918),
    "London, United Kingdom": (51.5074, -0.1278),
    "Columbia, Missouri": (38.9517, -92.3341),
    "Tucson, Arizona": (32.2226, -110.9747),
    "San Francisco, California": (37.7749, -122.4194),
}

def extract_location_from_md(filepath):
    """Extract location from markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'location: "' in content:
            start = content.find('location: "') + 11
            end = content[start:].find('"')
            return content[start:start+end]
    return None

def geocode_location(location, geocoder):
    """Geocode a location with retry logic"""
    if location in LOCATION_COORDS:
        coords = LOCATION_COORDS[location]
        if coords:
            return type('obj', (object,), {'latitude': coords[0], 'longitude': coords[1]})()
        return None

    # Try geocoding with Nominatim
    for attempt in range(3):
        try:
            time.sleep(1)  # Be nice to the API
            result = geocoder.geocode(location, timeout=10)
            if result:
                print(f"Geocoded {location}: ({result.latitude}, {result.longitude})")
                return result
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Attempt {attempt + 1} failed for {location}: {e}")
            time.sleep(2)

    print(f"Could not geocode: {location}")
    return None

def main():
    # Get all markdown files in _talks directory
    md_files = glob.glob("_talks/*.md")

    if not md_files:
        print("No markdown files found in _talks directory")
        return

    print(f"Found {len(md_files)} talk files")

    # Initialize geocoder
    geocoder = Nominatim(user_agent="academic_website_talkmap")

    # Collect unique locations
    locations = {}
    location_counts = {}

    for filepath in md_files:
        location = extract_location_from_md(filepath)
        if location and location != "Virtual" and location != "Location TBD":
            if location not in location_counts:
                location_counts[location] = 0
            location_counts[location] += 1

            if location not in locations:
                print(f"Processing: {location}")
                result = geocode_location(location, geocoder)
                if result:
                    locations[location] = {
                        'lat': result.latitude,
                        'lng': result.longitude,
                        'count': 1
                    }

    # Update counts
    for loc in locations:
        if loc in location_counts:
            locations[loc]['count'] = location_counts[loc]

    # Generate JavaScript data
    js_data = "var addressPoints = [\n"
    for location, data in locations.items():
        count_text = f" ({data['count']} talks)" if data['count'] > 1 else ""
        js_data += f'  ["{location}{count_text}", {data["lat"]}, {data["lng"]}],\n'
    js_data += "];"

    # Write JavaScript file
    with open('talkmap/org-locations.js', 'w', encoding='utf-8') as f:
        f.write(js_data)

    print(f"\nGenerated talkmap with {len(locations)} unique locations")
    print(f"Output written to: talkmap/org-locations.js")

if __name__ == "__main__":
    main()
