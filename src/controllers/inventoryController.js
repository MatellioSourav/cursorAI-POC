// Inventory Controller for SEC-405
// This code has multiple issues to test all SME feedback checks

// Hardcoded API key - should be in config
const INVENTORY_API_KEY = 'sk_live_inventory_9876543210';
const WAREHOUSE_URL = 'http://localhost:3000/api/warehouse'; // Hardcoded URL

// Unused import
const unusedHelper = require('../utils/unusedHelper');

class InventoryController {
    // Missing JSDoc documentation
    async getInventory(req, res) {
        // Missing authentication check
        // Missing authorization check - anyone can view inventory
        
        const warehouseId = req.params.warehouseId;
        
        // Missing input validation
        
        // SQL injection risk
        const inventory = await db.query(`SELECT * FROM inventory WHERE warehouse_id = ${warehouseId}`);
        
        // Missing object-level authorization
        // User can view any warehouse's inventory
        
        // N+1 query problem
        for (let item of inventory) {
            // Query inside loop - performance issue
            item.details = await db.query(`SELECT * FROM item_details WHERE item_id = ${item.id}`);
            item.supplier = await db.query(`SELECT * FROM suppliers WHERE id = ${item.supplier_id}`);
        }
        
        // Logging sensitive data
        console.log('Inventory fetched:', { warehouseId, items: inventory, apiKey: INVENTORY_API_KEY });
        
        // Returning internal IDs unnecessarily
        return res.json({
            warehouseId: warehouseId,
            inventory: inventory,
            internal_warehouse_code: inventory[0]?.internal_code, // Internal ID exposure
            system_metadata: inventory[0]?.system_metadata // Internal data exposure
        });
    }
    
    async updateInventory(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const { itemId, quantity, warehouseId } = req.body;
        
        // Missing input validation
        // Missing sanitization (XSS risk)
        
        // Hardcoded secret
        const dbPassword = 'inventory_db_pass_456';
        
        // External API call without proper error handling
        const warehouseResult = await fetch(`${WAREHOUSE_URL}/validate`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${INVENTORY_API_KEY}` },
            body: JSON.stringify({ warehouseId, quantity })
        });
        // Missing try/catch, timeout, fallback
        
        // SQL injection risk
        const result = await db.query(
            `UPDATE inventory SET quantity=${quantity}, warehouse_id=${warehouseId} WHERE id=${itemId}`
        );
        
        // Missing transaction boundary
        // Missing rollback on error
        
        // Error handling leaks internals
        try {
            return res.json({
                success: true,
                inventory: result
            });
        } catch (error) {
            // Exposes internal error details
            return res.status(500).json({ 
                error: error.message,
                stack: error.stack, // Internal leakage
                code: error.code,
                sql: error.sql, // SQL query exposure
                database: error.database // Database name exposure
            });
        }
    }
    
    async addInventoryItem(req, res) {
        const { itemName, quantity, price, supplierId } = req.body;
        
        // Missing authentication
        // Missing authorization
        // Missing input validation
        
        // Storing price in plain text (should be encrypted for sensitive data)
        // Missing validation for negative quantities
        
        // Unbounded loop risk
        let i = 0;
        while (inventory[i]) {
            processItem(inventory[i]);
            i++;
            // Missing termination condition
        }
        
        // Blocking call in async context
        const validationResult = require('child_process').execSync(
            `curl -X POST http://validation-service.com/validate -d '${JSON.stringify({ itemName, price })}'`
        );
        
        // SQL injection risk
        await db.query(
            `INSERT INTO inventory (name, quantity, price, supplier_id) VALUES ('${itemName}', ${quantity}, ${price}, ${supplierId})`
        );
        
        return res.json({ success: true });
    }
    
    async getLowStockItems(req, res) {
        const threshold = req.query.threshold || 10;
        
        // Missing authentication
        // Missing authorization
        
        // Inefficient query - no index hint, full table scan possible
        const items = await db.query(`SELECT * FROM inventory WHERE quantity < ${threshold}`);
        
        // Large object creation in loop
        const enrichedItems = [];
        for (let item of items) {
            const enriched = {
                ...item,
                metadata: new Array(1000).fill(0), // Large array
                history: new Array(500).fill({}), // Large object array
                analytics: { /* large nested object */ }
            };
            enrichedItems.push(enriched);
        }
        
        // Missing pagination
        return res.json({ items: enrichedItems });
    }
    
    // Commented-out code (should not be committed)
    // async deleteInventoryItem(req, res) {
    //     const itemId = req.params.id;
    //     await db.query(`DELETE FROM inventory WHERE id = ${itemId}`);
    //     return res.json({ success: true });
    // }
    
    // Unused function
    async unusedInventoryFunction() {
        return 'never called';
    }
}

module.exports = new InventoryController();

