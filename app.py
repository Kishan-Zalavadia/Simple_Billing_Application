# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)   

# Database Models
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(200))
    customer_address = db.Column(db.Text)
    customer_contact = db.Column(db.String(20))
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=18.0)  # GST percentage
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    
    # Add these two lines:
    discount_type = db.Column(db.String(20), default='percentage')  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bill_items = db.relationship('BillItem', backref='bill', lazy=True, cascade='all, delete-orphan')

class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    item = db.relationship('Item', backref='bill_items')

# Routes
@app.route('/')
def index():
    shop = Shop.query.first()
    items_count = Item.query.count()
    bills_count = Bill.query.count()
    return render_template('index.html', shop=shop, items_count=items_count, bills_count=bills_count)

@app.route('/shop/setup', methods=['GET', 'POST'])
def shop_setup():
    if request.method == 'POST':
        # Delete existing shop (single shop system)
        Shop.query.delete()
        
        shop = Shop(
            name=request.form['name'],
            address=request.form['address'],
            contact_number=request.form['contact_number'],
            email=request.form.get('email'),
            tax_number=request.form.get('tax_number')
        )
        db.session.add(shop)
        db.session.commit()
        flash('Shop details updated successfully!', 'success')
        return redirect(url_for('index'))
    
    shop = Shop.query.first()
    return render_template('shop_setup.html', shop=shop)

@app.route('/items')
def items():
    items = Item.query.all()
    return render_template('items.html', items=items)

@app.route('/items/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        item = Item(
            name=request.form['name'],
            description=request.form.get('description'),
            price=float(request.form['price']),
            category=request.form.get('category')
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('items'))
    
    return render_template('add_item.html')

@app.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form.get('description')
        item.price = float(request.form['price'])
        item.category = request.form.get('category')
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('items'))
    
    return render_template('edit_item.html', item=item)

@app.route('/items/delete/<int:item_id>')
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('items'))

@app.route('/bills')
def bills():
    bills = Bill.query.order_by(Bill.created_at.desc()).all()
    return render_template('bills.html', bills=bills)

@app.route('/bills/create')
def create_bill():
    items = Item.query.all()
    return render_template('create_bill.html', items=items)

@app.route('/api/calculate_bill', methods=['POST'])
def calculate_bill():
    data = request.get_json()
    bill_items = data.get('items', [])
    tax_rate = float(data.get('tax_rate', 18.0))
    discount_type = data.get('discount_type', 'percentage')
    discount_value = float(data.get('discount_value', 0.0))

    subtotal = 0
    calculated_items = []

    for item_data in bill_items:
        item = Item.query.get(item_data['item_id'])
        if item:
            quantity = int(item_data['quantity'])
            unit_price = item.price
            total_price = quantity * unit_price
            subtotal += total_price

            calculated_items.append({
                'name': item.name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })

    # Calculate Discount
    if discount_type == 'percentage':
        discount_amount = (subtotal * discount_value) / 100
    else:  # fixed
        discount_amount = discount_value

    discounted_amount = subtotal - discount_amount
    
    # Calculate Tax
    tax_amount = (discounted_amount * tax_rate) / 100
    total_amount = discounted_amount + tax_amount

    return jsonify({
        'items': calculated_items,
        'subtotal': round(subtotal, 2),
        'discount_type': discount_type,
        'discount_value': discount_value,
        'discount_amount': round(discount_amount, 2),
        'discounted_amount': round(discounted_amount, 2),
        'tax_rate': tax_rate,
        'tax_amount': round(tax_amount, 2),
        'total_amount': round(total_amount, 2)
    })

@app.route('/bills/save', methods=['POST'])
def save_bill():
    data = request.get_json()

    # Generate bill number
    last_bill = Bill.query.order_by(Bill.id.desc()).first()
    bill_number = f"INV-{(last_bill.id + 1) if last_bill else 1:04d}"

    # Create bill
    bill = Bill(
        bill_number=bill_number,
        customer_name=data.get('customer_name'),
        customer_address=data.get('customer_address'),
        customer_contact=data.get('customer_contact'),
        subtotal=data.get('subtotal'),
        tax_rate=data.get('tax_rate'),
        tax_amount=data.get('tax_amount'),
        total_amount=data.get('total_amount'),
        discount_type=data.get('discount_type'),  # Add this line
        discount_value=data.get('discount_value')   # Add this line
    )
    db.session.add(bill)
    db.session.flush()  # Get the bill ID

    # Add bill items
    for item_data in data.get('items', []):
        bill_item = BillItem(
            bill_id=bill.id,
            item_id=item_data['item_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            total_price=item_data['total_price']
        )
        db.session.add(bill_item)

    db.session.commit()

    return jsonify({
        'success': True,
        'bill_id': bill.id,
        'bill_number': bill.bill_number
    })

@app.route('/bills/download/<int:bill_id>')
def download_bill(bill_id):
    """
    Generates a professionally designed PDF invoice and returns it for download.
    
    This enhanced version features:
    - A modern color scheme.
    - A two-column header for shop and invoice details.
    - Improved table styling with alternating row colors (zebra striping).
    - Correct text alignment for items and financials.
    - A clear, right-aligned section for totals.
    - A professional footer.
    """
    # In a real Flask app, you'd get these from your database.
    bill = Bill.query.get_or_404(bill_id)
    shop = Shop.query.first()

    # --- Document Setup ---
    buffer = BytesIO()
    # Set top and bottom margins
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    # --- Custom Styles ---
    styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='LeftAlign', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='InvoiceTitle', fontSize=22, fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=colors.HexColor('#003366')))
    styles.add(ParagraphStyle(name='ShopTitle', fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#003366')))
    styles.add(ParagraphStyle(name='FooterStyle', fontSize=8, alignment=TA_CENTER, textColor=colors.grey))
    
    # --- Header Section ---
    header_data = [
        [
            Paragraph(shop.name, styles['ShopTitle']),
            Paragraph("INVOICE", styles['InvoiceTitle'])
        ],
        [
            Paragraph(f"""{shop.address}<br/>Contact: {shop.contact_number}<br/>Email: {shop.email or ''}<br/>{f"Tax No: {shop.tax_number}" if shop.tax_number else ''}""",styles['Normal']
),
            Paragraph(f"<b>Bill Number:</b> {bill.bill_number}<br/><b>Date:</b> {bill.created_at.strftime('%Y-%m-%d')}", styles['RightAlign'])
        ]
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('SPAN', (1, 0), (1, 0)), # Span INVOICE title
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    
    story.append(Spacer(1, 0.25*inch))
    
    # --- Customer Details Section ---
    if bill.customer_name:
        customer_details_data = [
            [Paragraph("<b>Bill To:</b>", styles['Normal'])],
            [Paragraph(bill.customer_name, styles['Normal'])],
            [Paragraph(bill.customer_address or '', styles['Normal'])],
            [Paragraph(f"Contact: {bill.customer_contact or ''}", styles['Normal'])],
        ]
        customer_table = Table(customer_details_data, colWidths=[7*inch])
        customer_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(customer_table)

    story.append(Spacer(1, 0.25*inch))
    
    # --- Items Table and Financials ---
    table_header = ['Item Description', 'Quantity', 'Unit Price', 'Total']
    table_data = [table_header]
    
    for bill_item in bill.bill_items:
        table_data.append([
            Paragraph(bill_item.item.name, styles['Normal']),
            str(bill_item.quantity),
            f"{bill_item.unit_price:.2f}",
            f"{bill_item.total_price:.2f}"
        ])
    
    # --- Financial Calculations ---
    if bill.discount_type == 'percentage':
        discount_amount = (bill.subtotal * bill.discount_value) / 100
        discount_label = f'Discount ({bill.discount_value}%)'
    else:
        discount_amount = bill.discount_value
        discount_label = 'Discount'
    
    discounted_amount = bill.subtotal - discount_amount

    # --- Append Financials to Table Data ---
    summary_start_row = len(table_data)
    table_data.append(['', '', 'Subtotal:', f"{bill.subtotal:.2f}"])
    
    if bill.discount_value > 0:
        table_data.append(['', '', discount_label, f"-{discount_amount:.2f}"])
        table_data.append(['', '', 'Amount After Discount:', f"{discounted_amount:.2f}"])
    
    table_data.append(['', '', f'Tax ({bill.tax_rate}%):', f"{bill.tax_amount:.2f}"])
    table_data.append(['', '', '', '']) # Blank spacer row
    table_data.append(['', '', 'Total Amount:', f"{bill.total_amount:.2f}"])
    
    # --- Create and Style the Table ---
    items_table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch])
    
    final_total_row_index = len(table_data) - 1
    blank_row_index = final_total_row_index - 1

    table_style_commands = [
        # General styling
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),

        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Column alignment for item rows
        ('ALIGN', (0, 1), (0, summary_start_row - 1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, summary_start_row - 1), 'RIGHT'),

        # Zebra striping for item rows
        ('ROWBACKGROUNDS', (0, 1), (-1, summary_start_row - 1), [colors.HexColor('#E0E8F0'), colors.white]),
        
        # Grid for item rows only
        ('GRID', (0, 0), (-1, summary_start_row - 1), 1, colors.HexColor('#C0C0C0')),

        # Styling for the summary section
        ('SPAN', (0, summary_start_row), (1, final_total_row_index)),
        ('ALIGN', (2, summary_start_row), (-1, final_total_row_index), 'RIGHT'),
        ('LINEABOVE', (2, summary_start_row), (-1, summary_start_row), 1, colors.HexColor('#C0C0C0')),

        # Remove border from the blank spacer row
        ('LINEABOVE', (2, blank_row_index), (-1, blank_row_index), 0, colors.white),

        # Style the final total row
        ('FONTNAME', (2, final_total_row_index), (-1, final_total_row_index), 'Helvetica-Bold'),
        ('FONTSIZE', (2, final_total_row_index), (-1, final_total_row_index), 12),
        ('BACKGROUND', (2, final_total_row_index), (-1, final_total_row_index), colors.HexColor('#E0E8F0')),
        ('TOPPADDING', (2, final_total_row_index), (-1, final_total_row_index), 8),
        ('BOTTOMPADDING', (2, final_total_row_index), (-1, final_total_row_index), 8),
        ('GRID', (2, final_total_row_index), (-1, final_total_row_index), 1, colors.HexColor('#003366')),
    ]
    
    items_table.setStyle(TableStyle(table_style_commands))
    
    story.append(items_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # --- Footer ---
    story.append(Paragraph("Thank you for your business!", styles['FooterStyle']))
    
    # --- Build PDF ---
    doc.build(story)
    
    buffer.seek(0)
    return send_file(buffer, download_name=f"bill_{bill.bill_number}.pdf", as_attachment=True)

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)