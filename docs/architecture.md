# System Architecture Document

## Overview
This document outlines the system architecture, workflow, endpoints, and data models for the Cineforge application.

## System Architecture
The Cineforge application is built using a microservices architecture where each service handles specific functionality. The architecture consists of:

- **Frontend:** Built with React.js, it communicates with backend services through RESTful APIs.
- **Backend Services:**
  - **User Service:** Handles user authentication and management.
  - **Media Service:** Manages media uploads, processing, and storage.
  - **Comment Service:** Manages user comments and interactions on media.
- **Database:** A NoSQL database like MongoDB is used for flexibility and scalability.

![System Architecture Diagram](path/to/architecture_diagram.png)

## Workflow
1. **User Registration:** Users can register using the frontend application, which sends a request to the User Service.
2. **Authentication:** Users log in, and the User Service issues a token for authenticated requests.
3. **Media Upload:** Users can upload media, which is handled by the Media Service.
4. **Commenting:** Users can comment on media, which is managed by the Comment Service.
5. **Data Storage:** All user and media data are stored in the NoSQL database.

## Endpoints
### User Service
- `POST /api/users/register`: Register a new user.
- `POST /api/users/login`: User authentication.

### Media Service
- `POST /api/media/upload`: Upload media file.
- `GET /api/media/{id}`: Retrieve media details.

### Comment Service
- `POST /api/comments`: Add a comment.
- `GET /api/comments/{mediaId}`: Get comments for a media item.

## Data Models
### User
```json
{
  "id": "string",
  "username": "string",
  "password": "string",
  "email": "string"
}
```

### Media
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "url": "string",
  "uploadDate": "string"
}
```

### Comment
```json
{
  "id": "string",
  "mediaId": "string",
  "userId": "string",
  "comment": "string",
  "timestamp": "string"
}
```

## Conclusion
This document serves as a comprehensive guide to the architecture, workflows, endpoints, and data models of the Cineforge application, assisting developers in understanding the system’s implementation and functionality.