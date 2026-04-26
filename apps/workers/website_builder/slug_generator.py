"""Generate URL-safe unique slugs for sites table."""
from slugify import slugify


def generate_unique_slug(company_name: str, supabase_client) -> str:
    """
    Generate a URL-safe slug from a company name. If a row in `sites` table
    already has the same slug, append `-2`, `-3`, etc. until unique.
    """
    # Pre-process: replace & with 'and', remove apostrophes (no separator)
    name = company_name.replace("&", "and")
    name = name.replace("'", "").replace("’", "")
    base = slugify(name, lowercase=True)
    if not _slug_exists(base, supabase_client):
        return base

    n = 2
    while True:
        candidate = f"{base}-{n}"
        if not _slug_exists(candidate, supabase_client):
            return candidate
        n += 1


def _slug_exists(slug: str, supabase_client) -> bool:
    result = (
        supabase_client.table("sites")
        .select("id")
        .eq("slug", slug)
        .execute()
    )
    return bool(result.data)
