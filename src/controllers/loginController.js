// Dummy Login Code for Testing JIRA Integration SEC-396
// This code has intentional issues that the AI should catch when reviewing against JIRA ticket SEC-396

// Login Controller - Missing some requirements
class LoginController {
    async login(req, res) {
        const { email, password } = req.body;
        
        // Missing email format validation
        // Missing password length validation (AC5)
        
        // Direct database query - potential SQL injection risk (AC8)
        const user = await db.query(`SELECT * FROM users WHERE email = '${email}'`);
        
        if (!user) {
            // Violates AC2 - reveals that email doesn't exist
            return res.status(401).json({ error: 'Email not found' });
        }
        
        // Missing bcrypt password hashing
        if (user.password !== password) {
            return res.status(401).json({ error: 'Invalid password' });
        }
        
        // Missing JWT token generation
        // Missing "Remember Me" functionality (AC3)
        
        // HTTP instead of HTTPS - violates AC7
        return res.status(200).json({ message: 'Login successful' });
    }
    
    // Missing logout functionality (AC6)
    // Missing rate limiting (AC4)
    // Missing session timeout (AC3)
}

module.exports = new LoginController();

