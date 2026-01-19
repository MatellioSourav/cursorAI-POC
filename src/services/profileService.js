// Profile Service for SEC-402
// This code has multiple issues to test all SME feedback checks

class ProfileService {
    async getUserProfile(userId) {
        // Swallowed exception (empty catch block)
        try {
            const profile = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
            return profile;
        } catch (error) {
            // Empty catch - swallows exception
        }
    }
    
    async updateUserProfile(userId, profileData) {
        // Overly generic exception handling
        try {
            const result = await db.query(
                `UPDATE users SET name='${profileData.name}', email='${profileData.email}' WHERE id=${userId}`
            );
            return result;
        } catch (error) {
            // Generic catch - doesn't handle specific error types
            throw new Error('Something went wrong');
        }
    }
    
    async validateEmail(email) {
        // External API call without retry logic
        const response = await fetch(`http://external-api.com/validate-email?email=${email}`);
        return response.json();
        // Missing try/catch
        // Missing timeout
        // Missing fallback
    }
    
    async hashPassword(password) {
        // Weak hashing (should use bcrypt/argon2)
        // Using simple hash - INSECURE
        const crypto = require('crypto');
        return crypto.createHash('md5').update(password).digest('hex');
        // MD5 is cryptographically broken
    }
    
    async processProfileUpdate(userId, updates) {
        // Missing transaction boundary
        // Multiple DB operations without transaction
        
        // Operation 1
        await db.query(`UPDATE users SET name='${updates.name}' WHERE id=${userId}`);
        
        // Operation 2
        await db.query(`UPDATE user_preferences SET theme='${updates.theme}' WHERE user_id=${userId}`);
        
        // Operation 3
        await db.query(`INSERT INTO user_activity (user_id, action) VALUES (${userId}, 'profile_updated')`);
        
        // If any operation fails, others are not rolled back
    }
    
    async getProfileHistory(userId) {
        // Inefficient data structure usage
        const history = [];
        
        // Large object creation in loop
        for (let i = 0; i < 10000; i++) {
            const item = {
                id: i,
                timestamp: new Date(),
                action: 'profile_update',
                data: new Array(1000).fill(0), // Large array in each iteration
                metadata: { /* large object */ }
            };
            history.push(item);
        }
        
        return history;
    }
    
    async syncProfileToExternalService(userId) {
        // Blocking call in async context
        const profile = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
        
        // Synchronous blocking operation
        const syncResult = require('child_process').execSync(
            `curl -X POST http://external-service.com/sync -d '${JSON.stringify(profile)}'`
        );
        
        return syncResult.toString();
    }
    
    async getProfileStats(userId) {
        // Sequential await in loop (should be parallel if safe)
        const stats = {};
        
        const orders = await db.query(`SELECT COUNT(*) FROM orders WHERE user_id = ${userId}`);
        stats.orderCount = orders[0].count;
        
        const payments = await db.query(`SELECT COUNT(*) FROM payments WHERE user_id = ${userId}`);
        stats.paymentCount = payments[0].count;
        
        const reviews = await db.query(`SELECT COUNT(*) FROM reviews WHERE user_id = ${userId}`);
        stats.reviewCount = reviews[0].count;
        
        // Could be done in parallel with Promise.all()
        
        return stats;
    }
    
    // Missing health check
    // No method to check if service is healthy
    
    // Inconsistent error propagation
    async updateProfilePicture(userId, pictureUrl) {
        try {
            const result = await db.query(`UPDATE users SET picture_url='${pictureUrl}' WHERE id=${userId}`);
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
}

module.exports = new ProfileService();

