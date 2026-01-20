// Order Service for SEC-407 E-Commerce Application
// This code has multiple issues to test all SME feedback checks

// Hardcoded payment gateway URL - should be in config
const PAYMENT_GATEWAY_URL = 'https://api.payment-gateway.com';

class OrderService {
    async createOrder(userId, shippingAddress, paymentMethod) {
        // Swallowed exception (empty catch block)
        try {
            // FIXED: Using parameterized query
            const cart = await db.query(
                `SELECT * FROM carts WHERE user_id = ?`,
                [userId]
            );
            
            if (!cart.length || !cart[0].items) {
                throw new Error('Cart is empty');
            }
            
            // Missing transaction boundary
            // Multiple operations without transaction
            
            // Operation 1: Validate stock - FIXED: Using parameterized query
            for (let item of cart[0].items) {
                const product = await db.query(
                    `SELECT stock_quantity FROM products WHERE id = ?`,
                    [item.product_id]
                );
                if (product[0].stock_quantity < item.quantity) {
                    throw new Error('Insufficient stock');
                }
            }
            
            // Operation 2: Create order - FIXED: Using parameterized query
            const order = await db.query(
                `INSERT INTO orders (user_id, status, total_amount, shipping_address) 
                 VALUES (?, 'pending', ?, ?)`,
                [userId, cart[0].total, JSON.stringify(shippingAddress)]
            );
            
            // Operation 3: Create order items - FIXED: Using parameterized queries
            for (let item of cart[0].items) {
                await db.query(
                    `INSERT INTO order_items (order_id, product_id, quantity, price_at_time) 
                     VALUES (?, ?, ?, ?)`,
                    [order.insertId, item.product_id, item.quantity, item.price_at_time]
                );
                
                // Operation 4: Update inventory - FIXED: Using parameterized query
                await db.query(
                    `UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?`,
                    [item.quantity, item.product_id]
                );
            }
            
            // Operation 5: Clear cart - FIXED: Using parameterized query
            await db.query(
                `DELETE FROM cart_items WHERE cart_id = ?`,
                [cart[0].id]
            );
            
            // If any operation fails, others are not rolled back
            return { orderId: order.insertId, status: 'pending' };
            
        } catch (error) {
            // FIXED: Proper error handling instead of empty catch
            console.error('Error creating order:', error.message);
            throw error; // Re-throw to caller
        }
    }
    
    async getOrderDetails(orderId, userId) {
        // Missing object-level authorization check
        // User can view any order
        
        // FIXED: Better error handling
        try {
            // FIXED: Using parameterized query
            const order = await db.query(
                `SELECT * FROM orders WHERE id = ?`,
                [orderId]
            );
            
            if (!order.length) {
                throw new Error('Order not found');
            }
            
            // Missing authorization check
            // if (order[0].user_id !== userId) { throw error }
            
            // FIXED: Using parameterized query
            const items = await db.query(
                `SELECT * FROM order_items WHERE order_id = ?`,
                [orderId]
            );
            
            // Still has N+1 query problem (intentional - to test bot detection)
            for (let item of items) {
                item.product = await db.query(
                    `SELECT * FROM products WHERE id = ?`,
                    [item.product_id]
                );
            }
            
            return {
                order: order[0],
                items: items
            };
            
        } catch (error) {
            // FIXED: Better error handling with specific error types
            if (error.code === 'NOT_FOUND') {
                throw new Error('Order not found');
            } else if (error.code === 'DB_ERROR') {
                throw new Error('Database error occurred');
            } else {
                throw error; // Re-throw original error
            }
        }
    }
    
    async processPayment(orderId, paymentData) {
        // External API call without retry logic
        // Using hardcoded URL instead of config
        const paymentResult = await fetch(`${PAYMENT_GATEWAY_URL}/charge`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.PAYMENT_API_KEY || 'hardcoded_key'}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paymentData)
        });
        // Missing try/catch
        // Missing timeout
        // Missing fallback
        // Missing retry logic
        
        return paymentResult.json();
    }
    
    async updateOrderStatus(orderId, status) {
        // FIXED: Consistent error handling
        try {
            // FIXED: Using parameterized query
            const result = await db.query(
                `UPDATE orders SET status = ? WHERE id = ?`,
                [status, orderId]
            );
            return result;
        } catch (error) {
            // FIXED: Consistent error propagation - always throw
            throw error;
        }
    }
    
    // Missing health check
    // No method to check if service is healthy
    
    // Blocking call in async context
    async sendOrderConfirmation(orderId) {
        const order = await this.getOrderDetails(orderId);
        
        // Synchronous blocking operation
        const emailResult = require('child_process').execSync(
            `curl -X POST http://email-service.com/send -d '${JSON.stringify(order)}'`
        );
        
        return emailResult.toString();
    }
}

module.exports = new OrderService();

