// Order Service for SEC-401
// Missing proper error handling and validation

class OrderService {
    // Missing JSDoc
    async processOrder(orderId) {
        // Swallowed exception (empty catch block)
        try {
            const order = await db.query(`SELECT * FROM orders WHERE id = ${orderId}`);
            await this.updateInventory(order.items);
        } catch (error) {
            // Empty catch - swallows exception
        }
        
        // Overly generic exception handling
        try {
            await this.sendNotification(order.userId);
        } catch (Exception) {
            // Too generic - should catch specific exceptions
            console.log('Error');
        }
        
        // Missing retry logic for external service
        const result = await externalService.call(orderId);
        // No retry, no circuit breaker, no fallback
        
        return result;
    }
    
    // Inefficient data structure
    async findOrder(items) {
        // Using array for lookup - should use Set/Map
        const processedItems = [];
        for (let item of items) {
            if (processedItems.indexOf(item.id) === -1) { // O(n) lookup
                processedItems.push(item.id);
            }
        }
    }
    
    // Large object creation in loop
    async processOrders(orders) {
        for (let order of orders) {
            // Creating large object inside loop
            const largeObject = {
                data: new Array(10000).fill(0),
                metadata: { /* large object */ }
            };
            await this.saveOrder(order, largeObject);
        }
    }
    
    // Missing transaction boundary
    async createOrderWithItems(orderData, items) {
        // Should be in transaction
        await db.query(`INSERT INTO orders ...`);
        for (let item of items) {
            await db.query(`INSERT INTO order_items ...`);
        }
        // If second insert fails, first insert is not rolled back
    }
    
    // Blocking call in async context
    async fetchOrderData(orderId) {
        // Blocking synchronous operation
        const data = fs.readFileSync(`/tmp/order_${orderId}.json`);
        return JSON.parse(data);
    }
    
    // Missing health check
    async healthCheck() {
        // Should implement health check for monitoring
        return { status: 'ok' };
    }
}

module.exports = new OrderService();

