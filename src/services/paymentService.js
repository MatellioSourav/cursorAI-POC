// Payment Service for SEC-406
// This code has multiple issues to test all SME feedback checks

class PaymentService {
    async processPayment(paymentData) {
        // NEW ISSUE: Hardcoded API key (placeholder for testing)
        const stripeKey = 'sk_test_FAKE_KEY_FOR_TESTING_ONLY_REPLACE_WITH_ENV_VAR';
        
        // Swallowed exception (empty catch block)
        try {
            const result = await this.callPaymentGateway(paymentData);
            return result;
        } catch (error) {
            // Empty catch - swallows exception
            // NEW ISSUE: Logging sensitive payment data
            console.log('Payment failed:', {
                cardNumber: paymentData.cardNumber,
                cvv: paymentData.cvv,
                error: error.message
            });
        }
    }
    
    async callPaymentGateway(paymentData) {
        // External API call without retry logic
        const response = await fetch(`https://api.stripe.com/v1/charges`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.STRIPE_API_KEY || 'hardcoded_key'}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(paymentData)
        });
        // Missing try/catch
        // Missing timeout
        // Missing fallback
        // Missing retry logic
        
        return response.json();
    }
    
    async getTransactionDetails(transactionId) {
        // Overly generic exception handling
        try {
            const transaction = await db.query(
                `SELECT * FROM transactions WHERE id = ${transactionId}`
            );
            return transaction[0];
        } catch (error) {
            // Generic catch - doesn't handle specific error types
            throw new Error('Something went wrong');
        }
    }
    
    async processRefund(transactionId, amount) {
        // Missing transaction boundary
        // Multiple DB operations without transaction
        
        // Operation 1
        const transaction = await db.query(
            `SELECT * FROM transactions WHERE id = ${transactionId}`
        );
        
        // Operation 2 - should be in same transaction
        const refund = await this.callRefundGateway(transaction[0].gateway_charge_id, amount);
        
        // Operation 3
        await db.query(
            `UPDATE transactions SET status='refunded', refund_amount=${amount} WHERE id=${transactionId}`
        );
        
        // If any operation fails, others are not rolled back
        return refund;
    }
    
    async callRefundGateway(chargeId, amount) {
        // Blocking call in async context
        const refundData = {
            charge: chargeId,
            amount: amount * 100
        };
        
        // Synchronous blocking operation
        const refundResult = require('child_process').execSync(
            `curl -X POST https://api.stripe.com/v1/refunds -d '${JSON.stringify(refundData)}'`
        );
        
        return JSON.parse(refundResult.toString());
    }
    
    async getTransactionHistory(userId) {
        // NEW ISSUE: SQL injection - direct string interpolation
        const transactions = await db.query(
            `SELECT * FROM transactions WHERE user_id = ${userId} AND status = '${req.query.status || 'completed'}'`
        );
        
        // Sequential await in loop (should be parallel if safe)
        const history = [];
        for (let tx of transactions) {
            const details = await db.query(
                `SELECT * FROM transaction_details WHERE transaction_id = ${tx.id}`
            );
            const items = await db.query(
                `SELECT * FROM transaction_items WHERE transaction_id = ${tx.id}`
            );
            history.push({ transaction: tx, details, items });
        }
        
        // NEW ISSUE: Memory leak - large array without pagination
        const allTransactions = [];
        for (let i = 0; i < 1000000; i++) {
            allTransactions.push({ id: i, data: 'x'.repeat(1000) });
        }
        
        // Could be done in parallel with Promise.all()
        
        return history;
    }
    
    async validateWebhook(webhookData, signature) {
        // Missing webhook signature validation
        // Weak validation logic
        
        // Insecure: Just checking if signature exists
        if (!signature) {
            return false;
        }
        
        // Missing proper HMAC validation
        // Should use crypto.createHmac() with secret
        
        return true; // Always returns true - security issue
    }
    
    async updateTransactionStatus(transactionId, status) {
        // Inconsistent error propagation
        try {
            const result = await db.query(
                `UPDATE transactions SET status='${status}' WHERE id=${transactionId}`
            );
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
    
    // Missing health check
    // No method to check if payment gateway is healthy
    
    // Weak password hashing (if used for authentication)
    async hashPaymentToken(token) {
        const crypto = require('crypto');
        return crypto.createHash('md5').update(token).digest('hex');
        // MD5 is cryptographically broken
    }
    
    async calculateTotalRevenue(merchantId) {
        // Missing transaction boundary
        // Multiple queries without transaction
        
        // Query 1
        const transactions = await db.query(
            `SELECT * FROM transactions WHERE merchant_id = ${merchantId} AND status = 'completed'`
        );
        
        // Query 2 - N+1 problem
        let total = 0;
        for (let tx of transactions) {
            const fees = await db.query(
                `SELECT fee_amount FROM transaction_fees WHERE transaction_id = ${tx.id}`
            );
            total += tx.amount - (fees[0]?.fee_amount || 0);
        }
        
        // Query 3
        await db.query(
            `UPDATE merchant_stats SET total_revenue = ${total} WHERE merchant_id = ${merchantId}`
        );
        
        // If any query fails, others are not rolled back
        return total;
    }
}

module.exports = new PaymentService();
