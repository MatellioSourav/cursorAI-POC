// Cart Controller for SEC-407 E-Commerce Application
// This code has multiple issues to test all SME feedback checks

// Hardcoded database password
const DB_PASSWORD = 'cart_db_pass_456';

class CartController {
    // Missing JSDoc documentation
    
    async addToCart(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const { productId, quantity } = req.body;
        const userId = req.user?.id || req.body.userId; // Insecure - can be spoofed
        
        // Missing input validation
        // Missing sanitization
        
        // FIXED: Using parameterized query to prevent SQL injection
        const product = await db.query(
            `SELECT * FROM products WHERE id = ? AND stock_quantity >= ?`,
            [productId, quantity]
        );
        
        if (!product.length) {
            return res.status(400).json({ 
                error: 'Product not found or out of stock',
                productId: productId, // Internal ID exposure
                stock: product[0]?.stock_quantity // Internal data
            });
        }
        
        // Missing object-level authorization
        // User can add items to any user's cart
        
        // Missing transaction boundary
        // No rollback on error
        
        // FIXED: Using parameterized queries
        const existingItem = await db.query(
            `SELECT * FROM cart_items WHERE cart_id = (SELECT id FROM carts WHERE user_id = ?) AND product_id = ?`,
            [userId, productId]
        );
        
        if (existingItem.length) {
            // FIXED: Using parameterized query
            await db.query(
                `UPDATE cart_items SET quantity = quantity + ? WHERE id = ?`,
                [quantity, existingItem[0].id]
            );
        } else {
            // FIXED: Using parameterized query
            await db.query(
                `INSERT INTO cart_items (cart_id, product_id, quantity, price_at_time) 
                 VALUES ((SELECT id FROM carts WHERE user_id = ?), ?, ?, ?)`,
                [userId, productId, quantity, product[0].price]
            );
        }
        
        // Missing error handling
        // Missing stock validation after update
        
        // Logging sensitive data
        console.log('Item added to cart:', { 
            userId, 
            productId, 
            quantity,
            dbPassword: DB_PASSWORD // Secret exposure
        });
        
        return res.json({ success: true });
    }
    
    async getCart(req, res) {
        // Missing authentication
        // Missing authorization
        
        const userId = req.user?.id || req.params.userId;
        
        // Missing input validation
        
        // FIXED: Using parameterized query
        const cart = await db.query(
            `SELECT * FROM carts WHERE user_id = ?`,
            [userId]
        );
        
        if (!cart.length) {
            return res.json({ cart: { items: [] } });
        }
        
        // Missing object-level authorization
        // User can view any user's cart
        
        // N+1 query problem
        const items = await db.query(
            `SELECT * FROM cart_items WHERE cart_id = ${cart[0].id}`
        );
        
        let subtotal = 0;
        for (let item of items) {
            // Query inside loop - performance issue
            item.product = await db.query(
                `SELECT * FROM products WHERE id = ${item.product_id}`
            );
            item.subtotal = item.quantity * item.price_at_time;
            subtotal += item.subtotal;
        }
        
        // Hardcoded values - should be in config
        const taxRate = 0.10; // 10% tax
        const shippingThreshold = 50; // Free shipping over $50
        const shippingCost = 5.00; // Standard shipping
        
        // Added: Calculate totals (but still has N+1 query issue)
        // TODO: Optimize queries to avoid N+1 problem
        
        const tax = subtotal * taxRate;
        const shipping = subtotal >= shippingThreshold ? 0 : shippingCost;
        const total = subtotal + tax + shipping;
        
        // Missing error handling
        // Missing validation
        
        return res.json({
            cart: {
                id: cart[0].id,
                items: items,
                subtotal: subtotal,
                tax: tax,
                shipping: shipping,
                total: total,
                freeShippingEligible: subtotal >= shippingThreshold
            }
        });
    }
    
    async updateCartItem(req, res) {
        // Missing authentication
        // Missing authorization
        
        const { itemId } = req.params;
        const { quantity } = req.body;
        const userId = req.user?.id;
        
        // Missing input validation
        // Missing stock validation
        
        // SQL injection vulnerability
        const item = await db.query(
            `SELECT * FROM cart_items WHERE id = ${itemId}`
        );
        
        if (!item.length) {
            return res.status(404).json({ error: 'Cart item not found' });
        }
        
        // Missing object-level authorization
        // User can update any cart item
        
        // Missing transaction boundary
        // FIXED: Using parameterized query
        await db.query(
            `UPDATE cart_items SET quantity = ? WHERE id = ?`,
            [quantity, itemId]
        );
        
        // Missing error handling
        // Missing stock check
        
        return res.json({ success: true });
    }
    
    async removeFromCart(req, res) {
        // Missing authentication
        // Missing authorization
        
        const { itemId } = req.params;
        
        // Missing input validation
        
        // FIXED: Using parameterized query
        await db.query(
            `DELETE FROM cart_items WHERE id = ?`,
            [itemId]
        );
        
        // Missing object-level authorization
        // Missing error handling
        // Missing validation that item belongs to user's cart
        
        return res.json({ success: true });
    }
}

module.exports = new CartController();

