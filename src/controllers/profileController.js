// Profile Controller for SEC-402
// This code has multiple issues to test all SME feedback checks
// TEST: Added test comment to verify code review bot works correctly

// Hardcoded API key - should be in config
const API_KEY = 'sk_live_profile_1234567890';
const UPLOAD_URL = 'http://localhost:3000/api/uploads'; // Hardcoded URL

// Unused import
const unusedValidator = require('../utils/unusedValidator');

class ProfileController {
    // Missing JSDoc documentation
    async getProfile(req, res) {
        // Missing authentication check
        // Missing authorization check - user can view any profile
        
        const userId = req.params.userId || req.user?.id;
        
        // Missing input validation
        
        // SQL injection risk
        const profile = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
        
        // Missing object-level authorization check
        // User can view any other user's profile
        
        // Logging sensitive data
        console.log('Profile fetched:', { userId, email: profile.email, phone: profile.phone });
        
        // Returning PII unnecessarily
        return res.json({
            id: profile.id,
            name: profile.name,
            email: profile.email, // PII exposure
            phone: profile.phone, // PII exposure
            password: profile.password_hash, // CRITICAL: Exposing password hash
            internal_id: profile.internal_system_id, // Internal ID exposure
            created_at: profile.created_at
        });
    }
    
    async updateProfile(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const userId = req.params.userId;
        const { name, email, phone, address } = req.body;
        
        // Missing input validation
        // Missing sanitization (XSS risk)
        
        // Hardcoded secret
        const dbPassword = 'profile_db_pass_123';
        
        // External API call without proper error handling
        const validationResult = await fetch(`${UPLOAD_URL}/validate`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${API_KEY}` },
            body: JSON.stringify({ email, phone })
        });
        // Missing try/catch, timeout, fallback
        
        // SQL injection risk
        const result = await db.query(
            `UPDATE users SET name='${name}', email='${email}', phone='${phone}', address='${address}' WHERE id=${userId}`
        );
        
        // Missing transaction boundary
        // Missing rollback on error
        
        // Error handling leaks internals
        try {
            return res.json({
                success: true,
                profile: result
            });
        } catch (error) {
            // Exposes internal error details
            return res.status(500).json({ 
                error: error.message,
                stack: error.stack, // Internal leakage
                code: error.code,
                sql: error.sql // SQL query exposure
            });
        }
    }
    
    async changePassword(req, res) {
        const userId = req.params.userId;
        const { currentPassword, newPassword } = req.body;
        
        // Missing authentication check
        // Missing authorization check
        // Missing input validation
        
        // Get user from database
        const user = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
        
        // Password validation in plain text comparison (INSECURE)
        if (user.password !== currentPassword) {
            return res.status(401).json({ error: 'Current password incorrect' });
        }
        
        // Storing password in plain text (CRITICAL SECURITY ISSUE)
        await db.query(`UPDATE users SET password='${newPassword}' WHERE id=${userId}`);
        
        // Logging password (CRITICAL)
        console.log('Password changed:', { userId, newPassword });
        
        return res.json({ success: true });
    }
    
    async uploadProfilePicture(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const file = req.files?.picture;
        
        // Missing file type validation
        // Missing file size validation
        
        // Hardcoded upload path
        const uploadPath = '/var/www/uploads/';
        
        // No file size limit check
        // No file type check
        
        // Storing in public directory (security risk)
        const filePath = `${uploadPath}${file.name}`;
        await file.mv(filePath);
        
        // Returning full system path (information disclosure)
        return res.json({
            success: true,
            imageUrl: filePath, // Exposes internal path
            fullPath: `/var/www/uploads/${file.name}` // Internal path exposure
        });
    }
    
    async getProfileActivity(req, res) {
        const userId = req.params.userId;
        
        // Missing authentication
        // Missing authorization
        
        // N+1 query problem
        const activities = await db.query(`SELECT * FROM user_activities WHERE user_id = ${userId}`);
        
        for (let activity of activities) {
            // Query inside loop - performance issue
            activity.user = await db.query(`SELECT * FROM users WHERE id = ${activity.user_id}`);
            activity.details = await db.query(`SELECT * FROM activity_details WHERE activity_id = ${activity.id}`);
        }
        
        // Unbounded loop risk
        let i = 0;
        while (activities[i]) {
            processActivity(activities[i]);
            i++;
            // Missing termination condition
        }
        
        // Missing pagination
        return res.json({ activities });
    }
    
    // Commented-out code (should not be committed)
    // async deleteProfile(req, res) {
    //     const userId = req.params.userId;
    //     await db.query(`DELETE FROM users WHERE id = ${userId}`);
    //     return res.json({ success: true });
    // }
    
    // Unused function
    async unusedProfileFunction() {
        return 'never called';
    }
}

module.exports = new ProfileController();

