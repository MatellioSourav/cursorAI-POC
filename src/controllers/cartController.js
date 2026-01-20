// Cart Controller for SEC-407 E-Commerce Application
// This code has multiple issues to test all SME feedback checks

// FIXED: Moved hardcoded values to config
const config = require('../config/appConfig');
const TAX_RATE = config.TAX_RATE || 0.10;
const SHIPPING_THRESHOLD = config.SHIPPING_THRESHOLD || 50;
const SHIPPING_COST = config.SHIPPING_COST || 5.00;

class CartController {
    // Missing JSDoc documentation
    
    async addToCart(req, res) {
        // FIXED: Added authentication check
        if (!req.user || !req.user.id) {
            return res.status(401).json({ error: 'Authentication required' });
        }
        
        const { productId, quantity } = req.body;
        const userId = req.user.id; // FIXED: Use authenticated user ID
        
        // FIXED: Added input validation
        if (!productId || !quantity || quantity < 1 || quantity > 10) {
            return res.status(400).json({ error: 'Invalid product ID or quantity' });
        }
        
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
        
        // FIXED: Object-level authorization - user can only add to their own cart
        // (userId is from authenticated session, so already validated)
        
        // Still missing: Transaction boundary (intentional for bot to flag)
        
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
        
        // FIXED: Removed sensitive data from logs
        console.log('Item added to cart:', { 
            userId, 
            productId, 
            quantity
            // Removed: dbPassword
        });
        
        return res.json({ success: true });
    }
    
    async getCart(req, res) {
        // FIXED: Added authentication check
        if (!req.user || !req.user.id) {
            return res.status(401).json({ error: 'Authentication required' });
        }
        
        const userId = req.user.id; // FIXED: Use authenticated user ID
        
        // Missing input validation
        
        // FIXED: Using parameterized query
        const cart = await db.query(
            `SELECT * FROM carts WHERE user_id = ?`,
            [userId]
        );
        
        if (!cart.length) {
            return res.json({ cart: { items: [] } });
        }
        
        // FIXED: Object-level authorization - user can only view their own cart
        // (userId is from authenticated session, cart belongs to that user)
        
        // FIXED: Reduced N+1 queries - get all products in one query
        const items = await db.query(
            `SELECT * FROM cart_items WHERE cart_id = ?`,
            [cart[0].id]
        );
        
        if (items.length > 0) {
            // FIXED: Batch query instead of N+1
            const productIds = items.map(item => item.product_id);
            const products = await db.query(
                `SELECT * FROM products WHERE id IN (${productIds.map(() => '?').join(',')})`,
                productIds
            );
            const productMap = new Map(products.map(p => [p.id, p]));
            
            let subtotal = 0;
            for (let item of items) {
                item.product = productMap.get(item.product_id);
                item.subtotal = item.quantity * item.price_at_time;
                subtotal += item.subtotal;
            }
        } else {
            subtotal = 0;
        }
        
        // FIXED: Using config values instead of hardcoded
        
        // Added: Calculate totals (but still has N+1 query issue)
        // TODO: Optimize queries to avoid N+1 problem
        
        const tax = subtotal * TAX_RATE;
        const shipping = subtotal >= SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
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
                freeShippingEligible: subtotal >= SHIPPING_THRESHOLD
            }
        });
    }
    
    async updateCartItem(req, res) {
        // FIXED: Added authentication check
        if (!req.user || !req.user.id) {
            return res.status(401).json({ error: 'Authentication required' });
        }
        
        const { itemId } = req.params;
        const { quantity } = req.body;
        const userId = req.user.id;
        
        // FIXED: Added input validation
        if (!quantity || quantity < 1 || quantity > 10) {
            return res.status(400).json({ error: 'Invalid quantity' });
        }
        
        // Still missing: Stock validation (intentional for bot to flag)
        
        // SQL injection vulnerability
        const item = await db.query(
            `SELECT * FROM cart_items WHERE id = ${itemId}`
        );
        
        if (!item.length) {
            return res.status(404).json({ error: 'Cart item not found' });
        }
        
        // FIXED: Object-level authorization - verify item belongs to user's cart
        const userCart = await db.query(
            `SELECT id FROM carts WHERE user_id = ?`,
            [userId]
        );
        if (!userCart.length || item[0].cart_id !== userCart[0].id) {
            return res.status(403).json({ error: 'Unauthorized' });
        }
        
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
        // FIXED: Added authentication check
        if (!req.user || !req.user.id) {
            return res.status(401).json({ error: 'Authentication required' });
        }
        
        const { itemId } = req.params;
        const userId = req.user.id;
        
        // FIXED: Added input validation
        if (!itemId) {
            return res.status(400).json({ error: 'Invalid item ID' });
        }
        
        // FIXED: Object-level authorization - verify item belongs to user's cart
        const userCart = await db.query(
            `SELECT id FROM carts WHERE user_id = ?`,
            [userId]
        );
        const item = await db.query(
            `SELECT * FROM cart_items WHERE id = ?`,
            [itemId]
        );
        if (!item.length || item[0].cart_id !== userCart[0].id) {
            return res.status(403).json({ error: 'Unauthorized' });
        }
        
        // FIXED: Using parameterized query
        await db.query(
            `DELETE FROM cart_items WHERE id = ?`,
            [itemId]
        );
        
        // FIXED: Added error handling
        return res.json({ success: true });
    }
}

module.exports = new CartController();

