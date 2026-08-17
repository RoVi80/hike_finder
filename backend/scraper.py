import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.schweizer-wanderwege.ch/de/wandervorschlaege/"

async def fetch_hike_recommendations(location: str):
    params = {
        "criteria[fulltext]": location,
        "criteria[seasons][]": "68"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(BASE_URL, params=params)
        soup = BeautifulSoup(response.text, "html.parser")

        hikes = []

        for card in soup.select("div.uk-card.l-hike"):
            # Title and URL
            title_link = card.select_one("h3.uk-card-title > a")
            title = title_link.get_text(strip=True) if title_link else None
            url = f"https://www.schweizer-wanderwege.ch{title_link['href']}" if title_link and title_link.has_attr('href') else None


            # Description
            desc_tag = card.select_one("div.uk-text-default")
            description = desc_tag.get_text(strip=True) if desc_tag else None

            # Image
            img_tag = card.select_one("picture img")
            image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

            # Metadata
            metadata_spans = card.select("div.l-hike-footer span.l-card-footer-label")
            metadata = [span.get_text(strip=True) for span in metadata_spans]

            hikes.append({
                "title": title,
                "url": url,
                "image": image_url,
                "description": description,
                "metadata": metadata
            })

        return hikes
