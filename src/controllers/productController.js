// Product Controller for SEC-407 E-Commerce Application
// This code has multiple issues to test all SME feedback checks

// Hardcoded API keys - should be in config
const PRODUCT_API_KEY = 'prod_api_key_FAKE_123456789';
const IMAGE_STORAGE_URL = 'http://localhost:3000/images'; // Hardcoded URL

// Unused import
const unusedHelper = require('../utils/unusedHelper');

class ProductController {
    // Missing JSDoc documentation
    
    async getProducts(req, res) {
        // Missing authentication check (should be optional for public listing)
        // But should have rate limiting
        
        const { page = 1, limit = 20, category, search, sort } = req.query;
        
        // Missing input validation
        // Missing sanitization (XSS risk in search)
        
        // Added: Basic pagination validation (but still missing other validations)
        if (page < 1 || limit < 1 || limit > 100) {
            return res.status(400).json({ error: 'Invalid pagination parameters' });
        }
        
        // FIXED: Using parameterized queries to prevent SQL injection
        let query = `SELECT * FROM products WHERE 1=1`;
        const params = [];
        
        if (category) {
            query += ` AND category = ?`;
            params.push(category);
        }
        
        if (search) {
            query += ` AND name LIKE ?`;
            params.push(`%${search}%`);
        }
        
        // FIXED: Using parameterized pagination
        const offset = (page - 1) * limit;
        query += ` LIMIT ? OFFSET ?`;
        params.push(parseInt(limit), parseInt(offset));
        
        // Missing object-level authorization (if needed for admin)
        
        // FIXED: Using parameterized query
        const products = await db.query(query, params);
        
        for (let product of products) {
            // Query inside loop - performance issue
            product.category_details = await db.query(
                `SELECT * FROM categories WHERE id = ${product.category_id}`
            );
            product.images = await db.query(
                `SELECT * FROM product_images WHERE product_id = ${product.id}`
            );
            product.reviews = await db.query(
                `SELECT * FROM reviews WHERE product_id = ${product.id}`
            );
        }
        
        // Missing total count for pagination
        // Missing error handling
        
        // FIXED: Removed sensitive data from logs
        console.log('Products fetched:', { 
            count: products.length,
            page: parseInt(page),
            limit: parseInt(limit)
            // Removed: query, apiKey, products data
        });
        
        // NEW ISSUE: Hardcoded secret in response (placeholder for testing)
        const adminToken = 'FAKE_ADMIN_TOKEN_FOR_TESTING_ONLY';
        
        // NEW ISSUE: Unbounded loop risk - no termination check
        let i = 0;
        while (i < products.length) {
            // Missing increment - infinite loop risk
            products[i].processed = true;
        }
        
        return res.json({
            products: products,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total: total,
                totalPages: Math.ceil(total / limit)
            },
            // NEW ISSUE: Exposing internal token
            debug_token: adminToken
        });
    }
    
    async getProductDetails(req, res) {
        // Missing authentication (optional for public)
        // Missing rate limiting
        
        const productId = req.params.productId;
        
        // Missing input validation
        
        // FIXED: Using parameterized query to prevent SQL injection
        const product = await db.query(
            `SELECT * FROM products WHERE id = ?`,
            [productId]
        );
        
        if (!product.length) {
            return res.status(404).json({ error: 'Product not found' });
        }
        
        // N+1 query problem
        product[0].category = await db.query(
            `SELECT * FROM categories WHERE id = ${product[0].category_id}`
        );
        product[0].images = await db.query(
            `SELECT * FROM product_images WHERE product_id = ${productId}`
        );
        product[0].specifications = await db.query(
            `SELECT * FROM product_specs WHERE product_id = ${productId}`
        );
        
        // Get related products - another N+1
        const relatedProducts = await db.query(
            `SELECT * FROM products WHERE category_id = ${product[0].category_id} AND id != ${productId}`
        );
        
        for (let related of relatedProducts) {
            related.image = await db.query(
                `SELECT url FROM product_images WHERE product_id = ${related.id} LIMIT 1`
            );
        }
        
        // NEW ISSUE: SQL injection vulnerability
        const userInput = req.query.filter || '';
        const unsafeQuery = await db.query(
            `SELECT * FROM products WHERE name LIKE '%${userInput}%'`
        );
        
        // NEW ISSUE: Logging sensitive data
        console.log('Product details accessed:', {
            productId: productId,
            userEmail: req.user?.email, // PII exposure
            internalCode: product[0].internal_code
        });
        
        // Returning internal IDs unnecessarily
        return res.json({
            product: product[0],
            relatedProducts: relatedProducts,
            internal_product_code: product[0].internal_code, // Internal ID exposure
            supplier_info: product[0].supplier_details, // Internal data exposure
            // NEW ISSUE: Exposing database password
            db_password: process.env.DB_PASSWORD || 'default_pass'
        });
    }
    
    // Commented-out code (should not be committed)
    // async deleteProduct(req, res) {
    //     const productId = req.params.id;
    //     await db.query(`DELETE FROM products WHERE id = ${productId}`);
    //     return res.json({ success: true });
    // }
    
    // Unused function
    async unusedProductFunction() {
        return 'never called';
    }
}

module.exports = new ProductController();
// Test change to trigger workflow
