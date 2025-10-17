package com.example.payment;

import java.sql.*;
import java.util.*;

/**
 * Payment Processor - Demo file for AI Code Review
 * This file has intentional issues for AI to detect
 */
public class PaymentProcessor {
    
    private Connection connection;
    
    public PaymentProcessor(Connection conn) {
        this.connection = conn;
    }
    
    /**
     * Process payment - HAS SECURITY VULNERABILITIES!
     */
    public boolean processPayment(String userId, String amount, String cardNumber) {
        // SECURITY: SQL Injection vulnerability - never concatenate user input!
        String query = "INSERT INTO payments (user_id, amount, card_number) VALUES ('" 
                      + userId + "', '" + amount + "', '" + cardNumber + "')";
        
        try {
            Statement stmt = connection.createStatement();
            stmt.executeUpdate(query);
            
            // SECURITY: Storing credit card number in plaintext!
            // BUG: No validation of amount
            // BUG: No transaction handling
            
            return true;
        } catch (SQLException e) {
            // CODE QUALITY: Swallowing exception, no logging
            return false;
        }
    }
    
    /**
     * Get user balance - SQL INJECTION!
     */
    public double getUserBalance(String userId) {
        // SECURITY: SQL Injection vulnerability
        String query = "SELECT balance FROM accounts WHERE user_id = '" + userId + "'";
        
        try {
            Statement stmt = connection.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            
            if (rs.next()) {
                return rs.getDouble("balance");
            }
            
            // BUG: Resources not closed - memory leak!
            
        } catch (SQLException e) {
            e.printStackTrace(); // SECURITY: Exposing stack trace
        }
        
        return 0.0;
    }
    
    /**
     * Validate credit card - WEAK VALIDATION!
     */
    public boolean validateCard(String cardNumber) {
        // CODE QUALITY: Very weak validation
        if (cardNumber.length() == 16) {
            return true;
        }
        return false;
        
        // Missing: Luhn algorithm check
        // Missing: Card type validation
        // Missing: Expiry date check
    }
    
    /**
     * Apply discount - LOGIC BUG!
     */
    public double applyDiscount(double amount, int discountPercent) {
        // BUG: No validation - could be negative or > 100
        // BUG: Integer division issue
        
        double discount = amount * discountPercent / 100;
        return amount - discount;
        
        // What if discountPercent is 150? You'd pay customers!
    }
    
    /**
     * Get all transactions - PERFORMANCE ISSUE!
     */
    public List<Transaction> getAllTransactions() {
        List<Transaction> transactions = new ArrayList<>();
        
        try {
            // PERFORMANCE: No pagination - could return millions of rows!
            // PERFORMANCE: SELECT * is inefficient
            String query = "SELECT * FROM transactions";
            
            Statement stmt = connection.createStatement();
            ResultSet rs = stmt.executeQuery(query);
            
            // PERFORMANCE: N+1 query problem
            while (rs.next()) {
                String userId = rs.getString("user_id");
                
                // Making separate query for each transaction!
                String userQuery = "SELECT name FROM users WHERE id = '" + userId + "'";
                Statement userStmt = connection.createStatement();
                ResultSet userRs = userStmt.executeQuery(userQuery);
                
                // Creating transaction objects...
                // BUG: Resources not properly closed
            }
            
        } catch (SQLException e) {
            e.printStackTrace();
        }
        
        return transactions;
    }
    
    /**
     * Calculate fees - RACE CONDITION!
     */
    private static int transactionCount = 0;
    
    public double calculateFees(double amount) {
        // BUG: Race condition with static variable in multi-threaded environment
        transactionCount++;
        
        // CODE QUALITY: Magic numbers
        if (transactionCount > 100) {
            return amount * 0.01; // 1% fee
        } else {
            return amount * 0.02; // 2% fee
        }
    }
    
    /**
     * Refund payment - MISSING AUTHENTICATION!
     */
    public void refundPayment(String paymentId) {
        // SECURITY: No authorization check!
        // Any user could refund any payment
        
        String query = "UPDATE payments SET status = 'refunded' WHERE id = '" + paymentId + "'";
        
        try {
            Statement stmt = connection.createStatement();
            stmt.executeUpdate(query);
        } catch (SQLException e) {
            // CODE QUALITY: Silent failure
        }
    }
    
    // TESTING: No unit tests for any of these critical payment functions!
}

// DESIGN: This class violates Single Responsibility Principle
// DESIGN: No interface, tight coupling to JDBC
// SECURITY: Passwords and sensitive data should be encrypted
// PERFORMANCE: No connection pooling
// CODE QUALITY: No input validation anywhere

