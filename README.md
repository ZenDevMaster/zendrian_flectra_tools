# Zendrian Flectra Product Inactivity Archiver 🚀

## Purpose

The Zendrian Flectra Product Inactivity Archiver is a Python-based tool designed to help businesses manage their product catalog in Flectra (a fork of Odoo 11). The primary goal is to identify and archive products that have shown no significant activity over a specified period. By archiving inactive products, businesses can keep their product listings clutter-free and up-to-date, improving both customer experience and inventory management.

## Capabilities

1. **Authentication and Connection** 🔒
   - The app authenticates and connects to the Flectra server using credentials securely stored in a `.env` file.
   - Custom XML-RPC transport with connection timeout handling.

2. **Product Inactivity Check** 🕵️‍♂️
   - Retrieves a list of active products from the Flectra server.
   - For each product, checks if it has had any sales or purchase orders in the last two years.
   - Confirms if the product was created at least one year ago.
   - Ensures the product has no stock available in internal locations.

3. **Reordering Rules Management** 🔄
   - Identifies and archives any active reordering rules associated with the product before archiving the product itself.
   - Outputs IDs for reordering rules found to facilitate debugging and verification.

4. **Archiving Products** 🗃️
   - Archives products meeting the inactivity criteria by marking them as inactive in the database.

5. **CSV Report Generation** 📊
   - Generates a CSV report of products that meet the inactivity criteria, listing product names and default codes.
   - Saves the report to a file named `products_with_no_recent_activity.csv`.

6. **Graceful Termination** ✋
   - Handles termination signals (`SIGINT` and `SIGTERM`) to save progress before exiting gracefully.
   - Ensures that no data is lost during unexpected interruptions.

## Example Workflow

1. **Run the Script**:
   - The script authenticates with the Flectra server and retrieves a list of active products.

2. **Check Each Product**:
   - For each product, the script checks for recent sales and purchase activities, creation date, and stock availability.
   
3. **Manage Reordering Rules**:
   - If a product meets the inactivity criteria, the script identifies and archives any associated reordering rules.

4. **Archive the Product**:
   - The product is archived in the Flectra database by marking it as inactive.

5. **Generate Report**:
   - A CSV report of archived products is generated and saved for review.

## Debugging 🐞

- The script provides detailed console output for debugging purposes, including the IDs of reordering rules found and any issues encountered during archiving.

## Requirements 📦

- Python 3.x
- Flectra 1.7 (forked from Odoo 11)
- `python-dotenv` library for loading credentials from the `.env` file.

## Installation ⚙️

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ZenDevMaster/zendrian_flectra_tools.git
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file**:
   ```
   URL=https://flectra.domain
   DB=***
   FLECTRA_USERNAME=***
   FLECTRA_PASSWORD=***
   ```

4. **Run the Script**:
   ```bash
   python unsold_products.py
   ```

## Conclusion 🎉

The Zendrian Flectra Product Inactivity Archiver is an essential tool for businesses using Flectra, helping them maintain a clean and efficient product catalog by automatically archiving inactive products and generating insightful reports.