// Payment Service for SEC-400
// This code has intentional issues for testing AI review

class PaymentService {
    // Missing JSDoc documentation
    async processPayment(userId, amount, paymentMethod) {
        // Missing input validation
        // Missing authentication check
        // Missing authorization check
        
        // Direct SQL query - SQL injection risk
        const user = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
        
        if (!user) {
            // Generic error - should be more specific
            throw new Error('Error');
        }
        
        // Missing amount validation (should be > 0)
        // Missing payment method validation
        
        // Missing transaction handling
        // Missing error handling
        // Missing logging
        
        // Direct database update without transaction
        await db.query(`UPDATE accounts SET balance = balance - ${amount} WHERE user_id = ${userId}`);
        
        // Missing payment gateway integration
        // Missing payment confirmation
        // Missing rollback on failure
        
        return { success: true };
    }
    
    // Missing JSDoc documentation
    async refundPayment(paymentId) {
        // Missing authentication
        // Missing authorization
        // Missing paymentId validation
        
        // SQL injection risk
        const payment = await db.query(`SELECT * FROM payments WHERE id = ${paymentId}`);
        
        if (!payment) {
            return { error: 'Not found' };
        }
        
        // Missing refund logic
        // Missing transaction handling
        // Missing error handling
        
        return { success: true };
    }
    
    // Missing JSDoc documentation
    async getPaymentHistory(userId) {
        // Missing authentication
        // Missing authorization - user can view any user's payment history
        
        // SQL injection risk
        const payments = await db.query(`SELECT * FROM payments WHERE user_id = ${userId} ORDER BY created_at DESC`);
        
        // Missing pagination
        // Missing data sanitization
        // Missing error handling
        
        return payments;
    }
}

module.exports = new PaymentService();

