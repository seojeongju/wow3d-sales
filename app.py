from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)

# 데이터베이스 모델
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    unit = db.Column(db.String(20))
    stock = db.Column(db.Integer, default=0)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# 라우트
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        unit = request.form['unit']
        
        product = Product(name=name, description=description, unit=unit)
        db.session.add(product)
        db.session.commit()
        flash('제품이 추가되었습니다.')
        return redirect(url_for('products'))
    
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        phone = request.form['phone']
        address = request.form['address']
        
        supplier = Supplier(name=name, contact=contact, phone=phone, address=address)
        db.session.add(supplier)
        db.session.commit()
        flash('구매처가 추가되었습니다.')
        return redirect(url_for('suppliers'))
    
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        phone = request.form['phone']
        address = request.form['address']
        
        customer = Customer(name=name, contact=contact, phone=phone, address=address)
        db.session.add(customer)
        db.session.commit()
        flash('판매처가 추가되었습니다.')
        return redirect(url_for('customers'))
    
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        product_id = request.form['product_id']
        supplier_id = request.form['supplier_id']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        
        purchase = Purchase(product_id=product_id, supplier_id=supplier_id,
                          quantity=quantity, price=price)
        product = Product.query.get(product_id)
        product.stock += quantity
        
        db.session.add(purchase)
        db.session.commit()
        flash('구매가 등록되었습니다.')
        return redirect(url_for('purchase'))
    
    products = Product.query.all()
    suppliers = Supplier.query.all()
    purchases = Purchase.query.all()
    return render_template('purchase.html', products=products, suppliers=suppliers, purchases=purchases)

@app.route('/sale', methods=['GET', 'POST'])
def sale():
    if request.method == 'POST':
        product_id = request.form['product_id']
        customer_id = request.form['customer_id']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        
        product = Product.query.get(product_id)
        if product.stock >= quantity:
            sale = Sale(product_id=product_id, customer_id=customer_id,
                       quantity=quantity, price=price)
            product.stock -= quantity
            
            db.session.add(sale)
            db.session.commit()
            flash('판매가 등록되었습니다.')
        else:
            flash('재고가 부족합니다!')
        return redirect(url_for('sale'))
    
    products = Product.query.all()
    customers = Customer.query.all()
    sales = Sale.query.all()
    return render_template('sale.html', products=products, customers=customers, sales=sales)

@app.route('/summary')
def summary():
    # Get the selected month from query parameters, default to current month
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    try:
        # Parse the selected month
        year, month = map(int, selected_month.split('-'))
        start_date = datetime(year, month, 1)
        # Calculate end date (first day of next month)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Get all products
        products = Product.query.all()
        
        # Create a dictionary to store purchase and sale quantities by product
        product_stats = {}
        for product in products:
            product_stats[product.id] = {
                'purchase_qty': 0,
                'sale_qty': 0
            }
        
        # Calculate purchase quantities for the month
        purchases = Purchase.query.filter(
            Purchase.date >= start_date,
            Purchase.date < end_date
        ).all()
        
        for purchase in purchases:
            product_stats[purchase.product_id]['purchase_qty'] += purchase.quantity
        
        # Calculate sale quantities for the month
        sales = Sale.query.filter(
            Sale.date >= start_date,
            Sale.date < end_date
        ).all()
        
        for sale in sales:
            product_stats[sale.product_id]['sale_qty'] += sale.quantity
        
        return render_template('summary.html', 
                             products=products, 
                             product_stats=product_stats,
                             purchases=purchases, 
                             sales=sales, 
                             selected_month=selected_month)
    
    except ValueError:
        return render_template('summary.html', 
                             error="올바른 날짜 형식을 선택해주세요.",
                             products=[],
                             purchases=[],
                             sales=[],
                             selected_month=selected_month)

@app.route('/suppliers/edit/<int:id>', methods=['POST'])
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    supplier.name = request.form['name']
    supplier.contact = request.form['contact']
    supplier.phone = request.form['phone']
    supplier.address = request.form['address']
    
    # 관련된 구매 내역 업데이트
    purchases = Purchase.query.filter_by(supplier_id=id).all()
    for purchase in purchases:
        purchase.supplier_name = supplier.name  # 구매 내역에 새로운 업체명 반영
    
    db.session.commit()
    flash('구매처 정보가 수정되었습니다.')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/check/<int:id>', methods=['GET'])
def check_supplier(id):
    purchases = Purchase.query.filter_by(supplier_id=id).count()
    can_delete = purchases == 0
    return jsonify({
        'can_delete': can_delete,
        'message': '이 구매처와 연결된 구매 내역이 있어 삭제할 수 없습니다.' if not can_delete else ''
    })

@app.route('/suppliers/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    purchases = Purchase.query.filter_by(supplier_id=id).count()
    if purchases > 0:
        return jsonify({
            'success': False,
            'message': '이 구매처와 연결된 구매 내역이 있어 삭제할 수 없습니다.'
        }), 400
    
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('구매처가 삭제되었습니다.')
    return jsonify({'success': True})

@app.route('/customers/edit/<int:id>', methods=['POST'])
def edit_customer(id):
    try:
        customer = Customer.query.get_or_404(id)
        customer.name = request.form['name']
        customer.contact = request.form['contact']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/customers/check/<int:id>', methods=['GET'])
def check_customer(id):
    sales = Sale.query.filter_by(customer_id=id).count()
    can_delete = sales == 0
    return jsonify({
        'can_delete': can_delete,
        'message': '이 판매처와 연결된 판매 내역이 있어 삭제할 수 없습니다.' if not can_delete else ''
    })

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    try:
        sales = Sale.query.filter_by(customer_id=id).count()
        if sales > 0:
            return jsonify({
                'success': False,
                'message': '이 판매처와 연결된 판매 내역이 있어 삭제할 수 없습니다.'
            }), 400
        
        customer = Customer.query.get_or_404(id)
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/products/edit/<int:id>', methods=['POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    product.name = request.form['name']
    product.description = request.form['description']
    product.unit = request.form['unit']
    db.session.commit()
    flash('제품 정보가 수정되었습니다.')
    return redirect(url_for('products'))

@app.route('/products/check/<int:id>', methods=['GET'])
def check_product(id):
    purchases = Purchase.query.filter_by(product_id=id).count()
    sales = Sale.query.filter_by(product_id=id).count()
    can_delete = purchases == 0 and sales == 0
    return jsonify({
        'can_delete': can_delete,
        'message': '이 제품과 연결된 구매/판매 내역이 있어 삭제할 수 없습니다.' if not can_delete else ''
    })

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    purchases = Purchase.query.filter_by(product_id=id).count()
    sales = Sale.query.filter_by(product_id=id).count()
    if purchases > 0 or sales > 0:
        return jsonify({
            'success': False,
            'message': '이 제품과 연결된 구매/판매 내역이 있어 삭제할 수 없습니다.'
        }), 400
    
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('제품이 삭제되었습니다.')
    return jsonify({'success': True})

@app.route('/purchase/edit/<int:id>', methods=['POST'])
def edit_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    old_quantity = purchase.quantity
    
    purchase.product_id = request.form['product_id']
    purchase.supplier_id = request.form['supplier_id']
    purchase.quantity = int(request.form['quantity'])
    purchase.price = float(request.form['price'])
    
    # 재고 수정
    product = Product.query.get(purchase.product_id)
    product.stock = product.stock - old_quantity + purchase.quantity
    
    db.session.commit()
    flash('구매 내역이 수정되었습니다.')
    return redirect(url_for('purchase'))

@app.route('/purchase/delete/<int:id>', methods=['POST'])
def delete_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    
    # 재고 감소
    product = Product.query.get(purchase.product_id)
    product.stock -= purchase.quantity
    
    db.session.delete(purchase)
    db.session.commit()
    flash('구매 내역이 삭제되었습니다.')
    return jsonify({'success': True})

@app.route('/sale/edit/<int:id>', methods=['POST'])
def edit_sale(id):
    sale = Sale.query.get_or_404(id)
    old_quantity = sale.quantity
    
    # 새로운 수량이 재고보다 많은지 확인
    product = Product.query.get(sale.product_id)
    new_quantity = int(request.form['quantity'])
    if product.stock + old_quantity < new_quantity:
        return jsonify({
            'success': False,
            'message': '재고가 부족합니다.'
        }), 400
    
    sale.product_id = request.form['product_id']
    sale.customer_id = request.form['customer_id']
    sale.quantity = new_quantity
    sale.price = float(request.form['price'])
    
    # 재고 수정
    product.stock = product.stock + old_quantity - new_quantity
    
    db.session.commit()
    flash('판매 내역이 수정되었습니다.')
    return redirect(url_for('sale'))

@app.route('/sale/delete/<int:id>', methods=['POST'])
def delete_sale(id):
    sale = Sale.query.get_or_404(id)
    
    # 재고 증가
    product = Product.query.get(sale.product_id)
    product.stock += sale.quantity
    
    db.session.delete(sale)
    db.session.commit()
    flash('판매 내역이 삭제되었습니다.')
    return jsonify({'success': True})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=port)
