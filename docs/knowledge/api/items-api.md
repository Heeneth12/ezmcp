## Get All Items
Use this endpoint to browse or filter the full inventory catalog. Returns a paginated list of items, optionally filtered by type, brand, category, or active status.
Endpoint: POST /v1/items/all?page=0&size=10
Request body fields (all optional): active (boolean, default true), itemType (PRODUCT or SERVICE), brand (string), category (string).
Default values: page=0, size=10, active=true.

## Search Items
Use this endpoint to find items by keyword. Searches across item Name and Description fields and returns matching results.
Endpoint: POST /v1/items/search
Request body: searchQuery (string, required).
Returns matching items regardless of active status.

## Create Item
Use this endpoint to add a new item to the inventory. The item is created as Active by default.
Endpoint: POST /v1/items
Required fields: name, category, unitOfMeasure, purchasePrice, sellingPrice.
Optional fields: itemType (default PRODUCT), brand, manufacturer, itemCode, sku, barcode, hsnSacCode, taxPercentage, discountPercentage, description.
If itemCode is omitted, one is auto-generated as ITM-XXXX.

## Update Item
Use this endpoint to edit the details of an existing item. Only include the fields you want to change.
Endpoint: POST /v1/items/{id}/update
The item must be identified by its numeric ID.

## Toggle Item Status
Use this endpoint to enable or disable an item. Disabling is a soft delete — the item data is retained but hidden from catalog views.
Endpoint: POST /v1/items/{id}/status?active=true
Set active=true to enable, active=false to disable.

## Get Bulk Import Template
Use this endpoint to download the Excel template for bulk item import.
Endpoint: GET /v1/items/template
Returns the download URL for the Excel bulk import template.
