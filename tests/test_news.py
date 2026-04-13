from datetime import datetime, timedelta, timezone

from app.services.aggregation.news_aggregator import NewsAggregator


def create_user_and_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "editor@dubnewsai.com",
            "full_name": "News Editor",
            "password": "supersecure123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "editor@dubnewsai.com", "password": "supersecure123"},
    )
    return login_response.json()["access_token"]


def test_create_article_and_list_with_filters(client):
    token = create_user_and_token(client)
    base_headers = {"Authorization": f"Bearer {token}"}

    first_article = {
        "title": "Dubai Rental Demand Hits New Heights",
        "description": "Rising investor appetite is pushing rental demand higher across key districts.",
        "content": "Analysts expect continued momentum throughout the quarter.",
        "url": "https://dubnewsai.test/articles/rental-demand",
        "source": "manual",
        "source_name": "DUBNEWSAI",
        "author": "News Editor",
        "category": "real_estate",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "image_url": "https://dubnewsai.test/images/rental-demand.jpg",
    }
    second_article = {
        "title": "Dubai Metro Expansion Supports Property Growth",
        "description": "Infrastructure upgrades continue to reshape buyer demand corridors.",
        "content": "Transit-linked communities are seeing stronger lead volume.",
        "url": "https://dubnewsai.test/articles/metro-expansion",
        "source": "manual",
        "source_name": "DUBNEWSAI",
        "author": "News Editor",
        "category": "infrastructure",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "image_url": "https://dubnewsai.test/images/metro-expansion.jpg",
    }

    create_first = client.post("/api/v1/news/", headers=base_headers, json=first_article)
    create_second = client.post("/api/v1/news/", headers=base_headers, json=second_article)

    assert create_first.status_code == 201
    assert create_second.status_code == 201
    assert create_first.json()["source"] == "manual"
    assert create_first.json()["category"] == "real_estate"

    list_response = client.get("/api/v1/news/?page=1&page_size=20")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert len(payload["articles"]) == 2

    filtered_response = client.get("/api/v1/news/?category=real_estate&page=1&page_size=20")
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["total"] == 1
    assert filtered_payload["articles"][0]["title"] == "Dubai Rental Demand Hits New Heights"

    search_response = client.get("/api/v1/news/?search=metro&page=1&page_size=20")
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["total"] == 1
    assert search_payload["articles"][0]["category"] == "infrastructure"


def test_deduplication_and_article_view_count(client):
    token = create_user_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": "Dubai Off-Plan Activity Remains Elevated",
        "description": "Developers continue to launch projects into a receptive market.",
        "content": "Investor appetite remains resilient in key submarkets.",
        "url": "https://dubnewsai.test/articles/off-plan-activity",
        "source": "manual",
        "source_name": "DUBNEWSAI",
        "author": "News Editor",
        "category": "development",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }

    first_response = client.post("/api/v1/news/", headers=headers, json=payload)
    duplicate_response = client.post("/api/v1/news/", headers=headers, json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409

    article_id = first_response.json()["id"]
    get_response = client.get(f"/api/v1/news/{article_id}")
    assert get_response.status_code == 200
    assert get_response.json()["view_count"] == 1


def test_create_news_requires_authentication(client):
    response = client.post(
        "/api/v1/news/",
        json={
            "title": "Unauthorized Article Attempt",
            "description": "This request should be rejected because no bearer token is provided.",
            "content": "No token attached.",
            "url": "https://dubnewsai.test/articles/unauthorized",
            "source": "manual",
            "source_name": "DUBNEWSAI",
            "author": "Anonymous",
            "category": "general",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 401


def test_news_query_plan_rotates_high_priority_provider_queries():
    aggregator = NewsAggregator()
    queries = aggregator._queries_for_provider(
        "newsapi",
        "Dubai real estate",
        datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc),
    )

    assert queries[0] == "Dubai real estate"
    assert len(queries) == 3
    assert len(set(queries)) == len(queries)


def test_news_query_plan_keeps_rss_single_query():
    aggregator = NewsAggregator()
    queries = aggregator._queries_for_provider(
        "rss_feeds",
        "Dubai real estate",
        datetime(2026, 4, 13, 9, 0, tzinfo=timezone.utc),
    )

    assert queries == ["Dubai real estate"]
