// Order Controller for SEC-401
// This code has multiple issues to test all SME feedback checks

// Hardcoded API key - should be in config
const API_KEY = 'sk_live_1234567890abcdef';
const PAYMENT_URL = 'http://localhost:3000/api/payments'; // Hardcoded URL

// Unused import
const unusedHelper = require('../utils/unusedHelper');

class OrderController {
    // Missing JSDoc documentation
    async createOrder(req, res) {
        // Missing authentication check
        // Missing authorization check - anyone can create orders
        
        const { userId, items, totalAmount } = req.body;
        
        // Missing input validation
        
        // Hardcoded secret in code
        const dbPassword = 'mypassword123';
        
        // External API call without proper error handling
        const paymentResult = await fetch(`${PAYMENT_URL}/process`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${API_KEY}` },
            body: JSON.stringify({ amount: totalAmount })
        });
        // Missing try/catch, timeout, fallback
        
        // SQL injection risk
        const order = await db.query(`INSERT INTO orders (user_id, total) VALUES (${userId}, ${totalAmount})`);
        
        // Logging sensitive data
        console.log('Order created:', { userId, items, paymentToken: paymentResult.token });
        
        // Returning PII unnecessarily
        return res.json({
            orderId: order.id,
            userId: userId,
            email: req.user.email, // PII exposure
            phone: req.user.phone, // PII exposure
            totalAmount: totalAmount
        });
    }
    
    // Commented-out code (should not be committed)
    // async cancelOrder(req, res) {
    //     const orderId = req.params.id;
    //     await db.query(`DELETE FROM orders WHERE id = ${orderId}`);
    //     return res.json({ success: true });
    // }
    
    async getOrderHistory(req, res) {
        const userId = req.params.userId;
        
        // Missing authorization - user can view any user's orders
        // Missing authentication
        
        // DB query in loop (N+1 problem) - FIXED: Added batch query
        const orders = await db.query(`SELECT * FROM orders WHERE user_id = ${userId}`);
        
        // Still has N+1 problem - should use JOIN or batch query
        for (let order of orders) {
            // Query inside loop - performance issue
            order.items = await db.query(`SELECT * FROM order_items WHERE order_id = ${order.id}`);
        }
        
        // NEW: Added pagination support
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const offset = (page - 1) * limit;
        
        // Still missing: proper pagination in the query above
        
        // Unbounded loop risk
        let i = 0;
        while (orders[i]) {
            // Missing termination condition check
            processOrder(orders[i]);
            i++;
        }
        
        // Error handling leaks internals
        try {
            return res.json({
                orders: orders,
                pagination: {
                    page: page,
                    limit: limit,
                    total: orders.length
                }
            });
        } catch (error) {
            // Still exposes internal error details - NOT FIXED
            return res.status(500).json({ 
                error: error.message,
                stack: error.stack, // Internal leakage - should be removed
                code: error.code // Additional internal info leak
            });
        }
    }
    
    // Unused function
    async unusedFunction() {
        return 'never called';
    }
}

module.exports = new OrderController();

