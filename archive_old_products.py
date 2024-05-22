import xmlrpc.client
from datetime import datetime, timedelta
import csv
import os
import signal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = os.getenv('URL')
db = os.getenv('DB')
username = os.getenv('FLECTRA_USERNAME')
password = os.getenv('FLECTRA_PASSWORD')
timeout = 60  # seconds

run_level = 'DEBUG'

# Custom XML-RPC transport to set timeout and handle HTTPS properly
class TimeoutTransport(xmlrpc.client.SafeTransport):
    """
    Custom XML-RPC transport to set timeout and handle HTTPS properly.
    This class uses SafeTransport to ensure HTTPS connections.
    """
    def __init__(self, timeout=60, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout

    def make_connection(self, host):
        """Make a secure connection with a timeout."""
        conn = super().make_connection(host)
        conn.timeout = self.timeout
        return conn

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=TimeoutTransport(timeout))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', transport=TimeoutTransport(timeout))

# List to store products and progress
products_with_no_recent_activity = []

def check_product_inactivity(product, two_years_ago):
    """
    Checks if a product has no sales, purchase activity, or stock in the last two years.
    Also checks if the product was created at least 1 year ago.
    """
    product_id = product['id']

    # Check for recent sales orders
    if models.execute_kw(db, uid, password,
                         'sale.order.line', 'search_count',
                         [[('product_id', '=', product_id), ('create_date', '>=', two_years_ago)]]) > 0:
        if run_level == 'DEBUG':
            print("Returning because sale in past 2 years")
        return False

    # Check for recent purchase orders
    if models.execute_kw(db, uid, password,
                         'purchase.order.line', 'search_count',
                         [[('product_id', '=', product_id), ('create_date', '>=', two_years_ago)]]) > 0:
        if run_level == 'DEBUG':
            print("Returning because purchase in past 2 years")
        return False
    
    # Check if the product was created at least 1 year ago
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if product.get('create_date', one_year_ago) > one_year_ago:
        if run_level == 'DEBUG':
            print("Returning because product is less than 1 year old")
        return False

    # Check for stock availability
    stock_qty = models.execute_kw(db, uid, password,
                                  'stock.quant', 'search_read',
                                  [[('product_id', '=', product_id), 
                                    ('location_id.usage', '=', 'internal')]],  # Exclude locations that are not internal
                                  {'fields': ['quantity']})
    if any(quant['quantity'] > 0 for quant in stock_qty):
        if run_level == 'DEBUG':
            print("Returning because inventory found")
        return False

    if run_level == 'DEBUG':
            print("Returning, passed all checks")
    return True

def debug_and_archive_reordering_rules(product_template_id):
    """
    Archives the reordering rules associated with the product template.
    Outputs the IDs found for reordering rules before marking them as inactive.
    """
    try:
        # Search for active reordering rules
        reordering_rules = models.execute_kw(db, uid, password,
                                             'stock.warehouse.orderpoint', 'search_read',
                                             [[('product_id.product_tmpl_id', '=', product_template_id)]],
                                             {'fields': ['id', 'name']})
        print(f"Found reordering rules for product {product_template_id}: {reordering_rules}")
        
        # Archive each reordering rule
        for rule in reordering_rules:
            models.execute_kw(db, uid, password,
                              'stock.warehouse.orderpoint', 'write',
                              [[rule['id']], {'active': False}])
            print(f"Reordering rule {rule['id']} archived successfully.")
    except Exception as e:
        print(f"Failed to archive reordering rules for product {product_template_id}: {e}")


def archive_product(product_template_id):
    """
    Archives the product if it has no recent activity.
    """
    try:
        # Archive reordering rules before archiving the product
        debug_and_archive_reordering_rules(product_template_id)

        models.execute_kw(db, uid, password,
                          'product.template', 'write',
                          [[product_template_id], {'active': False}])
        print(f"Product {product_template_id} archived successfully.")
    except Exception as e:
        print(f"Failed to archive product {product_template_id}: {e}")

def get_products_with_no_recent_activity():
    """
    Retrieves products having no sales, purchases, or stock for more than 2 years.
    Generates a CSV report for these products and archives them if they meet the criteria.
    """
    print("Authenticating and connecting to the server...")

    two_years_ago = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')

    global products_with_no_recent_activity
    try:
        print("Retrieving all products...")

        all_products = models.execute_kw(db, uid, password,
                                         'product.product', 'search_read',
                                         [[('active', '=', True)]], {'fields': ['id', 'name', 'default_code', 'create_date', 'product_tmpl_id']})
        
        print(f"Total products retrieved: {len(all_products)}")

        if all_products:
            for product in all_products:
                print(f"Processing product 1/{len(all_products)}: {product['name']}")
                if check_product_inactivity(product, two_years_ago):
                    print("Will be archived...")
                    products_with_no_recent_activity.append(product)
                    # Archive the product and reordering rules
                    archive_product(product['product_tmpl_id'][0])
                #return  # Exit after processing the first product for debugging

        print(f"Found {len(products_with_no_recent_activity)} product(s) matching criteria.")
        generate_csv_report()

    except Exception as e:
        print(f"Failed to retrieve products: {e}")
        return

def generate_csv_report():
    """
    Generates a CSV report for products with no recent activity.
    """
    report_path = 'products_with_no_recent_activity.csv'
    print(f"Generating CSV report: {report_path}")

    try:
        with open(report_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'DefaultCode'])
            
            for product in products_with_no_recent_activity:
                writer.writerow([
                    product['name'],
                    product.get('default_code', 'N/A')
                ])
        
        print(f"Report generated successfully: {report_path}")
    except Exception as e:
        print(f"Failed to generate report: {e}")

def signal_handler(sig, frame):
    """
    Signal handler to catch termination signals and save progress.
    """
    print("Termination signal received. Saving progress...")
    generate_csv_report()
    print("Exiting gracefully.")
    exit(0)

if __name__ == "__main__":
    # Setup signal handling for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    get_products_with_no_recent_activity()