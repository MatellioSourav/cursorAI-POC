// Payment Controller for SEC-406
// This code has multiple issues to test all SME feedback checks

// Hardcoded payment gateway API key - should be in config
const STRIPE_API_KEY = 'sk_test_FAKE_KEY_FOR_TESTING_ONLY_REPLACE_WITH_ENV_VAR';
const PAYPAL_CLIENT_ID = 'paypal_client_FAKE_ID_123456789';
const PAYPAL_SECRET = 'paypal_secret_FAKE_SECRET_abcdefghijklmnop';

// Hardcoded database password
const DB_PASSWORD = 'FAKE_DB_PASSWORD_FOR_TESTING_ONLY';

// Payment gateway URLs - should be in config
const STRIPE_API_URL = 'https://api.stripe.com/v1';
const PAYPAL_API_URL = 'https://api.paypal.com/v1';

// Unused import
const unusedHelper = require('../utils/unusedHelper');

class PaymentController {
    // Missing JSDoc documentation
    
    async processPayment(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const { amount, currency, paymentMethod, cardNumber, cvv, expiryDate } = req.body;
        
        // Missing input validation
        // Missing sanitization
        
        // Logging sensitive payment data - SECURITY ISSUE
        console.log('Processing payment:', { 
            amount, 
            cardNumber, // PII exposure
            cvv, // Sensitive data
            expiryDate,
            apiKey: STRIPE_API_KEY // Secret exposure
        });
        
        // SQL injection vulnerability
        const userId = req.user?.id || req.body.userId;
        const transaction = await db.query(
            `INSERT INTO transactions (user_id, amount, currency, payment_method, card_number, status) 
             VALUES (${userId}, ${amount}, '${currency}', '${paymentMethod}', '${cardNumber}', 'pending')`
        );
        
        // Missing object-level authorization
        // User can process payment for any user_id
        
        // Missing transaction boundary
        // No rollback on error
        
        // External API call without proper error handling
        const paymentResult = await fetch(`${STRIPE_API_URL}/charges`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${STRIPE_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: amount * 100, // Convert to cents
                currency: currency,
                source: cardNumber
            })
        });
        // Missing try/catch, timeout, retry logic, fallback
        
        // N+1 query problem
        if (paymentResult.ok) {
            const paymentData = await paymentResult.json();
            
            // Query inside loop - performance issue
            for (let item of paymentData.items || []) {
                item.details = await db.query(
                    `SELECT * FROM payment_details WHERE transaction_id = ${transaction.insertId} AND item_id = ${item.id}`
                );
            }
            
            // Update transaction status
            await db.query(
                `UPDATE transactions SET status='completed', gateway_response='${JSON.stringify(paymentData)}' WHERE id=${transaction.insertId}`
            );
        }
        
        // Error handling leaks internals
        try {
            return res.json({
                success: true,
                transactionId: transaction.insertId,
                status: 'completed',
                gatewayResponse: paymentResult.json() // Internal data exposure
            });
        } catch (error) {
            // Exposes internal error details
            return res.status(500).json({
                error: error.message,
                stack: error.stack, // Internal leakage
                code: error.code,
                sql: error.sql, // SQL query exposure
                database: error.database, // Database name exposure
                apiKey: STRIPE_API_KEY // Secret exposure in error
            });
        }
    }
    
    async getPaymentDetails(req, res) {
        // Missing authentication
        // Missing authorization
        
        const transactionId = req.params.transactionId;
        
        // Missing input validation
        
        // SQL injection vulnerability
        const transaction = await db.query(
            `SELECT * FROM transactions WHERE id = ${transactionId}`
        );
        
        // Missing object-level authorization
        // User can view any transaction
        
        // N+1 query problem
        if (transaction.length > 0) {
            // Query inside loop
            transaction[0].items = await db.query(
                `SELECT * FROM transaction_items WHERE transaction_id = ${transactionId}`
            );
            
            for (let item of transaction[0].items) {
                item.product = await db.query(
                    `SELECT * FROM products WHERE id = ${item.product_id}`
                );
            }
        }
        
        // Returning sensitive data
        return res.json({
            transaction: transaction[0],
            cardNumber: transaction[0]?.card_number, // PII exposure
            cvv: transaction[0]?.cvv, // Sensitive data exposure
            apiKey: STRIPE_API_KEY, // Secret exposure
            internalGatewayId: transaction[0]?.gateway_internal_id // Internal ID exposure
        });
    }
    
    async processRefund(req, res) {
        // Missing authentication
        // Missing authorization
        
        const { transactionId, amount, reason } = req.body;
        
        // Missing input validation
        // Missing transaction boundary
        
        // SQL injection vulnerability
        const transaction = await db.query(
            `SELECT * FROM transactions WHERE id = ${transactionId} AND status = 'completed'`
        );
        
        if (!transaction.length) {
            return res.status(400).json({ error: 'Transaction not found or not refundable' });
        }
        
        // Missing object-level authorization
        // User can refund any transaction
        
        // External API call without retry logic
        const refundResult = await fetch(`${STRIPE_API_URL}/refunds`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${STRIPE_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                charge: transaction[0].gateway_charge_id,
                amount: amount ? amount * 100 : null
            })
        });
        // Missing try/catch, timeout, fallback
        
        // Update transaction without transaction boundary
        await db.query(
            `UPDATE transactions SET status='refunded', refund_amount=${amount}, refund_reason='${reason}' WHERE id=${transactionId}`
        );
        
        // Missing rollback if refund fails
        
        return res.json({ success: true, refundId: refundResult.json().id });
    }
    
    async handleWebhook(req, res) {
        // Missing webhook signature validation
        // Missing authentication
        
        const webhookData = req.body;
        
        // Missing input validation
        
        // Logging sensitive webhook data
        console.log('Webhook received:', JSON.stringify(webhookData));
        
        // SQL injection vulnerability
        const transactionId = webhookData.data?.object?.id;
        await db.query(
            `UPDATE transactions SET status='${webhookData.type}', webhook_data='${JSON.stringify(webhookData)}' WHERE gateway_charge_id='${transactionId}'`
        );
        
        // Missing error handling
        // No validation of webhook payload
        
        return res.json({ received: true });
    }
    
    async getTransactionHistory(req, res) {
        // Missing authentication
        // Missing authorization
        
        const userId = req.params.userId || req.query.userId;
        
        // Missing input validation
        
        // SQL injection vulnerability
        const transactions = await db.query(
            `SELECT * FROM transactions WHERE user_id = ${userId} ORDER BY created_at DESC`
        );
        
        // Missing object-level authorization
        // User can view any user's transactions
        
        // Missing pagination
        // Could return thousands of records
        
        // Large object creation in loop
        const enrichedTransactions = [];
        for (let tx of transactions) {
            const enriched = {
                ...tx,
                metadata: new Array(1000).fill(0), // Large array
                history: new Array(500).fill({}), // Large object array
                analytics: {
                    // Large nested object
                    dailyStats: new Array(365).fill({}),
                    monthlyStats: new Array(12).fill({})
                }
            };
            enrichedTransactions.push(enriched);
        }
        
        return res.json({ transactions: enrichedTransactions });
    }
    
    // Commented-out code (should not be committed)
    // async deleteTransaction(req, res) {
    //     const transactionId = req.params.id;
    //     await db.query(`DELETE FROM transactions WHERE id = ${transactionId}`);
    //     return res.json({ success: true });
    // }
    
    // Unused function
    async unusedPaymentFunction() {
        return 'never called';
    }
}

module.exports = new PaymentController();
