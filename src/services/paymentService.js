// Payment Service for SEC-400
// Implements secure payment processing with proper validation and error handling

const logger = require('../utils/logger');

/**
 * Payment Service - Handles payment processing, refunds, and payment history
 * @class PaymentService
 */
class PaymentService {
    /**
     * Process a payment for a user
     * @param {string} userId - The user ID making the payment
     * @param {number} amount - Payment amount (must be > 0)
     * @param {string} paymentMethod - Payment method (credit_card, debit_card, wallet)
     * @returns {Promise<Object>} Payment result with success status and transaction ID
     * @throws {Error} If validation fails or payment processing fails
     */
    async processPayment(userId, amount, paymentMethod) {
        // Input validation
        if (!userId || typeof userId !== 'string') {
            throw new Error('Invalid user ID');
        }
        
        if (!amount || typeof amount !== 'number' || amount <= 0) {
            throw new Error('Payment amount must be greater than 0');
        }
        
        const validPaymentMethods = ['credit_card', 'debit_card', 'wallet'];
        if (!paymentMethod || !validPaymentMethods.includes(paymentMethod)) {
            throw new Error('Invalid payment method');
        }
        
        // Use parameterized query to prevent SQL injection
        const user = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
        
        if (!user || user.length === 0) {
            logger.error(`User not found: ${userId}`);
            throw new Error('User not found');
        }
        
        // Start transaction
        await db.beginTransaction();
        
        try {
            // Process payment through gateway (mock implementation)
            const gatewayResponse = await this._processPaymentGateway(amount, paymentMethod);
            
            if (!gatewayResponse.success) {
                throw new Error('Payment gateway processing failed');
            }
            
            // Update account balance using parameterized query
            await db.query(
                'UPDATE accounts SET balance = balance - ? WHERE user_id = ?',
                [amount, userId]
            );
            
            // Record payment transaction
            const paymentRecord = await db.query(
                'INSERT INTO payments (user_id, amount, payment_method, status, transaction_id) VALUES (?, ?, ?, ?, ?)',
                [userId, amount, paymentMethod, 'completed', gatewayResponse.transactionId]
            );
            
            // Commit transaction
            await db.commit();
            
            // Log successful payment
            logger.info(`Payment processed successfully: User ${userId}, Amount ${amount}, Transaction ${gatewayResponse.transactionId}`);
            
            // Send payment confirmation (mock)
            await this._sendPaymentConfirmation(userId, amount, gatewayResponse.transactionId);
            
            return {
                success: true,
                transactionId: gatewayResponse.transactionId,
                amount: amount,
                message: 'Payment processed successfully'
            };
        } catch (error) {
            // Rollback transaction on failure
            await db.rollback();
            logger.error(`Payment processing failed: ${error.message}`, { userId, amount, paymentMethod });
            throw error;
        }
    }
    
    /**
     * Process a refund for a completed payment
     * @param {string} paymentId - The payment ID to refund
     * @returns {Promise<Object>} Refund result with success status
     * @throws {Error} If refund validation fails or processing fails
     */
    async refundPayment(paymentId) {
        // Input validation
        if (!paymentId || typeof paymentId !== 'string') {
            throw new Error('Invalid payment ID');
        }
        
        // Use parameterized query to prevent SQL injection
        const payment = await db.query('SELECT * FROM payments WHERE id = ?', [paymentId]);
        
        if (!payment || payment.length === 0) {
            logger.error(`Payment not found: ${paymentId}`);
            throw new Error('Payment not found');
        }
        
        const paymentData = payment[0];
        
        // Validate refund eligibility
        if (paymentData.status !== 'completed') {
            throw new Error('Only completed payments can be refunded');
        }
        
        // Start transaction
        await db.beginTransaction();
        
        try {
            // Process refund through gateway
            const refundResponse = await this._processRefundGateway(paymentData.transaction_id, paymentData.amount);
            
            if (!refundResponse.success) {
                throw new Error('Refund processing failed');
            }
            
            // Update account balance
            await db.query(
                'UPDATE accounts SET balance = balance + ? WHERE user_id = ?',
                [paymentData.amount, paymentData.user_id]
            );
            
            // Update payment status
            await db.query(
                'UPDATE payments SET status = ? WHERE id = ?',
                ['refunded', paymentId]
            );
            
            // Commit transaction
            await db.commit();
            
            // Log successful refund
            logger.info(`Refund processed successfully: Payment ${paymentId}, Amount ${paymentData.amount}`);
            
            // Send refund confirmation
            await this._sendRefundConfirmation(paymentData.user_id, paymentData.amount, refundResponse.refundId);
            
            return {
                success: true,
                refundId: refundResponse.refundId,
                amount: paymentData.amount,
                message: 'Refund processed successfully'
            };
        } catch (error) {
            // Rollback transaction on failure
            await db.rollback();
            logger.error(`Refund processing failed: ${error.message}`, { paymentId });
            throw error;
        }
    }
    
    /**
     * Get payment history for a user with pagination
     * @param {string} userId - The user ID
     * @param {number} page - Page number (default: 1)
     * @param {number} limit - Records per page (default: 50, max: 50)
     * @param {string} startDate - Optional start date filter (YYYY-MM-DD)
     * @param {string} endDate - Optional end date filter (YYYY-MM-DD)
     * @returns {Promise<Object>} Paginated payment history
     */
    async getPaymentHistory(userId, page = 1, limit = 50, startDate = null, endDate = null) {
        // Input validation
        if (!userId || typeof userId !== 'string') {
            throw new Error('Invalid user ID');
        }
        
        // Validate pagination parameters
        const pageNum = Math.max(1, parseInt(page) || 1);
        const pageLimit = Math.min(50, Math.max(1, parseInt(limit) || 50));
        const offset = (pageNum - 1) * pageLimit;
        
        try {
            // Build query with date filters
            let query = 'SELECT * FROM payments WHERE user_id = ?';
            const params = [userId];
            
            if (startDate) {
                query += ' AND created_at >= ?';
                params.push(startDate);
            }
            
            if (endDate) {
                query += ' AND created_at <= ?';
                params.push(endDate);
            }
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
            params.push(pageLimit, offset);
            
            // Use parameterized query to prevent SQL injection
            const payments = await db.query(query, params);
            
            // Get total count for pagination
            let countQuery = 'SELECT COUNT(*) as total FROM payments WHERE user_id = ?';
            const countParams = [userId];
            
            if (startDate) {
                countQuery += ' AND created_at >= ?';
                countParams.push(startDate);
            }
            
            if (endDate) {
                countQuery += ' AND created_at <= ?';
                countParams.push(endDate);
            }
            
            const countResult = await db.query(countQuery, countParams);
            const total = countResult[0].total;
            
            // Log payment history access
            logger.info(`Payment history accessed: User ${userId}, Page ${pageNum}, Limit ${pageLimit}`);
            
            return {
                payments: payments,
                pagination: {
                    page: pageNum,
                    limit: pageLimit,
                    total: total,
                    totalPages: Math.ceil(total / pageLimit)
                }
            };
        } catch (error) {
            logger.error(`Error fetching payment history: ${error.message}`, { userId });
            throw error;
        }
    }
    
    /**
     * Process payment through payment gateway (mock implementation)
     * @private
     * @param {number} amount - Payment amount
     * @param {string} paymentMethod - Payment method
     * @returns {Promise<Object>} Gateway response
     */
    async _processPaymentGateway(amount, paymentMethod) {
        // Mock gateway integration
        // In real implementation, this would call actual payment gateway API
        return {
            success: true,
            transactionId: `TXN-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        };
    }
    
    /**
     * Process refund through payment gateway (mock implementation)
     * @private
     * @param {string} transactionId - Original transaction ID
     * @param {number} amount - Refund amount
     * @returns {Promise<Object>} Gateway response
     */
    async _processRefundGateway(transactionId, amount) {
        // Mock gateway integration
        return {
            success: true,
            refundId: `REF-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        };
    }
    
    /**
     * Send payment confirmation (mock implementation)
     * @private
     * @param {string} userId - User ID
     * @param {number} amount - Payment amount
     * @param {string} transactionId - Transaction ID
     */
    async _sendPaymentConfirmation(userId, amount, transactionId) {
        // Mock email/SMS notification
        logger.info(`Payment confirmation sent to user ${userId}`);
    }
    
    /**
     * Send refund confirmation (mock implementation)
     * @private
     * @param {string} userId - User ID
     * @param {number} amount - Refund amount
     * @param {string} refundId - Refund ID
     */
    async _sendRefundConfirmation(userId, amount, refundId) {
        // Mock email/SMS notification
        logger.info(`Refund confirmation sent to user ${userId}`);
    }
}

module.exports = new PaymentService();
