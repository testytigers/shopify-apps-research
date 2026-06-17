#!/usr/bin/env python3
"""
Scrape Shopify App Store for top apps across 25 niches to reach ~250 apps.
Parses raw HTML from curl requests.
"""

import json
import re
import time
import random
import subprocess
import sys
from urllib.parse import quote, unquote

NICHES = {
    "wishlist": "wishlist",
    "out_of_stock_alerts": "out+of+stock+alerts+notifications",
    "checkout_customization": "checkout+customization",
    "bulk_operations": "bulk+operations+edit",
    "discounts_bundles": "discounts+bundles+offers",
    "product_reviews": "product+reviews+ratings",
    "live_chat_support": "live+chat+support",
    "email_marketing": "email+marketing+automation",
    "seo_optimization": "seo+optimization+meta",
    "inventory_management": "inventory+management+tracking",
    "order_tracking": "order+tracking+shipment",
    "social_media_shopping": "social+media+instagram+facebook",
    "payment_gateway": "payment+gateway+express+checkout",
    "shipping_fulfillment": "shipping+fulfillment+delivery",
    "return_refund": "returns+refunds+exchanges",
    "subscription_recurring": "subscription+recurring+billing",
    "countdown_timer": "countdown+timer+urgency",
    "size_chart": "size+chart+fit+guide",
    "loyalty_rewards": "loyalty+rewards+points",
    "product_customizer": "product+customizer+personalizer",
    "preorder": "preorder+pre-order",
    "currency_converter": "currency+converter+multi",
    "product_feed": "product+feed+google+shopping",
    "fraud_protection": "fraud+protection+security+order+risk",
    "abandoned_checkout": "abandoned+checkout+cart",
}

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def fetch_page(query):
    """Fetch Shopify App Store search page via curl."""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L", "--max-time", "20",
                "-H", f"User-Agent: {USER_AGENT}",
                "-H", "Accept-Language: en-US,en;q=0.9",
                f"https://apps.shopify.com/search?q={quote(query)}",
            ],
            capture_output=True, text=True, timeout=25
        )
        return result.stdout
    except Exception as e:
        print(f"  Fetch error: {e}", file=sys.stderr)
        return ""


def parse_app_page(html, niche):
    """Parse app data from the search results HTML."""
    apps = []
    
    # Extract app name + slug pairs from href patterns
    # Pattern: href="/apps.shopify.com/SLUG?search_id=..." ...>NAME</a>
    app_pattern = re.compile(
        r'href="[^"]*apps\.shopify\.com/([^/?]+)\?search_id=[^"]*"(?:\s[^>]*)?>\s*([^<]+)\s*</a>'
    )
    
    # Also try a simpler pattern
    alt_pattern = re.compile(
        r'href="([^"]*?/apps\.shopify\.com/([^/?]+))[^"]*"[^>]*>\s*([^<]+)\s*</a>'
    )
    
    # Find all app entries
    # Each app entry in the HTML looks like:
    # href="/apps.shopify.com/SLUG?search_id=..." ...>NAME</a>
    # And somewhere nearby: "5.0\n               out of 5 stars\n            " and "(77)\n            77 total reviews"
    
    # Extract app slugs and names
    slug_name_pairs = []
    for m in app_pattern.finditer(html):
        slug = m.group(1)
        name = m.group(2).strip().replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Skip non-app entries
        if name and len(name) > 2 and not name.startswith('Learn') and not name.startswith('Read ') and not name.startswith('Browse'):
            slug_name_pairs.append((slug, name))
    
    # Also try alternate pattern
    for m in alt_pattern.finditer(html):
        slug = m.group(2)
        name = m.group(3).strip().replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        if name and len(name) > 2 and not name.startswith('Learn') and not name.startswith('Read '):
            # Check if not already found
            if not any(s == slug for s, _ in slug_name_pairs):
                slug_name_pairs.append((slug, name))
    
    # Now extract ratings, review counts, and pricing for each app
    # These are in adjacent elements in the HTML
    # Look for patterns like: "5.0\n               out of 5 stars\n            "
    # And: "(77)\n            77 total reviews\n            •\n            Free"
    
    # Extract all rating numbers
    rating_pattern = re.compile(r'([\d.]+)\s*out of 5 stars')
    rating_matches = [(m.start(), m.group(1)) for m in rating_pattern.finditer(html)]
    
    # Extract review counts
    review_pattern = re.compile(r'\(\d+\)\s*\n\s*(\d+)\s*total reviews')
    review_matches = [(m.start(), m.group(1)) for m in review_pattern.finditer(html)]
    
    # Extract pricing - look for patterns after review counts
    # Pattern: "total reviews\n            •\n            Free" or "Free plan" or "Free trial"
    pricing_pattern = re.compile(
        r'total reviews\s*\n\s*•\s*\n\s*(Free(?:\splan)?(?:\savailable)?|Free trial|Free to install)\s*\n',
        re.MULTILINE
    )
    pricing_matches = [(m.start(), m.group(1)) for m in pricing_pattern.finditer(html)]
    
    # Try to match apps with their ratings, reviews, and pricing by position
    # Sort all matches by position in HTML
    rating_positions = sorted(rating_matches, key=lambda x: x[0])
    review_positions = sorted(review_matches, key=lambda x: x[0])
    pricing_positions = sorted(pricing_matches, key=lambda x: x[0])
    
    # For each app (slug, name), find the nearest rating, review, and pricing after it
    for slug, name in slug_name_pairs[:15]:  # Limit to first 15 apps per niche
        # Find the slug position
        slug_pattern_str = f'apps.shopify.com/{re.escape(slug)}'
        slug_match = re.search(slug_pattern_str, html)
        if not slug_match:
            continue
        
        slug_pos = slug_match.start()
        
        # Find rating after slug position
        best_rating = ""
        for pos, rating in rating_positions:
            if pos > slug_pos:
                best_rating = rating
                break
        
        # Find review count after slug position
        best_reviews = "0"
        for pos, reviews in review_positions:
            if pos > slug_pos:
                best_reviews = reviews
                break
        
        # Find pricing after review
        best_pricing = "Unknown"
        for pos, pricing in pricing_positions:
            if pos > slug_pos:
                best_pricing = pricing
                break
        
        # Clean up pricing
        if best_pricing == "Free":
            best_pricing = "Free"
        elif best_pricing == "Free plan":
            best_pricing = "Free plan"
        elif best_pricing == "Free trial":
            best_pricing = "Free trial available"
        elif best_pricing == "Free to install":
            best_pricing = "Free"
        else:
            best_pricing = "Unknown"
        
        if best_rating and best_reviews != "0":
            apps.append({
                "name": name,
                "slug": slug,
                "rating": best_rating,
                "reviews": int(best_reviews),
                "pricing": best_pricing,
                "niche": niche,
            })
    
    return apps


def main():
    output_file = '/Users/yahya/shopify_list/shopify_all_niches_v3.json'
    all_results = {}
    seen_names = set()
    
    niche_list = list(NICHES.keys())
    total_scraped = 0
    
    for i, niche in enumerate(niche_list):
        query = NICHES[niche]
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[{i+1}/{len(niche_list)}] Scraping niche: {niche} (query: {query})", file=sys.stderr)
        
        # Fetch page
        html = fetch_page(query)
        if not html:
            print(f"  Failed to fetch page", file=sys.stderr)
            continue
        
        print(f"  Page size: {len(html)} bytes", file=sys.stderr)
        
        # Parse apps
        apps = parse_app_page(html, niche)
        
        # Deduplicate
        niche_apps = []
        for app in apps:
            if app["name"] not in seen_names and app["reviews"] > 0:
                seen_names.add(app["name"])
                niche_apps.append(app)
                print(f"  ✓ {app['name']} | {app['rating']}★ | {app['reviews']} reviews | {app['pricing']}", file=sys.stderr)
        
        if niche_apps:
            all_results[niche] = niche_apps
            total_scraped += len(niche_apps)
            print(f"  => Got {len(niche_apps)} apps for {niche} (total: {total_scraped})", file=sys.stderr)
        
        # Be polite
        time.sleep(random.uniform(2, 4))
    
    # Save results
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"TOTAL APPS SCRAPED: {total_scraped}", file=sys.stderr)
    for niche, apps in all_results.items():
        print(f"  {niche}: {len(apps)} apps", file=sys.stderr)
    
    with open(output_file, 'w') as f:
        json.dump({"niches": all_results, "total": total_scraped}, f, indent=2)
    
    print(f"\nSaved to: {output_file}", file=sys.stderr)
    
    # Save individual niche files
    for niche, apps in all_results.items():
        niche_file = f"/Users/yahya/shopify_list/niches/{niche}.json"
        with open(niche_file, 'w') as f:
            json.dump({"niche": niche, "top_apps": apps}, f, indent=2)


if __name__ == '__main__':
    main()
