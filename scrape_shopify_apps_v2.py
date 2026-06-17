#!/usr/bin/env python3
"""
Scrape Shopify App Store for top apps across 20+ niches to reach ~250 apps.
Uses web_search via Python requests + BeautifulSoup to find apps.
"""

import json
import re
import time
import random
import subprocess
import sys
from urllib.parse import quote, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

# 20 niches to target ~250 apps (~12-15 per niche)
NICHES = {
    "wishlist": {
        "search_query": "site:apps.shopify.com search?q=wishlist",
        "keywords": ["wishlist", "favorites", "save for later", "wish list"],
    },
    "out_of_stock_alerts": {
        "search_query": "site:apps.shopify.com search?q=out+of+stock+alerts+notifications",
        "keywords": ["out of stock", "restock", "back in stock", "notify", "sold out"],
    },
    "checkout_customization": {
        "search_query": "site:apps.shopify.com search?q=checkout+customization",
        "keywords": ["checkout", "upsell", "customization", "post purchase", "order options"],
    },
    "bulk_operations": {
        "search_query": "site:apps.shopify.com search?q=bulk+operations+edit",
        "keywords": ["bulk", "bulk edit", "bulk operations", "csv", "import export"],
    },
    "discounts_bundles": {
        "search_query": "site:apps.shopify.com search?q=discounts+bundles+offers",
        "keywords": ["discount", "bundle", "volume discount", "free shipping", "offer"],
    },
    "product_reviews": {
        "search_query": "site:apps.shopify.com search?q=product+reviews",
        "keywords": ["reviews", "rating", "review", "user generated content", "photo review"],
    },
    "live_chat_support": {
        "search_query": "site:apps.shopify.com search?q=live+chat+support",
        "keywords": ["live chat", "chat", "support", "customer service", "help"],
    },
    "email_marketing": {
        "search_query": "site:apps.shopify.com search?q=email+marketing+automation",
        "keywords": ["email", "marketing", "newsletter", "automation", "campaign", "flow"],
    },
    "seo_optimization": {
        "search_query": "site:apps.shopify.com search?q=seo+optimization+meta",
        "keywords": ["seo", "meta", "optimization", "sitemap", "structured data", "schema"],
    },
    "inventory_management": {
        "search_query": "site:apps.shopify.com search?q=inventory+management+tracking",
        "keywords": ["inventory", "stock", "tracking", "warehouse", "multichannel"],
    },
    "order_tracking": {
        "search_query": "site:apps.shopify.com search?q=order+tracking+shipment",
        "keywords": ["tracking", "shipment", "delivery", "order status", "tracking page"],
    },
    "social_media": {
        "search_query": "site:apps.shopify.com search?q=social+media+instagram+facebook",
        "keywords": ["social", "instagram", "facebook", "tiktok", "share", "social proof"],
    },
    "payment_gateway": {
        "search_query": "site:apps.shopify.com search?q=payment+gateway+express+checkout",
        "keywords": ["payment", "express checkout", "apple pay", "google pay", "wallet"],
    },
    "shipping_fulfillment": {
        "search_query": "site:apps.shopify.com search?q=shipping+fulfillment+delivery",
        "keywords": ["shipping", "fulfillment", "delivery", "rate", "carrier", "postage"],
    },
    "return_refund": {
        "search_query": "site:apps.shopify.com search?q=returns+refunds+exchanges",
        "keywords": ["return", "refund", "exchange", "RMA", "replacement"],
    },
    "subscription_recurring": {
        "search_query": "site:apps.shopify.com search?q=subscription+recurring+billing",
        "keywords": ["subscription", "recurring", "billing", "membership", "repeat"],
    },
    "countdown_timer": {
        "search_query": "site:apps.shopify.com search?q=countdown+timer+urgency",
        "keywords": ["countdown", "timer", "urgency", "limited", "flash sale", "offer"],
    },
    "size_chart_fit": {
        "search_query": "site:apps.shopify.com search?q=size+chart+fit+guide",
        "keywords": ["size chart", "fit", "guide", "size guide", "size selector"],
    },
    "tax_calculator": {
        "search_query": "site:apps.shopify.com search?q=tax+calculator+vat+compliance",
        "keywords": ["tax", "vat", "compliance", "gst", "sales tax", "automated"],
    },
    "loyalty_rewards": {
        "search_query": "site:apps.shopify.com search?q=loyalty+rewards+points",
        "keywords": ["loyalty", "rewards", "points", "referral", "program", "gamification"],
    },
    "product_customizer": {
        "search_query": "site:apps.shopify.com search?q=product+customizer+personalizer",
        "keywords": ["customizer", "personalize", "custom", " engraving", "design tool"],
    },
    "preorder": {
        "search_query": "site:apps.shopify.com search?q=preorder+pre-order+advance",
        "keywords": ["preorder", "pre-order", "advance", "coming soon", "reserve"],
    },
    "currency_converter": {
        "search_query": "site:apps.shopify.com search?q=currency+converter+multi+language",
        "keywords": ["currency", "converter", "multi", "language", "translate", "international"],
    },
    "product_feed": {
        "search_query": "site:apps.shopify.com search?q=product+feed+google+shopping+merchant",
        "keywords": ["feed", "google", "shopping", "merchant", "catalog", "ads"],
    },
    "fraud_protection": {
        "search_query": "site:apps.shopify.com search?q=fraud+protection+security+order+risk",
        "keywords": ["fraud", "protection", "security", "risk", "verify", "order"],
    },
}


def google_search(query):
    """Search Google and return Shopify app store URLs."""
    try:
        result = subprocess.run(
            [
                "curl", "-s",
                "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "-H", "Accept-Language: en-US,en;q=0.9",
                f"https://www.google.com/search?q={quote(query)}&num=10",
            ],
            capture_output=True, text=True, timeout=30
        )
        urls = []
        # Match /url?q=... patterns
        matches = re.findall(r'/url\?q=([^"&]+)', result.stdout)
        for encoded_url in matches:
            decoded = unquote(encoded_url)
            # Extract actual URL from redirect
            app_match = re.search(r'https://apps\.shopify\.com/(?:app)?s?/([^/]+)', decoded)
            if app_match:
                urls.append(f"https://apps.shopify.com/app/{app_match.group(1)}")
            elif "apps.shopify.com" in decoded and "/apps/" in decoded:
                urls.append(decoded.replace("/apps/", "/app/"))
        # Deduplicate while preserving order
        return list(dict.fromkeys(urls))
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        return []


def scrape_single_app(url):
    """Scrape a single Shopify app page using curl."""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L",
                "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "-H", "Accept-Language: en-US,en;q=0.9",
                url,
            ],
            capture_output=True, text=True, timeout=30
        )
        html = result.stdout
        
        # Extract app name from page
        name = ""
        name_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
        if not name_match:
            name_match = re.search(r'"name":"([^"]+)"', html)
        if name_match:
            name = name_match.group(1).strip()
        
        # Extract rating
        rating = ""
        rating_match = re.search(r'([\d.]+)\s*(?:out of|/)\s*\d\s*(?:stars)?', html)
        if not rating_match:
            rating_match = re.search(r'"averageRating":([\d.]+)', html)
        if rating_match:
            rating = rating_match.group(1)
        
        # Extract review count
        reviews = 0
        review_match = re.search(r'([\d,]+)\s*(?:reviews?|ratings?)', html, re.IGNORECASE)
        if not review_match:
            review_match = re.search(r'"reviewCount":(\d+)', html)
        if review_match:
            reviews = int(review_match.group(1).replace(',', ''))
        else:
            # Try the number in parentheses pattern
            paren_match = re.search(r'\(([\d,]+)\)', html)
            if paren_match:
                reviews = int(paren_match.group(1).replace(',', ''))
        
        # Extract pricing tier
        pricing = ""
        if re.search(r'Free|free plan|free to install', html, re.IGNORECASE):
            pricing = "Free"
        elif re.search(r'from \$\d+', html) or re.search(r'\$[\d,]+/mo', html):
            price_match = re.search(r'(?:from )?\$(\d+)(?:\.\d+)?(?:/mo)?', html)
            if price_match:
                pricing = f"${price_match.group(1)}/mo"
        else:
            pricing = "Free"
        
        # Extract description
        description = ""
        desc_match = re.search(r'"description":"([^"]{20,500})"', html)
        if not desc_match:
            desc_match = re.search(r'<p[^>]*>([^<]{20,300})</p>', html)
        if desc_match:
            description = desc_match.group(1).strip()
        
        # Extract developer name
        developer = ""
        dev_match = re.search(r'by\s+([^<"\n]+)', html)
        if dev_match:
            developer = dev_match.group(1).strip()
        
        # Extract app URL
        app_url = re.search(r'href="(https://apps\.shopify\.com/app/[^"]+)"', html)
        if app_url:
            app_url = app_url.group(1)
        
        if name and reviews > 0:
            return {
                "name": name,
                "rating": rating,
                "reviews": reviews,
                "pricing": pricing,
                "description": description[:200] if description else "",
                "developer": developer,
                "url": app_url or url,
            }
        elif name and rating:
            # App with rating but no review count visible
            return {
                "name": name,
                "rating": rating,
                "reviews": 0,
                "pricing": pricing,
                "description": description[:200] if description else "",
                "developer": developer,
                "url": app_url or url,
            }
        else:
            return None
    except Exception as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        return None


def main():
    output_file = '/Users/yahya/shopify_list/shopify_all_niches_v2.json'
    all_results = {}
    seen_names = set()
    
    # Process each niche
    niche_list = list(NICHES.keys())
    for niche in niche_list:
        config = NICHES[niche]
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"=== Scraping niche: {niche} ===", file=sys.stderr)
        
        # Step 1: Search Google for app URLs
        search_urls = google_search(config["search_query"])
        print(f"Found {len(search_urls)} app URLs via Google search", file=sys.stderr)
        
        # Step 2: Scrape each app page
        niche_apps = []
        for url in search_urls:
            if url in seen_names or len(niche_apps) >= 15:
                break
            
            # Extract app name from URL for dedup
            url_name = url.split('/app/')[-1].strip().rstrip('/')
            
            if url_name in seen_names:
                continue
                
            print(f"  Scraping: {url_name}", file=sys.stderr)
            app = scrape_single_app(url)
            if app:
                seen_names.add(app["name"])
                app["search_url_name"] = url_name
                niche_apps.append(app)
                print(f"    ✓ {app['name']} | {app['rating']}★ | {app['reviews']} reviews | {app['pricing']}", file=sys.stderr)
            
            # Be polite
            time.sleep(random.uniform(1.5, 3.5))
        
        if niche_apps:
            all_results[niche] = niche_apps
            print(f"  => Got {len(niche_apps)} apps for {niche}", file=sys.stderr)
        
        time.sleep(random.uniform(2, 4))
    
    # Save results
    total = sum(len(v) for v in all_results.values())
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Total apps scraped: {total}", file=sys.stderr)
    for niche, apps in all_results.items():
        print(f"  {niche}: {len(apps)} apps", file=sys.stderr)
    
    with open(output_file, 'w') as f:
        json.dump({"niches": all_results, "total": total}, f, indent=2)
    
    print(f"\nSaved to: {output_file}", file=sys.stderr)
    
    # Also save individual niche files
    for niche, apps in all_results.items():
        niche_file = f"/Users/yahya/shopify_list/niches/{niche}.json"
        import os
        os.makedirs(os.path.dirname(niche_file), exist_ok=True)
        with open(niche_file, 'w') as f:
            json.dump({"niche": niche, "top_apps": apps}, f, indent=2)
    
    print("Individual niche files saved.", file=sys.stderr)


if __name__ == '__main__':
    main()
