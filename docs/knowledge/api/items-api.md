## Get All Items
Endpoint: POST /v1/items/all?page=0&size=10
Returns a paginated list of inventory items with optional filters.
Request body fields (all optional): active (boolean, default true), itemType (PRODUCT or SERVICE), brand (string), category (string).
Default values: page=0, size=10, active=true.

## Search Items
Endpoint: POST /v1/items/search
Keyword search across item Name and Description fields.
Request body: searchQuery (string, required).
Returns matching items regardless of active status.

## Create Item
Endpoint: POST /v1/items
Creates a new inventory item.
Required fields: name, category, unitOfMeasure, purchasePrice, sellingPrice.
Optional fields: itemType (default PRODUCT), brand, manufacturer, itemCode, sku, barcode, hsnSacCode, taxPercentage, discountPercentage, description.
If itemCode is omitted, one is auto-generated as ITM-XXXX.

## Update Item
Endpoint: POST /v1/items/{id}/update
Updates an existing item by numeric ID. Only provide the fields you want to change.

## Toggle Item Status
Endpoint: POST /v1/items/{id}/status?active=true
Enables (active=true) or disables (active=false) an item by numeric ID. This is a soft delete — data is retained.

## Get Bulk Import Template
Endpoint: GET /v1/items/template
Returns the download URL for the Excel bulk import template.
