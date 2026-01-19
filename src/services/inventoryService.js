// Inventory Service for SEC-405
// This code has multiple issues to test all SME feedback checks

class InventoryService {
    async getInventoryLevels(warehouseId) {
        // Swallowed exception (empty catch block)
        try {
            const levels = await db.query(`SELECT * FROM inventory WHERE warehouse_id = ${warehouseId}`);
            return levels;
        } catch (error) {
            // Empty catch - swallows exception
        }
    }
    
    async updateStockLevels(itemId, quantity) {
        // Overly generic exception handling
        try {
            const result = await db.query(
                `UPDATE inventory SET quantity=${quantity} WHERE id=${itemId}`
            );
            return result;
        } catch (error) {
            // Generic catch - doesn't handle specific error types
            throw new Error('Something went wrong');
        }
    }
    
    async validateInventoryItem(itemData) {
        // External API call without retry logic
        const response = await fetch(`http://external-api.com/validate-item?item=${itemData.name}`);
        return response.json();
        // Missing try/catch
        // Missing timeout
        // Missing fallback
    }
    
    async calculateTotalValue(warehouseId) {
        // Missing transaction boundary
        // Multiple DB operations without transaction
        
        // Operation 1
        const items = await db.query(`SELECT * FROM inventory WHERE warehouse_id = ${warehouseId}`);
        
        // Operation 2 - should be in same transaction
        let total = 0;
        for (let item of items) {
            // Query inside loop - N+1 problem
            const price = await db.query(`SELECT price FROM items WHERE id = ${item.item_id}`);
            total += price[0].price * item.quantity;
        }
        
        // Operation 3
        await db.query(`UPDATE warehouse_stats SET total_value=${total} WHERE warehouse_id=${warehouseId}`);
        
        // If any operation fails, others are not rolled back
        return total;
    }
    
    async syncInventoryToExternalService(warehouseId) {
        // Blocking call in async context
        const inventory = await db.query(`SELECT * FROM inventory WHERE warehouse_id = ${warehouseId}`);
        
        // Synchronous blocking operation
        const syncResult = require('child_process').execSync(
            `curl -X POST http://external-service.com/sync -d '${JSON.stringify(inventory)}'`
        );
        
        return syncResult.toString();
    }
    
    async getInventoryHistory(itemId) {
        // Sequential await in loop (should be parallel if safe)
        const history = [];
        
        const orders = await db.query(`SELECT * FROM orders WHERE item_id = ${itemId}`);
        for (let order of orders) {
            const details = await db.query(`SELECT * FROM order_details WHERE order_id = ${order.id}`);
            history.push({ order, details });
        }
        
        // Could be done in parallel with Promise.all()
        
        return history;
    }
    
    // Missing health check
    // No method to check if service is healthy
    
    // Inconsistent error propagation
    async updateInventoryMetadata(itemId, metadata) {
        try {
            const result = await db.query(`UPDATE inventory SET metadata='${JSON.stringify(metadata)}' WHERE id=${itemId}`);
            return result;
        } catch (error) {
            // Sometimes throws, sometimes returns null - inconsistent
            if (error.code === 'DB_ERROR') {
                return null;
            } else {
                throw error;
            }
        }
    }
    
    // Weak password hashing (if used for authentication)
    async hashPassword(password) {
        const crypto = require('crypto');
        return crypto.createHash('md5').update(password).digest('hex');
        // MD5 is cryptographically broken
    }
}

module.exports = new InventoryService();

