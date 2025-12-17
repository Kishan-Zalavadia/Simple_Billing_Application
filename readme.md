# Billing System

A comprehensive billing and inventory management system built with Flask, featuring real-time bill calculations, PDF generation, and customer management.

## Features

### Core Functionality
- ✅ Shop setup and management (single shop system)
- ✅ Items catalog with CRUD operations
- ✅ Bill creation with item selection
- ✅ Live bill preview with real-time calculations
- ✅ Tax calculation (configurable tax rate)
- ✅ Professional PDF generation with company header
- ✅ Bill storage and history
- ✅ Customer details capture
- ✅ Automatic bill numbering

### Technical Features
- SQLAlchemy ORM for database operations
- Bootstrap 5 for responsive design
- ReportLab for PDF generation
- AJAX for real-time calculations
- Form validation and error handling
- Flash messages for user feedback

## Project Structure

```
billing_system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── billing.db            # SQLite database (created automatically)
└── templates/            # HTML templates
    ├── base.html         # Base template with navigation
    ├── index.html        # Dashboard
    ├── shop_setup.html   # Shop configuration
    ├── items.html        # Items listing
    ├── add_item.html     # Add new item
    ├── edit_item.html    # Edit existing item
    ├── bills.html        # Bills listing
    └── create_bill.html  # Bill creation with live preview
```

## Installation

### 1. Create a virtual environment

**Linux/Mac:**
```bash
python3 -m venv billing_env
source billing_env/bin/activate
```

**Windows:**
```cmd
python -m venv billing_env
billing_env\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

### 4. Access the application

Open your browser and visit: [http://localhost:5000](http://localhost:5000)

## Requirements

Create a `requirements.txt` file with the following dependencies:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
reportlab==4.0.7
```

## Usage

1. **Shop Setup**: Configure your shop details (name, address, contact info)
2. **Add Items**: Create your product catalog with prices
3. **Create Bills**: Select items, specify quantities, and generate bills
4. **View History**: Access past bills and download PDFs
5. **Manage Inventory**: Edit or delete items as needed

## Database

The application uses SQLite database (`billing.db`) which is created automatically on first run. No manual database setup required.

## License

This project is open source and available for personal and commercial use.

## Support


