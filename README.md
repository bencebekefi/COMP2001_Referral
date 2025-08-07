# Trail Management API

A Flask-based RESTful API for managing walking and hiking trails, built with SQLAlchemy and session-based authentication. Includes full CRUD functionality for trails and comments, with role-based access control for admin users.

---

## Overview

This project is part of a coursework assignment for COMP2001. It focuses on developing and testing a secure backend service using Flask, SQLAlchemy, and external user authentication via the university's API.

---

##  Features

- User login/logout with session handling
- Role-based access control (`User` vs `Admin`)
- CRUD operations for:
  - **Trails** 
  - **Comments** (User can create/edit own, Admin can archive, edit)
- Swagger UI documentation at `/api/docs`
- Input validation and error handling
- Soft-delete functionality for comments

---

## Endpoints Summary

| Method | Endpoint                        | Access       | Description                          |
|--------|----------------------------------|--------------|--------------------------------------|
| GET    | `/trails`                       | Public       | Get all trails                       |
| GET    | `/trails/<id>`                  | Public       | Get single trail                     |
| POST   | `/trails`                       | Admin only   | Create new trail                     |
| PUT    | `/trails/<id>`                  | Admin only   | Update trail                         |
| DELETE | `/trails/<id>`                  | Admin only   | Delete trail                         |
| GET    | `/comments`                     | Public       | View all non-archived comments       |
| GET    | `/trails/<id>/comments`         | Public       | View comments for a specific trail   |
| POST   | `/trails/<id>/comments`         | Logged-in    | Add a comment to a trail             |
| PUT    | `/comments/<id>`                | Owner/Admin  | Edit a comment                       |
| DELETE | `/comments/<id>`                | Admin only   | Archive a comment    |
| POST   | `/login`                        | Public       | Log in                               |
| POST   | `/logout`                       | Logged-in    | Log out                              |

---

##  Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/trail-api.git
   cd trail-api

   python3 app.py
   
