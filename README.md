# BulletNEWS

A real-time news platform providing concise, bullet-point style news updates.

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Git (optional, for version control)

### Installation Steps

1. **Clone the repository** (if using Git):

   ```bash
   git clone <repository-url>
   cd BulletNEWS
   ```

2. **Create and activate a virtual environment**:

   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:

   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   ```

5. **Run migrations**:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser** (optional):

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
BulletNEWS/
├── BulletNEWS/          # Project settings
├── blog/                # Blog app
├── news/                # News app
├── newsfeed/           # News feed app
├── users/              # User management app
├── core/               # Core functionality
├── static/             # Static files
├── templates/          # HTML templates
├── media/              # User-uploaded files
├── requirements.txt    # Project dependencies
└── manage.py          # Django management script
```

## Common Issues and Solutions

1. **ModuleNotFoundError**:

   - Ensure you're in the virtual environment
   - Run `pip install -r requirements.txt` again

2. **Database errors**:

   - Check your database settings in settings.py
   - Ensure migrations are up to date

3. **Static files not loading**:

   - Run `python manage.py collectstatic`
   - Check STATIC_URL and STATIC_ROOT settings

4. **Port already in use**:
   - Change the port: `python manage.py runserver 8001`
   - Or kill the process using the port

## Development Guidelines

1. Always work in a virtual environment
2. Keep requirements.txt updated
3. Follow PEP 8 style guide
4. Write meaningful commit messages
5. Test changes before committing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# Final-BulletNEWS
