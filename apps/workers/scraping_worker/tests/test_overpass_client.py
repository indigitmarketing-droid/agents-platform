import pytest
from pytest_httpx import HTTPXMock
from apps.workers.scraping_worker.overpass_client import (
    OverpassClient,
    OverpassRateLimitError,
    OverpassUnreachableError,
)


@pytest.mark.asyncio
async def test_query_returns_elements_on_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": [{"id": 1, "tags": {"name": "Test"}}]},
    )
    client = OverpassClient()
    result = await client.query("test query")
    assert result == [{"id": 1, "tags": {"name": "Test"}}]


@pytest.mark.asyncio
async def test_query_returns_empty_when_no_elements(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": []},
    )
    client = OverpassClient()
    result = await client.query("test query")
    assert result == []


@pytest.mark.asyncio
async def test_query_retries_on_rate_limit(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=429,
    )
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": [{"id": 1}]},
    )
    client = OverpassClient(initial_backoff=0.01)
    result = await client.query("test query", max_retries=2)
    assert result == [{"id": 1}]


@pytest.mark.asyncio
@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
async def test_query_raises_after_max_retries(httpx_mock: HTTPXMock):
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass-api.de/api/interpreter",
            status_code=429,
        )
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass.kumi.systems/api/interpreter",
            status_code=429,
        )
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass.private.coffee/api/interpreter",
            status_code=429,
        )
    client = OverpassClient(initial_backoff=0.01)
    with pytest.raises((OverpassRateLimitError, OverpassUnreachableError)):
        await client.query("test query", max_retries=2)


@pytest.mark.asyncio
@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
async def test_query_falls_back_to_mirror_on_500(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=500,
    )
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=500,
    )
    httpx_mock.add_response(
        url="https://overpass.kumi.systems/api/interpreter",
        json={"elements": [{"id": 42}]},
    )
    client = OverpassClient(initial_backoff=0.01)
    result = await client.query("test query", max_retries=3)
    assert result == [{"id": 42}]


@pytest.mark.asyncio
async def test_query_uses_post_with_form_data(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": []},
    )
    client = OverpassClient()
    await client.query("test query")
    request = httpx_mock.get_request()
    assert request.method == "POST"
    assert b"data=test+query" in request.content or b"data=test%20query" in request.content
