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
        
        // SQL injection vulnerability
        let query = `SELECT * FROM products WHERE 1=1`;
        
        if (category) {
            query += ` AND category = '${category}'`; // SQL injection
        }
        
        if (search) {
            query += ` AND name LIKE '%${search}%'`; // SQL injection + XSS risk
        }
        
        // Missing pagination validation
        const offset = (page - 1) * limit;
        query += ` LIMIT ${limit} OFFSET ${offset}`; // SQL injection
        
        // Missing object-level authorization (if needed for admin)
        
        // N+1 query problem
        const products = await db.query(query);
        
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
        
        // Logging sensitive data
        console.log('Products fetched:', { 
            query, 
            apiKey: PRODUCT_API_KEY, 
            products 
        });
        
        return res.json({
            products: products,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit)
                // Missing: total, totalPages
            }
        });
    }
    
    async getProductDetails(req, res) {
        // Missing authentication (optional for public)
        // Missing rate limiting
        
        const productId = req.params.productId;
        
        // Missing input validation
        
        // SQL injection vulnerability
        const product = await db.query(
            `SELECT * FROM products WHERE id = ${productId}`
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
        
        // Returning internal IDs unnecessarily
        return res.json({
            product: product[0],
            relatedProducts: relatedProducts,
            internal_product_code: product[0].internal_code, // Internal ID exposure
            supplier_info: product[0].supplier_details // Internal data exposure
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
