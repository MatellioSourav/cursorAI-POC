// Profile Controller for SEC-399 (or your new JIRA key)
// This code has intentional issues for testing AI review

class ProfileController {
    // Missing JSDoc documentation
    async getProfile(req, res) {
        const userId = req.params.id;
        
        // Missing authentication check (AC6)
        // Missing authorization check - user can view any profile (AC7 violation)
        
        // SQL injection vulnerability
        const user = await db.query(`SELECT * FROM users WHERE id = ${userId}`);
        
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Missing error handling
        return res.json(user);
    }
    
    // Missing JSDoc documentation
    async updateProfile(req, res) {
        const userId = req.params.id;
        const { name, email, phone } = req.body;
        
        // Missing authentication check (AC6)
        // Missing authorization check - user can update any profile (AC7 violation)
        
        // Missing email format validation (AC4)
        // Missing phone number validation (AC5)
        
        // SQL injection vulnerability
        await db.query(`UPDATE users SET name = '${name}', email = '${email}', phone = '${phone}' WHERE id = ${userId}`);
        
        // Missing success message (AC9)
        // Missing error handling
        // Missing database transaction
        
        return res.status(200).json({ message: 'Updated' });
    }
    
    // Missing JSDoc documentation
    async uploadProfilePicture(req, res) {
        const userId = req.params.id;
        const file = req.files.profilePicture;
        
        // Missing authentication check (AC6)
        // Missing authorization check (AC7)
        
        // Missing file size validation (AC3 - should be max 5MB)
        // Missing file type validation (AC3 - should be JPG/PNG only)
        
        // Missing error handling for file upload
        // Missing file storage logic
        
        // Using HTTP instead of HTTPS (Security requirement)
        return res.status(200).json({ message: 'File uploaded' });
    }
}

module.exports = new ProfileController();

