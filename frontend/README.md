
# Junior Developer API Testing Interface

A comprehensive frontend testing application for the Junior Developer Program's Python/FastAPI backend APIs. This single-page application provides a complete UI for testing all API endpoints across the program.

## 🚀 Features

### Complete API Coverage
- **Authentication System**: User registration, login, profile management
- **Book Management**: Full CRUD operations with relationships
- **Author Management**: Create, read, update author information
- **Category Management**: Organize books by categories
- **Review System**: User reviews and ratings for books
- **Statistics Dashboard**: API usage and data statistics

### User-Friendly Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Tabbed Navigation**: Organized sections for different API endpoints
- **Real-time Feedback**: Instant notifications for all operations
- **Authentication Status**: Visual indicator of login status
- **Form Validation**: Client-side validation with helpful error messages

### Developer-Friendly Features
- **Easy Configuration**: Simply change the base URL to test different environments
- **JWT Token Management**: Automatic token storage and authentication headers
- **Response Display**: Formatted JSON responses with status codes
- **Error Handling**: Comprehensive error messages and debugging information
- **Pagination Support**: Handle large datasets with pagination controls

## 📋 Quick Start

### 1. Setup
1. Download all files to a directory
2. Open `index.html` in a web browser
3. Configure the API base URL (default: `http://localhost:8000`)

### 2. Basic Usage
1. **Start your FastAPI backend** 
2. **Register a new user** in the Authentication tab
3. **Login** to get authentication token
4. **Test API endpoints** across different tabs
5. **View responses** in the response sections

### 3. Configuration
- **Base URL**: Change in the configuration section at the top
- **Authentication**: Automatic token management after login
- **Persistence**: Settings and tokens are saved in browser localStorage

## 🔧 Configuration

### Changing API Base URL
1. Locate the configuration section at the top of the interface
2. Update the "API Base URL" field
3. The new URL is automatically saved and used for all requests

### Example URLs:
- Local development: `http://localhost:8000`
- Docker container: `http://localhost:8080`
- Remote server: `https://your-api-domain.com`

## 📚 API Endpoints Covered

### Authentication Endpoints
```
POST /register          - User registration
POST /login            - User login
GET  /me               - Get current user profile
```

### Book Endpoints
```
GET    /books           - Get all books (with pagination and filters)
GET    /books/{id}      - Get book by ID
POST   /books           - Create new book
PUT    /books/{id}      - Update book
DELETE /books/{id}      - Delete book
```

### Author Endpoints
```
GET    /authors         - Get all authors
GET    /authors/{id}    - Get author by ID
POST   /authors         - Create new author
PUT    /authors/{id}    - Update author
```

### Category Endpoints
```
GET    /categories      - Get all categories
POST   /categories      - Create new category
```

### Review Endpoints
```
GET    /reviews         - Get all reviews
GET    /reviews/{id}    - Get review by ID
POST   /reviews         - Create new review
PUT    /reviews/{id}    - Update review
DELETE /reviews/{id}    - Delete review
```

### Statistics Endpoints
```
GET    /stats           - Get API statistics
```

## 🎯 Testing Workflows

### 1. Basic Book Management
1. Create an author first
2. Create a category
3. Create a book with author and category
4. Test getting, updating, and deleting the book

### 2. Review System Testing
1. Ensure you're logged in
2. Create a book (or use existing book ID)
3. Create a review for the book
4. Test getting, updating, and deleting reviews

### 3. Advanced Features
1. Test book filtering by author, category, rating
2. Test search functionality
3. Test pagination with large datasets
4. Test authentication-protected endpoints

## 📊 Expected API Responses

### User Registration (201 Created)
```json
{
    "id": 1,
    "email": "user@example.com",
    "is_active": true,
    "role": "user",
    "created_at": "2023-09-12T10:30:00.123456"
}
```

### Login Response (200 OK)
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### Book Response (200 OK)
```json
{
    "id": 1,
    "title": "The Python Guide",
    "isbn": "978-0123456789",
    "published_date": "2023-01-15",
    "description": "A comprehensive guide to Python programming",
    "created_by": 1,
    "created_at": "2023-09-12T10:30:00.123456",
    "author": {
        "id": 1,
        "name": "John Doe",
        "bio": "Experienced Python developer",
        "nationality": "American"
    },
    "categories": [
        {
            "id": 1,
            "name": "Programming",
            "description": "Programming books"
        }
    ],
    "reviews": [
        {
            "id": 1,
            "rating": 5,
            "comment": "Excellent book!",
            "user": {
                "email": "user@example.com"
            }
        }
    ]
}
```

### Paginated Books Response (200 OK)
```json
{
    "items": [...],
    "total": 50,
    "page": 1,
    "size": 10,
    "pages": 5
}
```

### Error Response (400/401/403/404)
```json
{
    "detail": "Book not found"
}
```

## 🔐 Authentication

### JWT Token Management
- Tokens are automatically stored in browser localStorage
- Authentication headers are added to all protected requests
- Visual authentication status indicator
- Automatic logout functionality

### Protected Endpoints
- Creating books, authors, categories, reviews requires authentication
- Updating/deleting resources requires ownership or admin role
- Profile access requires valid authentication

## 🎨 Interface Features

### Visual Indicators
- **Green dot**: Authenticated
- **Red dot**: Not authenticated
- **Success notifications**: Green background
- **Error notifications**: Red background
- **Info notifications**: Blue background

### Form Features
- **Auto-clear**: Forms clear after successful operations
- **Validation**: Client-side validation with error messages
- **Placeholders**: Helpful placeholder text for all inputs
- **Date pickers**: Easy date selection for published dates and birth dates

### Response Display
- **Formatted JSON**: Pretty-printed JSON responses
- **Status codes**: HTTP status codes displayed
- **Syntax highlighting**: Terminal-style response display
- **Scrollable**: Large responses are scrollable

## 🛠️ Troubleshooting

### Common Issues

#### "Failed to fetch" Error
- **Cause**: Backend server not running or wrong URL
- **Solution**: Ensure your FastAPI server is running and URL is correct

#### "401 Unauthorized" Error
- **Cause**: Not logged in or token expired
- **Solution**: Login again to get a fresh token

#### "403 Forbidden" Error
- **Cause**: Insufficient permissions (e.g., non-admin trying admin operation)
- **Solution**: Login with appropriate role or check endpoint requirements

#### "404 Not Found" Error
- **Cause**: Resource doesn't exist or wrong ID
- **Solution**: Verify the resource exists and ID is correct

### CORS Issues
If you encounter CORS errors, ensure your FastAPI backend includes CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 Data Persistence

### Browser Storage
- **API Base URL**: Saved in localStorage
- **Authentication Token**: Saved in localStorage
- **User Information**: Saved in localStorage

### Session Management
- Tokens persist across browser sessions
- Automatic authentication status checking
- Clean logout removes all stored data

## 📈 Advanced Features

### Filtering and Search
- **Text search**: Search books by title and description
- **Author filter**: Filter books by specific author
- **Category filter**: Filter books by category
- **Rating filter**: Filter books by minimum rating

### Pagination
- **Page navigation**: Previous/Next buttons
- **Page numbers**: Direct page access
- **Page size**: Configurable items per page
- **Total count**: Display total items and pages

### Statistics Dashboard
- **Total counts**: Books, authors, categories, reviews
- **Average rating**: Overall rating across all books
- **Visual cards**: Clean statistical display

