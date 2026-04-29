# EZ Inventory — Full Application Navigation & Module Guide

## Dashboard

The Dashboard is the home screen of EZ Inventory. It shows a summary of key business metrics including stock levels, recent orders, pending approvals, and sales overview.

**How to get there:** Click "Dashboard" in the main menu or [go to Dashboard](/dashboard).

---

## Vendor Portal

### What is the Vendor Portal?

The Vendor Portal is a dedicated section for vendors (suppliers) to manage their interactions with your business. Vendors can view new orders placed to them, manage ASNs, and track sales returns.

**How to get there:** [Go to Vendor Portal](/vendor/dashboard)

### Vendor Dashboard

Shows an overview of vendor activity — pending orders, ASNs, and return requests.
[Go to Vendor Dashboard](/vendor/dashboard)

### New Orders (Vendor)

Lists all new purchase orders sent to the vendor that are awaiting acknowledgement or fulfillment.

- To view all new orders: [Go to New Orders](/vendor/new-orders)
- To open a specific order form: [Go to Order Form](/vendor/new-orders/form)

### ASN — Advance Shipment Notice

Vendors can create and manage ASNs (Advance Shipment Notices) to notify the buyer before goods are dispatched.
[Go to ASN](/vendor/asn)

### Sales Returns (Vendor)

Vendors can view and respond to purchase return requests raised by the buyer.
[Go to Vendor Sales Returns](/vendor/sales-returns)

---

## Items

### What is the Items Module?

The Items module is the product/service catalog of EZ Inventory. Every product or service that is bought or sold must first exist as an Item. Items have a code, category, unit of measure, purchase price, and selling price.

**How to get there:** Click "Items" in the menu or [go to Items](/items).

### View All Items

See the full list of all active and inactive items in the catalog.
[Go to Items List](/items)

### Create a New Item

To add a new product or service to the catalog:

1. Go to Items → click **"+ Create"** or [go directly to the Create Item form](/items/create)
2. Fill in: Name, Category, Unit of Measure, Purchase Price, Selling Price
3. Optionally add: Brand, SKU, Barcode, HSN/SAC Code, Tax %, Description
4. Click **Save**

### Edit an Existing Item

To update an item's details, go to the Items list, find the item, and click **Edit**, or navigate to `/items/edit/{id}`.

---

## Stock

### What is the Stock Module?

The Stock module tracks the current inventory levels for all items across your warehouse or store. You can view stock on hand, review the stock ledger (movement history), and make adjustments.

**How to get there:** [Go to Stock](/stock)

### View Current Stock

See all items and their current available quantities.
[Go to Stock Overview](/stock)

### Stock Ledger

The Stock Ledger shows the full history of stock movements — every receipt, sale, adjustment, and transfer that affected stock levels.
[Go to Stock Ledger](/stock/ledger)

### Stock Adjustment

Use Stock Adjustment to manually correct stock quantities (e.g., after a physical count or to write off damaged goods).

- View adjustments: [Go to Stock Adjustment](/stock/adjustment)
- Create a new adjustment: [Go to Create Adjustment](/stock/adjustment/create)

---

## Purchases

### What is the Purchases Module?

The Purchases module manages the full procurement lifecycle — from raising a purchase request to receiving goods. It has four sub-modules: Purchase Request (PRQ), Purchase Order (PO), Goods Receipt Note (GRN), and Purchase Return.

**How to get there:** [Go to Purchases](/purchases)

### Purchase Request (PRQ)

A PRQ is a formal internal request to procure goods before a Purchase Order is issued. It is the first step in the procurement process and typically requires approval.

- View all PRQs: [Go to PRQ List](/purchases/prq)
- Create a new PRQ: [Go to Create PRQ](/purchases/prq/form)

### Purchase Order (PO)

A Purchase Order is issued to a vendor after a PRQ is approved. It is a legally binding document confirming what is being ordered, at what price, and by when.

- View all Purchase Orders: [Go to PO List](/purchases/order)
- Create a new PO: [Go to Create PO](/purchases/order/form)

### Goods Receipt Note (GRN)

A GRN is created when goods arrive from a vendor. It confirms that the items received match the Purchase Order.

- View all GRNs: [Go to GRN List](/purchases/grn)
- Create a new GRN: [Go to Create GRN](/purchases/grn/form)

### Purchase Return

Use Purchase Return to send items back to a vendor due to defects, wrong delivery, or excess quantity.

- View all Purchase Returns: [Go to Purchase Returns](/purchases/return)
- Create a new Purchase Return: [Go to Create Purchase Return](/purchases/return/form)

---

## Sales

### What is the Sales Module?

The Sales module manages the full order-to-cash process. It includes Sales Orders, Invoices, Delivery Notes, and Sales Returns.

**How to get there:** [Go to Sales](/sales/order)

### Sales Order

A Sales Order is raised when a customer places an order for goods or services.

- View all Sales Orders: [Go to Sales Orders](/sales/order)
- Create a new Sales Order: [Go to Create Sales Order](/sales/order/form)

### Invoice

An Invoice is generated for a customer after a Sales Order is confirmed. It is the bill sent to the customer.

- View all Invoices: [Go to Invoices](/sales/invoice)
- Create a new Invoice: [Go to Create Invoice](/sales/invoice/form)

### Delivery

A Delivery Note is created when goods are dispatched to a customer.

- View all Deliveries: [Go to Deliveries](/sales/delivery)
- Create a new Delivery: [Go to Create Delivery](/sales/delivery/form)

### Sales Return

Use Sales Return when a customer returns goods due to defects, wrong delivery, or change of mind.

- View all Sales Returns: [Go to Sales Returns](/sales/return)
- Create a new Sales Return: [Go to Create Sales Return](/sales/return/form)

---

## Payments

### What is the Payments Module?

The Payments module tracks all financial transactions related to sales — customer payments received, advance payments, and credit notes.

**How to get there:** [Go to Payments](/payment)

### Payments List

View all payments received from customers against invoices.
[Go to Payments](/payment)

### Advance Payment

Record a payment received from a customer before an invoice is raised.
[Go to Advance Payments](/payment/advance)

### Credit Note

A Credit Note is issued to a customer when a refund or discount adjustment is needed (e.g., after a sales return).
[Go to Credit Notes](/payment/credit-note)

---

## Reports

### What is the Reports Module?

The Reports module provides business intelligence reports across purchases, sales, stock, and payments. Use it to analyse trends, monitor performance, and make informed decisions.

**How to get there:** [Go to Reports](/reports)

Available report types include stock reports, purchase reports, sales reports, and payment summaries.

---

## Documents

### What is the Documents Module?

The Documents module is a file manager where you can upload, store, and organise files related to your business — such as contracts, quotations, invoices, and certificates.

**How to get there:** [Go to Documents](/documents)

---

## Approval Console

### What is the Approval Console?

The Approval Console is where approvers review and act on pending approval requests — such as PRQs, Purchase Orders, and other transactions that require sign-off before processing.

**How to get there:** [Go to Approval Console](/approval)

If you have pending approvals, they will appear here. You can Approve or Reject each request and add comments.

---

## Settings

### What is the Settings Module?

Settings is where administrators configure the application — company profile, tax settings, units of measure, categories, number series, and other master data.

**How to get there:** [Go to Settings](/settings)

---

## User Management (Admin)

### What is User Management?

The User Management section is for administrators to manage user accounts — create new users, assign roles and permissions, and control who has access to which modules.

**How to get there:** [Go to User Management](/admin/users)

### View All Users

See a list of all system users and their roles.
[Go to Users List](/admin/users)

### Create or Edit a User

- Add a new user: [Go to Create User](/admin/users/form)
- Edit an existing user: Navigate to `/admin/users/form/{id}`

### User Profile

View and update a user's profile details.
[Go to User Profile](/admin/users/profile)

### Calendar

View the company or user calendar for scheduled events and tasks.
[Go to Calendar](/admin/user/calendar)

### Subscriptions

Manage your subscription plan and billing details.
[Go to Subscriptions](/admin/subscriptions)

---

## AI Chat Assistant

### What is the AI Chat?

The AI Chat is an intelligent assistant built into EZ Inventory that can answer questions about your business data, explain workflows, and guide you through the application.

**How to get there:** [Go to AI Chat](/ai-chat)

---

## Quick Reference — Where to Go for Common Tasks

| What do you want to do? | Where to go |
|---|---|
| Check current stock levels | [Stock](/stock) |
| See stock movement history | [Stock Ledger](/stock/ledger) |
| Correct a stock count | [Stock Adjustment](/stock/adjustment/create) |
| Request items to be purchased | [Create PRQ](/purchases/prq/form) |
| Issue a Purchase Order to vendor | [Create PO](/purchases/order/form) |
| Record goods received from vendor | [Create GRN](/purchases/grn/form) |
| Return goods to vendor | [Create Purchase Return](/purchases/return/form) |
| Raise a customer Sales Order | [Create Sales Order](/sales/order/form) |
| Generate a customer Invoice | [Create Invoice](/sales/invoice/form) |
| Record goods dispatched | [Create Delivery](/sales/delivery/form) |
| Process a customer return | [Create Sales Return](/sales/return/form) |
| Record a customer payment | [Payments](/payment) |
| Issue a credit note | [Credit Notes](/payment/credit-note) |
| Add a new item to catalog | [Create Item](/items/create) |
| Approve a pending request | [Approval Console](/approval) |
| Add a new user | [Create User](/admin/users/form) |
| View business reports | [Reports](/reports) |
| Upload or manage files | [Documents](/documents) |
| Configure system settings | [Settings](/settings) |
