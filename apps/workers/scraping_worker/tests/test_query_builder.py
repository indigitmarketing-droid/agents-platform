from apps.workers.scraping_worker.query_builder import build_no_website_query


def test_query_contains_category_type_and_value():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert 'node["amenity"="restaurant"]' in q


def test_query_filters_no_website():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert '[!"website"]' in q


def test_query_requires_phone():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert '["phone"]' in q


def test_query_includes_city():
    q = build_no_website_query("shop", "hairdresser", "Roma")
    assert '"name"="Roma"' in q


def test_query_has_json_output():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "[out:json]" in q


def test_query_has_timeout():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "[timeout:" in q


def test_query_has_max_results_limit():
    q = build_no_website_query("amenity", "restaurant", "Milano", limit=50)
    assert "out body 50" in q


def test_query_default_limit_100():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "out body 100" in q


def test_query_with_leisure_type():
    q = build_no_website_query("leisure", "fitness_centre", "Milano")
    assert 'node["leisure"="fitness_centre"]' in q


def test_query_with_craft_type():
    q = build_no_website_query("craft", "photographer", "Milano")
    assert 'node["craft"="photographer"]' in q
