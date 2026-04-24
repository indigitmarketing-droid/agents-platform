"""Build Overpass QL queries for finding businesses without websites."""


def build_no_website_query(
    category_type: str,
    category: str,
    city: str,
    limit: int = 100,
    timeout_seconds: int = 60,
) -> str:
    """
    Build an Overpass QL query that finds nodes of the given category in the
    given city that DO NOT have a `website` tag but DO have a `phone` tag.
    """
    return (
        f"[out:json][timeout:{timeout_seconds}];"
        f'area["name"="{city}"]["place"="city"]->.searchArea;'
        f"("
        f'node["{category_type}"="{category}"][!"website"]["phone"](area.searchArea);'
        f");"
        f"out body {limit};"
    )
