#!/usr/bin/env python3
"""Build feature comparison tables for all niches from the scraped data.

Extracts feature keywords from app descriptions and builds a comparison matrix.
"""

import json
import os
import re

# Common feature keyword extraction patterns
FEATURE_KEYWORDS = {
    "seo": ["seo", "search engine", "optimization", "rank", "ranking", "meta", "alt text", "image", "speed", "ai", "blog", "keyword", "schema", "json-ld", "sitemap", "robots", "analytics", "backlink", "content", "ai"],
    "translate": ["translate", "language", "currency", "multi", "global", "location", "auto", "ai", "deepl", "google", "open ai", "deepseek"],
    "discounts": ["bundle", "bogo", "buy one get", "buy x get y", "volume discount", "tiered", "quantity", "break", "gift", "free gift", "offer", "discount", "upsell", "aoi", "add on"],
    "email": ["email", "sms", "whatsapp", "rcs", "popup", "newsletter", "automation", "form", "sign up", "cart recovery", "loyalty", "personalized", "marketing"],
    "faq": ["faq", "question", "answer", "ai", "chat", "help", "support", "ticket", "accordion", "kb", "knowledge base", "product", "helpdesk", "schema", "seo"],
    "upsell": ["upsell", "cross sell", "bundle", "related", "frequently bought", "recommendation", "cart", "product", "suggestion", "ai", "popup", "post purchase", "offer", "volume"],
    "reviews": ["review", "rating", "photo", "video", "ai", "verified", "email", "request", "widget", "badge", "trust", "social proof", "automated", "response"],
    "wishlist": ["wishlist", "save", "favorite", "share", "price alert", "notify", "low stock", "back in stock", "email", "social", "share", "product", "list"],
    "blog": ["blog", "post", "ai", "writer", "seo", "editor", "publish", "schedule", "template", "image", "keyword", "content", "analytics", "recipe", "shopable"],
    "chat": ["chat", "live chat", "messenger", "whatsapp", "telegram", "ai", "bot", "ticket", "help", "support", "notification", "omnichannel", "integration", "automated"],
    "inventory": ["stock", "alert", "notify", "back in stock", "low stock", "out of stock", "predict", "demand", "forecast", "ai", "auto", "sync", "multichannel"],
    "shipping": ["shipping", "tracking", "delivery", "order", "label", "rate", "carrier", "insurance", "fulfill", "notification", "tracking number", "real time", "free shipping"],
    "payment": ["payment", "checkout", "express", "apple pay", "google pay", "paypal", "k pay", "klarna", "afterpay", "split payment", "installment", "subscription", "recurring"],
    "social": ["instagram", "social", "feed", "tiktok", "pinterest", "facebook", "reel", "shop", "tag", "product", "embed", "u gc", "influencer", "hashtag"],
    "loyalty": ["loyalty", "points", "reward", "referral", "tier", "vip", "gamification", "subscription", "program", "signup", "tier", "milestone", "earn", "redeem", "ai"],
    "checkout": ["checkout", "customization", "one page", "express", "upsell", "field", "banner", "progress bar", "trust", "badge", "shipping", "delivery", "payment", "brand"],
    "popup": ["popup", "signup", "form", "exit intent", "discount", "coupon", "email", "sms", "social", "countdown", "timer", "trigger", "automation", "form", "lead", "opt in"],
}

def extract_features(description):
    """Extract feature keywords from an app description."""
    desc_lower = description.lower()
    features = []
    for feature, keywords in FEATURE_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                features.append(feature)
                break
    return features

def build_comparison(niche_name, apps):
    """Build a comparison matrix for a niche."""
    # Collect all features across all apps in this niche
    all_features = set()
    app_data = []
    
    for app in apps:
        features = extract_features(app["description"])
        app_data.append({
            "name": app["name"],
            "rating": app["rating"],
            "reviews": app["reviews"],
            "pricing": app["pricing"],
            "features": features,
            "description": app["description"]
        })
        all_features.update(features)
    
    return app_data, sorted(all_features)

def generate_markdown(niche_name, app_data, all_features):
    """Generate a markdown comparison table."""
    lines = []
    lines.append(f"## {niche_name.replace('_', ' ').title()}")
    lines.append("")
    
    # Feature comparison table
    lines.append("### Feature Comparison")
    lines.append("")
    
    # Header row
    header = "| App | Rating | Reviews | Pricing | Features |"
    sep = "|" + "---|" * 6
    lines.append(header)
    lines.append(sep)
    
    # Feature descriptions
    feature_descriptions = {
        "seo": "SEO Optimization, Meta Tags, Sitemap, AI Content",
        "translate": "Language Translation, Currency Converter, Multi-language",
        "discounts": "Bundles, BOGO, Volume Discounts, Tiered Pricing",
        "email": "Email Marketing, SMS, WhatsApp, Popups, Automation",
        "faq": "FAQ Builder, Chatbot, Helpdesk, Knowledge Base, AI",
        "upsell": "Upsell/Cross-sell, Bundles, Related Products, AI",
        "reviews": "Reviews, Ratings, Photos, Videos, AI, Social Proof",
        "wishlist": "Wishlist, Save, Favorite, Price Alerts, Social Share",
        "blog": "Blog Builder, AI Writer, SEO, Editor, Publishing",
        "chat": "Live Chat, Messenger, WhatsApp, AI Bot, Support",
        "inventory": "Stock Alerts, Back in Stock, Low Stock, AI Forecast",
        "shipping": "Shipping, Tracking, Labels, Rates, Notifications",
        "payment": "Checkout, Express Pay, Installments, Subscription",
        "social": "Instagram, TikTok, Social Feed, UGC, Influencer",
        "loyalty": "Loyalty, Points, Rewards, Referral, Tiers, VIP",
        "checkout": "Checkout Customization, Express, Fields, Banners",
        "popup": "Popup, Signup Form, Exit Intent, Discount, Lead Gen",
    }
    
    for app in app_data:
        feature_tags = ", ".join([f"`{f}`" for f in app["features"]]) if app["features"] else "N/A"
        lines.append(f"| {app['name']} | ⭐{app['rating']} | {app['reviews']} | {app['pricing']} | {feature_tags} |")
    
    # Feature detail table
    lines.append("")
    lines.append("### Feature Matrix")
    lines.append("")
    lines.append("| App | " + " | ".join([f"`.{f}`" for f in all_features]) + " |")
    lines.append("| --- |" + " | " + " |".join(["-" * 8 for _ in all_features]) + " |")
    
    for app in app_data:
        row = f"| {app['name']} |"
        for f in all_features:
            row += f" {'✓' if f in app['features'] else '—'} |"
        lines.append(row)
    
    # Pricing summary
    lines.append("")
    lines.append("### Pricing Summary")
    lines.append("")
    pricing_counts = {}
    for app in app_data:
        pricing_counts[app["pricing"]] = pricing_counts.get(app["pricing"], 0) + 1
    
    for pricing, count in sorted(pricing_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{pricing}**: {count} apps")
    
    # Top apps by reviews
    lines.append("")
    lines.append("### Top Apps by Review Count")
    lines.append("")
    sorted_apps = sorted(app_data, key=lambda x: int(x["reviews"]) if isinstance(x["reviews"], (int, float)) or (isinstance(x["reviews"], str) and x["reviews"].isdigit()) else 0, reverse=True)
    for i, app in enumerate(sorted_apps[:5], 1):
        lines.append(f"{i}. **{app['name']}** — ⭐{app['rating']} | {app['reviews']} reviews | {app['pricing']}")
        lines.append(f"   _{app['description']}_")
    
    lines.append("")
    return "\n".join(lines)

def main():
    niches_dir = "/Users/yahya/shopify_list/niches/"
    output_file = "/Users/yahya/shopify_list/feature_comparison.md"
    
    all_sections = []
    all_niche_data = {}
    
    for fname in sorted(os.listdir(niches_dir)):
        if not fname.endswith(".json"):
            continue
        
        with open(os.path.join(niches_dir, fname)) as f:
            data = json.load(f)
        
        niche_name = fname.replace(".json", "")
        apps = data.get("top_apps", [])
        
        if not apps:
            continue
        
        app_data, all_features = build_comparison(niche_name, apps)
        all_niche_data[niche_name] = {"apps": app_data, "features": all_features}
        
        markdown = generate_markdown(niche_name, app_data, all_features)
        all_sections.append(markdown)
    
    # Write combined file
    with open(output_file, "w") as f:
        f.write("# Shopify App Store — Feature Comparison Report\n\n")
        f.write(f"**253 apps across 17 niches** — Feature comparison based on app descriptions.\n\n")
        f.write("## Table of Contents\n\n")
        for section in all_sections:
            title = section.split("\n")[0].replace("# ", "")
            slug = title.lower().replace(" ", "-")
            f.write(f"- [{title}](#{slug})\n")
        f.write("\n---\n\n")
        
        for section in all_sections:
            f.write(section + "\n\n")
    
    print(f"✅ Feature comparison report written to {output_file}")
    print(f"📊 {len(all_niche_data)} niches processed")
    
    # Save structured data for reference
    ref_file = "/Users/yahya/shopify_list/feature_comparison_data.json"
    with open(ref_file, "w") as f:
        json.dump(all_niche_data, f, indent=2)
    print(f"📋 Structured data saved to {ref_file}")

if __name__ == "__main__":
    main()