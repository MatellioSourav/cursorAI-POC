# E-Commerce Application - API Specifications

## Base URL
```
https://api.example.com/v1
```

## Authentication

Most endpoints require JWT authentication. Include token in Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### 1. Product Catalog

#### GET /api/products
List products with pagination and filters.

**Query Parameters**:
- `page` (integer, default: 1): Page number
- `limit` (integer, default: 20, max: 100): Items per page
- `category` (string, optional): Filter by category
- `search` (string, optional): Search query
- `sort` (string, optional): Sort by (price_asc, price_desc, name_asc, name_desc)

**Response**:
```json
{
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "description": "Product description",
      "price": 29.99,
      "image": "https://example.com/image.jpg",
      "category": "Electronics",
      "stock": 50,
      "inStock": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

**Status Codes**:
- 200: Success
- 400: Invalid parameters

#### GET /api/products/:productId
Get product details.

**Response**:
```json
{
  "id": 1,
  "name": "Product Name",
  "description": "Detailed description",
  "price": 29.99,
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "category": {
    "id": 1,
    "name": "Electronics"
  },
  "specifications": {
    "brand": "Brand Name",
    "model": "Model Number"
  },
  "stock": 50,
  "inStock": true,
  "relatedProducts": [
    {
      "id": 2,
      "name": "Related Product",
      "price": 39.99,
      "image": "https://example.com/related.jpg"
    }
  ]
}
```

**Status Codes**:
- 200: Success
- 404: Product not found

### 2. Shopping Cart

#### POST /api/cart/add
Add item to cart.

**Authentication**: Required

**Request Body**:
```json
{
  "productId": 1,
  "quantity": 2
}
```

**Response**:
```json
{
  "cart": {
    "id": 123,
    "items": [
      {
        "id": 1,
        "product": {
          "id": 1,
          "name": "Product Name",
          "price": 29.99,
          "image": "https://example.com/image.jpg"
        },
        "quantity": 2,
        "subtotal": 59.98
      }
    ],
    "subtotal": 59.98,
    "tax": 5.998,
    "shipping": 5.00,
    "total": 70.978
  }
}
```

**Status Codes**:
- 200: Success
- 400: Invalid input or out of stock
- 401: Unauthorized
- 404: Product not found

#### GET /api/cart
Get current cart.

**Authentication**: Required

**Response**:
```json
{
  "cart": {
    "id": 123,
    "items": [
      {
        "id": 1,
        "product": {
          "id": 1,
          "name": "Product Name",
          "price": 29.99,
          "image": "https://example.com/image.jpg"
        },
        "quantity": 2,
        "subtotal": 59.98
      }
    ],
    "subtotal": 59.98,
    "tax": 5.998,
    "shipping": 5.00,
    "total": 70.978,
    "freeShippingEligible": false
  }
}
```

**Status Codes**:
- 200: Success
- 401: Unauthorized

#### PUT /api/cart/:itemId
Update cart item quantity.

**Authentication**: Required

**Request Body**:
```json
{
  "quantity": 3
}
```

**Response**: Same as GET /api/cart

**Status Codes**:
- 200: Success
- 400: Invalid quantity or out of stock
- 401: Unauthorized
- 404: Cart item not found

#### DELETE /api/cart/:itemId
Remove item from cart.

**Authentication**: Required

**Response**: Same as GET /api/cart

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 404: Cart item not found

### 3. Orders

#### POST /api/orders
Create order from cart.

**Authentication**: Required

**Request Body**:
```json
{
  "shippingAddress": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "USA"
  },
  "paymentMethod": "credit_card"
}
```

**Response**:
```json
{
  "order": {
    "id": "ORD-12345",
    "status": "pending",
    "items": [
      {
        "product": {
          "id": 1,
          "name": "Product Name",
          "price": 29.99
        },
        "quantity": 2,
        "subtotal": 59.98
      }
    ],
    "subtotal": 59.98,
    "tax": 5.998,
    "shipping": 5.00,
    "total": 70.978,
    "shippingAddress": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zip": "10001",
      "country": "USA"
    },
    "createdAt": "2024-01-20T10:00:00Z"
  }
}
```

**Status Codes**:
- 201: Order created
- 400: Invalid input or out of stock
- 401: Unauthorized
- 409: Cart is empty

#### GET /api/orders/:orderId
Get order details.

**Authentication**: Required

**Response**: Same as POST /api/orders response

**Status Codes**:
- 200: Success
- 401: Unauthorized
- 403: Forbidden (not user's order)
- 404: Order not found

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common Error Codes**:
- `VALIDATION_ERROR`: Invalid input
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `OUT_OF_STOCK`: Product out of stock
- `INVALID_QUANTITY`: Quantity exceeds stock
- `EMPTY_CART`: Cart is empty

## Rate Limiting

- Product endpoints: 100 requests/minute
- Cart endpoints: 60 requests/minute
- Order endpoints: 30 requests/minute

## Versioning

API version is included in URL path: `/v1/`

Future versions will use `/v2/`, `/v3/`, etc.

