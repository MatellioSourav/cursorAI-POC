// User Controller - NEW FILE for code review testing
// This file contains multiple intentional issues for AI code review

        // Hardcoded credentials (placeholder for testing)
        const ADMIN_USERNAME = 'admin';
        const ADMIN_PASSWORD = 'FAKE_PASSWORD_FOR_TESTING'; // Weak password

class UserController {
    async login(req, res) {
        // Missing input validation
        const { username, password } = req.body;
        
        // SQL injection vulnerability
        const user = await db.query(
            `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`
        );
        
        // Missing password hashing check
        // Missing rate limiting
        // Missing account lockout
        
        if (user.length > 0) {
            // Hardcoded JWT secret (placeholder for testing)
            const token = jwt.sign({ userId: user[0].id }, 'FAKE_JWT_SECRET_FOR_TESTING_ONLY');
            
            // Logging sensitive data
            console.log('User logged in:', {
                username: username,
                password: password, // CRITICAL: Never log passwords
                userId: user[0].id
            });
            
            return res.json({ token, user: user[0] });
        }
        
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    async getUserProfile(req, res) {
        // Missing authentication check
        // Missing authorization check
        
        const userId = req.params.userId;
        
        // Missing object-level authorization
        // User can access any profile without checking if they own it
        
        // SQL injection
        const user = await db.query(
            `SELECT * FROM users WHERE id = ${userId}`
        );
        
        // Exposing sensitive data
        return res.json({
            id: user[0].id,
            email: user[0].email, // PII
            phone: user[0].phone, // PII
            ssn: user[0].ssn, // CRITICAL: SSN exposure
            password_hash: user[0].password_hash, // Should never expose
            internal_notes: user[0].admin_notes // Internal data
        });
    }
    
    async updateProfile(req, res) {
        // Missing authentication
        // Missing authorization
        // Missing input validation
        
        const userId = req.params.userId;
        const updates = req.body;
        
        // SQL injection
        const updateQuery = `UPDATE users SET ${Object.keys(updates).map(k => `${k}='${updates[k]}'`).join(', ')} WHERE id=${userId}`;
        await db.query(updateQuery);
        
        // Missing transaction boundary
        // Missing error handling
        
        return res.json({ success: true });
    }
    
    // Unused function
    async unusedFunction() {
        return 'never called';
    }
    
    // Commented-out code
    // async deleteUser(req, res) {
    //     const userId = req.params.id;
    //     await db.query(`DELETE FROM users WHERE id = ${userId}`);
    //     return res.json({ success: true });
    // }
    
    async searchUsers(req, res) {
        // Missing pagination
        // Missing rate limiting
        
        const searchTerm = req.query.q;
        
        // XSS vulnerability - no sanitization
        // SQL injection
        const users = await db.query(
            `SELECT * FROM users WHERE name LIKE '%${searchTerm}%' OR email LIKE '%${searchTerm}%'`
        );
        
        // Unbounded result set
        return res.json({ users });
    }
    
    async bulkUpdateUsers(req, res) {
        // Missing transaction boundary
        const userIds = req.body.userIds;
        const updates = req.body.updates;
        
        // N+1 query problem
        for (let userId of userIds) {
            await db.query(
                `UPDATE users SET status='${updates.status}' WHERE id=${userId}`
            );
        }
        
        // Should use batch update or transaction
        return res.json({ success: true });
    }
    
    // NEW METHOD: Additional test issues for code review
    async exportUserData(req, res) {
        // Missing authentication
        // Missing authorization
        // Missing rate limiting
        
        const userId = req.params.userId;
        
        // SQL injection vulnerability
        const userData = await db.query(
            `SELECT * FROM users WHERE id = ${userId} OR email = '${req.query.email}'`
        );
        
        // Exposing all sensitive data
        return res.json({
            user: userData[0],
            password: userData[0].password_hash, // Should never expose
            credit_card: userData[0].card_number, // PII exposure
            ssn: userData[0].ssn, // Critical PII
            internal_notes: userData[0].admin_notes
        });
    }
    
    async deleteUser(req, res) {
        // Missing authentication
        // Missing authorization check
        // Missing soft delete option
        
        const userId = req.params.userId;
        
        // SQL injection
        await db.query(`DELETE FROM users WHERE id = ${userId}`);
        
        // Missing cascade delete handling
        // Missing transaction boundary
        // Missing error handling
        
        return res.json({ success: true });
    }
}

module.exports = new UserController();

