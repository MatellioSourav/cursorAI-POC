/**
 * Data Validator Module - JavaScript/TypeScript
 * This file has intentional issues for AI code review
 */

// SECURITY: Sensitive data in comments
// Admin password: admin123 (TODO: remove this)

class DataValidator {
  constructor() {
    this.validationRules = {};
  }

  // BUG: No input validation
  validateEmail(email) {
    // CODE QUALITY: Weak regex pattern
    return email.includes('@');
  }

  // SECURITY: Vulnerable to ReDoS (Regular Expression Denial of Service)
  validatePassword(password) {
    const regex = /^(([a-zA-Z0-9])+)*$/;
    return regex.test(password);
  }

  // PERFORMANCE: Inefficient array operations
  findDuplicates(array) {
    const duplicates = [];
    // PERFORMANCE: O(n²) complexity
    for (let i = 0; i < array.length; i++) {
      for (let j = i + 1; j < array.length; j++) {
        if (array[i] === array[j]) {
          duplicates.push(array[i]);
        }
      }
    }
    return duplicates;
  }

  // BUG: Mutates input array (side effect)
  sortAndReturn(array) {
    return array.sort(); // Modifies original array!
  }

  // CODE QUALITY: Inconsistent error handling
  parseJSON(jsonString) {
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      // CODE QUALITY: Swallowing error, no logging
      return null;
    }
  }

  // SECURITY: Vulnerable to prototype pollution
  mergeObjects(target, source) {
    for (let key in source) {
      target[key] = source[key];
    }
    return target;
  }

  // PERFORMANCE: Creating new Date() in a loop
  filterRecentItems(items, days) {
    return items.filter(item => {
      const now = new Date(); // BUG: Should be outside loop
      const itemDate = new Date(item.date);
      const diff = (now - itemDate) / (1000 * 60 * 60 * 24);
      return diff <= days;
    });
  }
}

// SECURITY: Dangerous use of eval
function executeUserCode(code) {
  // CRITICAL: Never use eval with user input!
  return eval(code);
}

// BUG: No null/undefined checks
function processUserData(user) {
  const fullName = user.firstName + ' ' + user.lastName;
  const email = user.email.toLowerCase();
  const age = parseInt(user.age);
  
  return { fullName, email, age };
}

// BOILERPLATE: Repetitive validation functions
function validateName(name) {
  if (!name) return false;
  if (name.length < 2) return false;
  if (name.length > 50) return false;
  return true;
}

function validateAge(age) {
  if (!age) return false;
  if (age < 0) return false;
  if (age > 150) return false;
  return true;
}

function validatePhone(phone) {
  if (!phone) return false;
  if (phone.length < 10) return false;
  if (phone.length > 15) return false;
  return true;
}

// PERFORMANCE: Memory leak - event listeners not removed
class EventManager {
  constructor() {
    this.listeners = [];
  }

  addEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    this.listeners.push({ element, event, handler });
    // BUG: No cleanup method provided
  }
}

// CODE QUALITY: Magic numbers everywhere
function calculateDiscount(price, userLevel) {
  if (userLevel === 1) {
    return price * 0.95; // 5% discount
  } else if (userLevel === 2) {
    return price * 0.90; // 10% discount
  } else if (userLevel === 3) {
    return price * 0.85; // 15% discount
  }
  return price;
}

// SECURITY: SQL-like injection in NoSQL
function findUserByName(db, userName) {
  // SECURITY: Direct user input in query
  return db.collection('users').find({ 
    $where: `this.name == '${userName}'` 
  });
}

// BUG: Race condition possible
let counter = 0;
async function incrementCounter() {
  const current = counter;
  await new Promise(resolve => setTimeout(resolve, 100));
  counter = current + 1; // Race condition!
}

// TESTING: No unit tests for any of these functions!
// TESTING: No integration tests
// TESTING: No validation of edge cases

module.exports = {
  DataValidator,
  executeUserCode,
  processUserData,
  validateName,
  validateAge,
  validatePhone
};

