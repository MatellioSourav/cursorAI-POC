// Payment Controller for SEC-400
// Implements secure payment endpoints with authentication, authorization, and proper error handling

const paymentService = require('../services/paymentService');
const logger = require('../utils/logger');
const rateLimiter = require('../middleware/rateLimiter');

/**
 * Payment Controller - Handles HTTP requests for payment operations
 * @class PaymentController
 */
class PaymentController {
    /**
     * Process a payment
     * @route POST /api/payments/process
     * @access Private (requires authentication)
     * @param {Object} req - Express request object
     * @param {Object} res - Express response object
     * @returns {Object} Payment result or error
     */
    async processPayment(req, res) {
        try {
            // Authentication check (AC4)
            if (!req.user || !req.user.id) {
                return res.status(401).json({ 
                    error: 'Authentication required',
                    code: 'UNAUTHORIZED'
                });
            }
            
            // Rate limiting check (AC8)
            const rateLimitCheck = await rateLimiter.checkLimit(req.user.id, 'payment', 10, 60);
            if (!rateLimitCheck.allowed) {
                return res.status(429).json({
                    error: 'Rate limit exceeded. Maximum 10 requests per minute.',
                    code: 'RATE_LIMIT_EXCEEDED',
                    retryAfter: rateLimitCheck.retryAfter
                });
            }
            
            const { amount, paymentMethod } = req.body;
            const userId = req.user.id; // Use authenticated user ID (AC5)
            
            // Input validation
            if (!amount || typeof amount !== 'number' || amount <= 0) {
                return res.status(400).json({
                    error: 'Payment amount must be greater than 0',
                    code: 'INVALID_AMOUNT'
                });
            }
            
            if (!paymentMethod) {
                return res.status(400).json({
                    error: 'Payment method is required',
                    code: 'INVALID_PAYMENT_METHOD'
                });
            }
            
            // Process payment
            const result = await paymentService.processPayment(userId, amount, paymentMethod);
            
            // Log successful payment (AC9)
            logger.info('Payment processed successfully', {
                userId,
                amount,
                paymentMethod,
                transactionId: result.transactionId
            });
            
            // Return success response (AC1)
            return res.status(200).json({
                success: true,
                data: {
                    transactionId: result.transactionId,
                    amount: result.amount,
                    message: result.message
                }
            });
        } catch (error) {
            // User-friendly error handling (AC10)
            logger.error('Payment processing error', {
                error: error.message,
                userId: req.user?.id,
                stack: error.stack
            });
            
            // Return user-friendly error message
            return res.status(500).json({
                error: 'Payment processing failed. Please try again later.',
                code: 'PAYMENT_PROCESSING_FAILED'
            });
        }
    }
    
    /**
     * Process a refund
     * @route POST /api/payments/:paymentId/refund
     * @access Private (requires authentication)
     * @param {Object} req - Express request object
     * @param {Object} res - Express response object
     * @returns {Object} Refund result or error
     */
    async refundPayment(req, res) {
        try {
            // Authentication check (AC4)
            if (!req.user || !req.user.id) {
                return res.status(401).json({
                    error: 'Authentication required',
                    code: 'UNAUTHORIZED'
                });
            }
            
            const { paymentId } = req.params;
            const userId = req.user.id;
            
            // Input validation
            if (!paymentId) {
                return res.status(400).json({
                    error: 'Payment ID is required',
                    code: 'INVALID_PAYMENT_ID'
                });
            }
            
            // Authorization check - verify payment belongs to user (AC5)
            const payment = await db.query('SELECT user_id FROM payments WHERE id = ?', [paymentId]);
            if (!payment || payment.length === 0) {
                return res.status(404).json({
                    error: 'Payment not found',
                    code: 'PAYMENT_NOT_FOUND'
                });
            }
            
            if (payment[0].user_id !== userId) {
                return res.status(403).json({
                    error: 'You can only refund your own payments',
                    code: 'FORBIDDEN'
                });
            }
            
            // Process refund
            const result = await paymentService.refundPayment(paymentId);
            
            // Log successful refund (AC9)
            logger.info('Refund processed successfully', {
                userId,
                paymentId,
                refundId: result.refundId,
                amount: result.amount
            });
            
            // Return success response (AC2)
            return res.status(200).json({
                success: true,
                data: {
                    refundId: result.refundId,
                    amount: result.amount,
                    message: result.message
                }
            });
        } catch (error) {
            // User-friendly error handling (AC10)
            logger.error('Refund processing error', {
                error: error.message,
                userId: req.user?.id,
                paymentId: req.params.paymentId,
                stack: error.stack
            });
            
            // Return user-friendly error message
            return res.status(500).json({
                error: 'Refund processing failed. Please try again later.',
                code: 'REFUND_PROCESSING_FAILED'
            });
        }
    }
    
    /**
     * Get payment history for authenticated user
     * @route GET /api/payments/history
     * @access Private (requires authentication)
     * @param {Object} req - Express request object
     * @param {Object} res - Express response object
     * @returns {Object} Paginated payment history
     */
    async getPaymentHistory(req, res) {
        try {
            // Authentication check (AC4)
            if (!req.user || !req.user.id) {
                return res.status(401).json({
                    error: 'Authentication required',
                    code: 'UNAUTHORIZED'
                });
            }
            
            // Rate limiting check (AC8)
            const rateLimitCheck = await rateLimiter.checkLimit(req.user.id, 'payment_history', 10, 60);
            if (!rateLimitCheck.allowed) {
                return res.status(429).json({
                    error: 'Rate limit exceeded. Maximum 10 requests per minute.',
                    code: 'RATE_LIMIT_EXCEEDED',
                    retryAfter: rateLimitCheck.retryAfter
                });
            }
            
            const userId = req.user.id; // Use authenticated user ID (AC5)
            const { page = 1, limit = 50, startDate, endDate } = req.query;
            
            // Validate pagination
            const pageNum = parseInt(page) || 1;
            const pageLimit = Math.min(50, parseInt(limit) || 50); // Max 50 per page (AC3)
            
            // Get payment history with pagination (AC3)
            const result = await paymentService.getPaymentHistory(
                userId,
                pageNum,
                pageLimit,
                startDate,
                endDate
            );
            
            // Log payment history access (AC9)
            logger.info('Payment history accessed', {
                userId,
                page: pageNum,
                limit: pageLimit
            });
            
            // Return paginated response (AC3)
            return res.status(200).json({
                success: true,
                data: {
                    payments: result.payments,
                    pagination: result.pagination
                }
            });
        } catch (error) {
            // User-friendly error handling (AC10)
            logger.error('Error fetching payment history', {
                error: error.message,
                userId: req.user?.id,
                stack: error.stack
            });
            
            return res.status(500).json({
                error: 'Failed to fetch payment history. Please try again later.',
                code: 'PAYMENT_HISTORY_FETCH_FAILED'
            });
        }
    }
}

module.exports = new PaymentController();
