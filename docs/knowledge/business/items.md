## What is an Item?
An item represents a product or service tracked in EZ Inventory. Every item has a unique code, a category, a unit of measure, and both a purchase price and a selling price.

## Item Types
Items can be one of two types:
- **PRODUCT** — A physical good that is bought and sold (e.g., Electronics, Raw Materials).
- **SERVICE** — An intangible offering billed to customers (e.g., Installation, Consultation).

## Item Status
Items have an Active or Inactive status. Inactive items are soft-deleted — they are hidden from catalog views but their data is retained. Use the toggle feature to enable or disable an item.

## Required Fields When Adding an Item
- **Name** — Human-readable item name.
- **Item Code** — Unique identifier. Auto-generated as ITM-XXXX if not provided.
- **Category** — Grouping such as Electronics, Furniture, Raw Material.
- **Unit of Measure** — PCS, KG, BOX, LITRE, etc.
- **Purchase Price** — Cost price used for procurement.
- **Selling Price** — The price charged to customers.

## Optional Fields
Brand, Manufacturer, SKU, Barcode, HSN/SAC Code, Tax Percentage, Discount Percentage, Description.

## Adding a New Item
To add an item, provide Name, Category, Unit, Purchase Price, and Selling Price at minimum. An Item Code will be auto-generated if omitted. The item defaults to Active status on creation.

## Bulk Import
Use the bulk import template to add multiple items at once. Download the Excel template, fill in item data, and upload via the Bulk Import feature. The template endpoint is GET /v1/items/template.
