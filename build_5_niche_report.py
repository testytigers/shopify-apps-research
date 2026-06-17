#!/usr/bin/env python3
"""Build feature comparison for 5 specific niches only."""

import json
import os
import re

# Feature keyword extraction for each niche
FEATURE_PATTERNS = {
    "wishlist": ["wishlist", "save", "favorite", "share", "price alert", "notify", "email", "social", "product", "guest", "analytics", "back in stock", "restock", "tag", "collection", "pos", "loyalty", "points", "reward"],
    "out_of_stock_alerts": ["back in stock", "restock", "notify", "pre order", "low stock", "alert", "waitlist", "hide", "push down", "sort", "email", "sms", "whatsapp", "auto", "ai", "collection", "404"],
    "discounts_bundles": ["bundle", "bogo", "buy one get", "buy x get y", "volume discount", "tiered", "quantity", "break", "gift", "free gift", "offer", "discount", "upsell", "aoi", "add on", "popup", "faq", "social", "checkout", "shipping"],
    "bulk_operations": ["bulk", "edit", "import", "export", "csv", "delete", "product", "metafield", "tag", "image", "photo", "ai", "preview", "undo", "inventory", "migration", "data", "order", "collection", "batch", "background", "remove"],
}

# Checkout-specific: extract from app name directly since descriptions are too short
CHECKOUT_KEYWORDS = [
    "checkout", "rules", "customize", "payment", "method", "hide", "sort", 
    "order status", "thank you", "analytics", "heatmap", "replay", "ai", 
    "recording", "upsell", "post purchase", "discount", "deposit", "split",
    "express", "block", "branding", "banner", "custom", "smart", "order"
]

def extract_features_checkout(app_name, description):
    """Extract features from checkout app name + description."""
    combined = f"{app_name} {description}".lower()
    features = []
    for kw in CHECKOUT_KEYWORDS:
        if kw in combined:
            features.append(kw.replace(" ", "-"))
    return list(set(features))

def extract_features(description, niche):
    """Extract feature keywords from description."""
    desc_lower = description.lower()
    features = []
    for kw in FEATURE_PATTERNS.get(niche, []):
        if kw in desc_lower:
            features.append(kw.replace(" ", "-"))
    return list(set(features))

def build_report(niche_name, apps):
    """Build comparison for one niche."""
    all_features = set()
    app_data = []
    
    for app in apps:
        if niche_name == "payment_checkout":
            features = extract_features_checkout(app["name"], app.get("description", ""))
        else:
            features = extract_features(app.get("description", ""), niche_name)
        
        app_data.append({
            "name": app["name"],
            "rating": app.get("rating", "N/A"),
            "reviews": app.get("reviews", "N/A"),
            "pricing": app.get("pricing", "N/A"),
            "features": features,
            "description": app.get("description", "")
        })
        all_features.update(features)
    
    return app_data, sorted(all_features)

def generate_section(niche_name, app_data, all_features):
    """Generate markdown section for one niche."""
    lines = []
    title = niche_name.replace("_", " ").title()
    lines.append(f"## {title}")
    lines.append("")
    
    # Feature comparison table
    lines.append("### Feature Comparison")
    lines.append("")
    lines.append("| App | Rating | Reviews | Pricing | Features |")
    lines.append("|---|---|---|---|---|")
    
    for app in app_data:
        feature_tags = ", ".join([f"`{f}`" for f in app["features"]]) if app["features"] else "N/A"
        lines.append(f"| {app['name']} | {app['rating']} | {app['reviews']} | {app['pricing']} | {feature_tags} |")
    
    # Feature matrix
    lines.append("")
    lines.append("### Feature Matrix")
    lines.append("")
    header = "| App | " + " | ".join([f"`{f}`" for f in all_features]) + " |"
    lines.append(header)
    sep = "| --- |" + " | " + " |".join(["-" * 8 for _ in all_features]) + " |"
    lines.append(sep)
    
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
    numeric_apps = []
    for a in app_data:
        rv = a["reviews"]
        if isinstance(rv, str) and rv.isdigit():
            numeric_apps.append((int(rv), a))
        elif isinstance(rv, (int, float)):
            numeric_apps.append((int(rv), a))
    numeric_apps.sort(key=lambda x: -x[0])
    top5 = [a for _, a in numeric_apps[:5]]
    for i, app in enumerate(top5, 1):
        lines.append(f"{i}. **{app['name']}** — {app['rating']} | {app['reviews']} reviews | {app['pricing']}")
        lines.append(f"   _{app['description']}_")
    
    lines.append("")
    return "\n".join(lines)

def main():
    niches_dir = "/Users/yahya/shopify_list/niches/"
    output_file = "/Users/yahya/shopify_list/feature_comparison_5_niches.md"
    
    target_niches = ["wishlist", "out_of_stock_alerts", "discounts_bundles", "payment_checkout", "bulk_operations"]
    niche_display_names = {
        "wishlist": "Wishlist",
        "out_of_stock_alerts": "Out of Stock Alerts",
        "discounts_bundles": "Discounts & Bundles",
        "payment_checkout": "Checkout Customization",
        "bulk_operations": "Bulk Operations",
    }
    
    all_sections = []
    
    for niche in target_niches:
        filepath = os.path.join(niches_dir, f"{niche}.json")
        if not os.path.exists(filepath):
            print(f"⚠️ Skipping {niche}: file not found")
            continue
        
        with open(filepath) as f:
            data = json.load(f)
        
        apps = data.get("top_apps", [])
        app_data, all_features = build_report(niche, apps)
        markdown = generate_section(niche_display_names.get(niche, niche), app_data, all_features)
        all_sections.append(markdown)
    
    # Write combined file
    with open(output_file, "w") as f:
        f.write("# Shopify App Store — Feature Comparison (5 Niches)\n\n")
        f.write("Comparison of **5 niches** with feature matrices for all apps.\n\n")
        f.write("## Table of Contents\n\n")
        for section in all_sections:
            title = section.split("\n")[0].replace("# ", "")
            slug = title.lower().replace(" ", "-")
            f.write(f"- [{title}](#{slug})\n")
        f.write("\n---\n\n")
        
        for section in all_sections:
            f.write(section + "\n\n")
    
    print(f"✅ Report written to {output_file}")
    
    # Count total apps
    total_apps = 0
    for niche in target_niches:
        fp = os.path.join(niches_dir, f"{niche}.json")
        if os.path.exists(fp):
            with open(fp) as f:
                d = json.load(f)
            total_apps += len(d.get("top_apps", []))
    print(f"📊 {total_apps} apps across {len(all_sections)} niches")

if __name__ == "__main__":
    main()