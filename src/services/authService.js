// Authentication Service for SEC-398
// Handles password hashing, token generation, and account locking
// Has some intentional issues for testing AI review

const bcrypt = require('bcrypt');

class AuthService {
    constructor() {
        // Missing rate limiting storage (AC4)
        this.failedAttempts = {}; // Should use Redis or database
    }
    
    async hashPassword(password) {
        // Missing password length validation (AC5)
        // Should check: if (password.length < 8) throw error
        
        // Good: Using bcrypt (requirement met)
        const saltRounds = 10;
        return await bcrypt.hash(password, saltRounds);
    }
    
    async verifyPassword(plainPassword, hashedPassword) {
        return await bcrypt.compare(plainPassword, hashedPassword);
    }
    
    async generateToken(user) {
        // Missing JWT library import
        // Missing "Remember Me" token expiry logic (AC3)
        // Should use: jwt.sign(payload, secret, { expiresIn: rememberMe ? '30d' : '30m' })
        
        // Temporary token (not secure)
        return Buffer.from(JSON.stringify(user)).toString('base64');
    }
    
    async checkRateLimit(email) {
        // Missing rate limiting implementation (AC4)
        // Should: Track attempts, lock after 5 failures for 30 minutes
        // Current: No rate limiting at all
        
        return { allowed: true, remainingAttempts: 5 };
    }
    
    async recordFailedAttempt(email) {
        // Missing account locking after 5 attempts (AC4)
        if (!this.failedAttempts[email]) {
            this.failedAttempts[email] = 0;
        }
        this.failedAttempts[email]++;
        
        // Should lock account after 5 attempts for 30 minutes
        // Missing lock mechanism
    }
    
    async resetFailedAttempts(email) {
        // Missing implementation
        delete this.failedAttempts[email];
    }
    
    // Missing logout token invalidation (AC6)
    // Missing session timeout handling (AC3)
}

module.exports = new AuthService();

